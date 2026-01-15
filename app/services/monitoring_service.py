from datetime import datetime
from typing import List
from sqlalchemy import select
import json

from app.database import async_session_maker
from app.services.redfish_client import RedfishClient, get_redfish_credentials
from app.models.heat_exchanger import HeatExchanger
from app.models.monitoring_data import MonitoringData
from app.models.settings import SystemSettings
from app.models.alert import Alert
from app.services.websocket_manager import manager
from app.services.email_service import email_service
from app.services.teams_service import teams_service


class MonitoringService:
    def __init__(self):
        pass
    
    async def poll_heat_exchanger(self, heat_exchanger_id: int, rscm_ip: str):
        """Poll a single heat exchanger and save data"""
        try:
            # Check if monitoring is enabled
            from app.database import async_session_maker as session_maker
            async with session_maker() as db:
                result = await db.execute(select(SystemSettings))
                settings = result.scalar_one_or_none()
                
                if not settings or not settings.monitoring_enabled:
                    return  # Skip polling if monitoring is disabled
            
            # Get credentials and create Redfish client
            username, password = await get_redfish_credentials()
            print(f"DEBUG: Using credentials - username: {username}, password: {'*' * len(password) if password else 'None'}")
            
            client = RedfishClient(rscm_ip, username, password)
            print(f"DEBUG: Connecting to {client.base_url}/redfish/v1/Managers/RackManager")
            
            # Get manager information only
            manager_info = await client.get_manager_info()
            
            # Get CDU controller status
            cdu_status = await client.get_cdu_status()
            
            # Get fan status
            fan_status = await client.get_fan_status()
            
            # Get pump status
            pump_status = await client.get_pump_status()
            
            if not manager_info:
                print(f"⚠ No manager info retrieved for heat exchanger {heat_exchanger_id}")
                return
            
            # Update heat exchanger with manager info
            from app.database import async_session_maker as session_maker
            async with session_maker() as db:
                # Get system settings for alarm threshold
                settings_result = await db.execute(select(SystemSettings).limit(1))
                system_settings = settings_result.scalars().first()
                pump_threshold = system_settings.pump_flow_critical_threshold if system_settings else 10.0
                
                result = await db.execute(
                    select(HeatExchanger).where(HeatExchanger.id == heat_exchanger_id)
                )
                heat_exchanger = result.scalar_one_or_none()
                if heat_exchanger:
                    heat_exchanger.manager_type = manager_info.get("manager_type")
                    heat_exchanger.model = manager_info.get("model")
                    heat_exchanger.firmware_version = manager_info.get("firmware_version")
                    heat_exchanger.status_state = manager_info.get("status_state")
                    heat_exchanger.status_health = manager_info.get("status_health")
                    heat_exchanger.hostname = manager_info.get("hostname")
                    heat_exchanger.unique_id = manager_info.get("unique_id")
                    heat_exchanger.time_since_boot = manager_info.get("time_since_boot")
                    
                    # Update CDU status if available
                    if cdu_status:
                        heat_exchanger.cdu_chassis_status = json.dumps(cdu_status.get("chassis_status", {}))
                        heat_exchanger.cdu_controller_status = json.dumps(cdu_status.get("controller_status", {}))
                        heat_exchanger.cdu_alarms = json.dumps({
                            "fan_alarms": cdu_status.get("fan_alarms"),
                            "pump_alarms": cdu_status.get("pump_alarms"),
                            "sensor_alarms": cdu_status.get("sensor_alarms"),
                            "leak_alarms": cdu_status.get("leak_alarms")
                        })
                        
                        # Process all alarm types and create Alert records
                        await self._process_alarms(db, heat_exchanger_id, heat_exchanger, cdu_status)
                        
                        # Extract ambient readings from CDU controller status
                        controller_status = cdu_status.get("controller_status", {})
                        ambient_temp = controller_status.get("AmbientTemperature")
                        ambient_humidity = controller_status.get("AmbientHumidity")
                        
                        # Combine all data for historical storage
                        combined_data = {
                            "cdu_status": cdu_status,
                            "fan_status": fan_status,
                            "pump_status": pump_status
                        }
                        
                        # Create monitoring data record with ambient values
                        monitoring_data = MonitoringData(
                            heat_exchanger_id=heat_exchanger_id,
                            timestamp=datetime.utcnow(),
                            temperature=ambient_temp if ambient_temp is not None else 0.0,
                            fan_speed=0,  # Not available from current endpoints
                            power_consumption=0.0,  # Not tracked per user request
                            humidity=ambient_humidity if ambient_humidity is not None else None,
                            status=heat_exchanger.status_state or "normal",
                            ambient_temperature=ambient_temp,
                            ambient_humidity=ambient_humidity,
                            raw_data=json.dumps(combined_data)
                        )
                        db.add(monitoring_data)
                    
                    # Update fan status if available
                    if fan_status:
                        heat_exchanger.fan_status = json.dumps(fan_status)
                    
                    # Update pump status if available
                    if pump_status:
                        heat_exchanger.pump_status = json.dumps(pump_status)
                        
                        # Check for critical low flow rates
                        urgent_alarms = []
                        for pump in pump_status:
                            flow_rate = pump.get("flow_liquid")
                            if flow_rate is not None and flow_rate < pump_threshold:
                                alarm_data = {
                                    "type": "CRITICAL_LOW_FLOW",
                                    "pump_id": pump.get("id"),
                                    "pump_name": pump.get("name"),
                                    "flow_rate": flow_rate,
                                    "threshold": pump_threshold,
                                    "timestamp": datetime.utcnow().isoformat()
                                }
                                urgent_alarms.append(alarm_data)
                                
                                # Create Alert record in database
                                try:
                                    alert = Alert(
                                        heat_exchanger_id=heat_exchanger_id,
                                        type="CRITICAL_LOW_FLOW",
                                        severity="critical",
                                        title=f"Critical Low Flow - {pump.get('name', pump.get('id'))}",
                                        description=f"Pump flow rate ({flow_rate} L/min) dropped below critical threshold ({pump_threshold} L/min)",
                                        pump_id=pump.get("id"),
                                        pump_name=pump.get("name"),
                                        flow_rate=flow_rate,
                                        threshold=pump_threshold,
                                        acknowledged=False,
                                        resolved=False
                                    )
                                    db.add(alert)
                                    await db.flush()  # Get alert ID
                                    alert_id = alert.id
                                    print(f"✓ Created Alert ID {alert_id} for {pump.get('name')}")
                                except Exception as e:
                                    print(f"❌ Failed to create alert: {e}")
                                    alert_id = None
                                
                                # Send email alert (pass db session) - don't let this fail the alert creation
                                try:
                                    await email_service.send_urgent_alarm_email(
                                        db,
                                        heat_exchanger.name,
                                        pump.get("name", pump.get("id")),
                                        flow_rate
                                    )
                                except Exception as e:
                                    print(f"❌ Failed to send email alert: {e}")
                                
                                # Send Teams notification (pass db session) - don't let this fail the alert creation
                                try:
                                    await teams_service.send_urgent_alarm_teams(
                                        db,
                                        heat_exchanger.name,
                                        pump.get("name", pump.get("id")),
                                        flow_rate
                                    )
                                except Exception as e:
                                    print(f"❌ Failed to send Teams alert: {e}")
                                
                                # Broadcast via WebSocket
                                if alert_id:
                                    await manager.broadcast(json.dumps({
                                        "type": "new_alert",
                                        "alert_id": alert_id,
                                        "heat_exchanger_id": heat_exchanger_id,
                                        "heat_exchanger_name": heat_exchanger.name,
                                        "severity": "critical",
                                        "title": f"Critical Low Flow - {pump.get('name', pump.get('id'))}",
                                        "pump_name": pump.get("name"),
                                        "flow_rate": flow_rate,
                                        "threshold": pump_threshold
                                    }))
                                
                                print(f"🚨 URGENT ALARM: {heat_exchanger.name} - {pump.get('name')} flow rate critically low: {flow_rate} L/min")
                        
                        # Store urgent alarms in heat_exchanger for backwards compatibility
                        if urgent_alarms:
                            heat_exchanger.urgent_alarms = json.dumps(urgent_alarms)
                        else:
                            heat_exchanger.urgent_alarms = None
                    
                    await db.commit()
            
            print(f"✓ Polled heat exchanger {heat_exchanger_id}: Manager info updated")
            
        except Exception as e:
            print(f"Error polling heat exchanger {heat_exchanger_id}: {e}")
    
    async def _process_alarms(self, db, heat_exchanger_id: int, heat_exchanger, cdu_status: dict):
        """Process all alarm types and create Alert records"""
        
        # Check for leak alarms
        leak_alarms = cdu_status.get("leak_alarms", {})
        if leak_alarms and leak_alarms.get("Alarms"):
            for alarm in leak_alarms.get("Alarms", []):
                # Check if alert already exists for this alarm
                existing = await db.execute(
                    select(Alert).where(
                        Alert.heat_exchanger_id == heat_exchanger_id,
                        Alert.type == "LEAK_ALARM",
                        Alert.description.contains(alarm),
                        Alert.resolved == False
                    )
                )
                if not existing.scalar_one_or_none():
                    try:
                        alert = Alert(
                            heat_exchanger_id=heat_exchanger_id,
                            type="LEAK_ALARM",
                            severity="warning",
                            title=f"Leak Detection - {alarm}",
                            description=f"Leak sensor alarm detected: {alarm}",
                            acknowledged=False,
                            resolved=False
                        )
                        db.add(alert)
                        await db.flush()
                        print(f"⚠️ Created leak alarm alert: {alarm}")
                    except Exception as e:
                        print(f"❌ Failed to create leak alarm alert: {e}")
        
        # Check for fan alarms
        fan_alarms = cdu_status.get("fan_alarms", {})
        if fan_alarms and fan_alarms.get("Alarms"):
            alarm_dict = fan_alarms.get("Alarms", {})
            for alarm_name, alarm_active in alarm_dict.items():
                if alarm_active:  # Only create alert if alarm is active
                    existing = await db.execute(
                        select(Alert).where(
                            Alert.heat_exchanger_id == heat_exchanger_id,
                            Alert.type == "FAN_ALARM",
                            Alert.description.contains(alarm_name),
                            Alert.resolved == False
                        )
                    )
                    if not existing.scalar_one_or_none():
                        try:
                            alert = Alert(
                                heat_exchanger_id=heat_exchanger_id,
                                type="FAN_ALARM",
                                severity="warning",
                                title=f"Fan Alarm - {alarm_name}",
                                description=f"Fan system alarm detected: {alarm_name}",
                                acknowledged=False,
                                resolved=False
                            )
                            db.add(alert)
                            await db.flush()
                            print(f"⚠️ Created fan alarm alert: {alarm_name}")
                        except Exception as e:
                            print(f"❌ Failed to create fan alarm alert: {e}")
        
        # Check for pump alarms
        pump_alarms = cdu_status.get("pump_alarms", {})
        if pump_alarms and pump_alarms.get("Alarms"):
            alarm_dict = pump_alarms.get("Alarms", {})
            for alarm_name, alarm_active in alarm_dict.items():
                if alarm_active:
                    existing = await db.execute(
                        select(Alert).where(
                            Alert.heat_exchanger_id == heat_exchanger_id,
                            Alert.type == "PUMP_ALARM",
                            Alert.description.contains(alarm_name),
                            Alert.resolved == False
                        )
                    )
                    if not existing.scalar_one_or_none():
                        try:
                            alert = Alert(
                                heat_exchanger_id=heat_exchanger_id,
                                type="PUMP_ALARM",
                                severity="warning",
                                title=f"Pump Alarm - {alarm_name}",
                                description=f"Pump system alarm detected: {alarm_name}",
                                acknowledged=False,
                                resolved=False
                            )
                            db.add(alert)
                            await db.flush()
                            print(f"⚠️ Created pump alarm alert: {alarm_name}")
                        except Exception as e:
                            print(f"❌ Failed to create pump alarm alert: {e}")
        
        # Check for sensor alarms
        sensor_alarms = cdu_status.get("sensor_alarms", {})
        if sensor_alarms and sensor_alarms.get("Alarms"):
            alarms_list = sensor_alarms.get("Alarms", [])
            for alarm in alarms_list:
                existing = await db.execute(
                    select(Alert).where(
                        Alert.heat_exchanger_id == heat_exchanger_id,
                        Alert.type == "SENSOR_ALARM",
                        Alert.description.contains(alarm),
                        Alert.resolved == False
                    )
                )
                if not existing.scalar_one_or_none():
                    try:
                        alert = Alert(
                            heat_exchanger_id=heat_exchanger_id,
                            type="SENSOR_ALARM",
                            severity="warning",
                            title=f"Sensor Alarm - {alarm}",
                            description=f"Sensor alarm detected: {alarm}",
                            acknowledged=False,
                            resolved=False
                        )
                        db.add(alert)
                        await db.flush()
                        print(f"⚠️ Created sensor alarm alert: {alarm}")
                    except Exception as e:
                        print(f"❌ Failed to create sensor alarm alert: {e}")
    
    async def poll_all_heat_exchangers(self):
        """Poll all active heat exchangers"""
        try:
            # Check if async_session_maker is initialized
            from app.database import async_session_maker as session_maker
            if session_maker is None:
                print("Database not initialized yet, skipping poll")
                return
                
            async with session_maker() as db:
                result = await db.execute(
                    select(HeatExchanger).where(HeatExchanger.is_active == True)
                )
                heat_exchangers = result.scalars().all()
                
                for he in heat_exchangers:
                    await self.poll_heat_exchanger(he.id, he.rscm_ip)
        except Exception as e:
            print(f"Error polling all heat exchangers: {e}")


# Global monitoring service instance
monitoring_service = MonitoringService()

