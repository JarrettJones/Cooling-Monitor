import httpx
from typing import Dict, Any, Optional
from sqlalchemy import select
from app.config import settings


async def get_redfish_credentials():
    """Get Redfish credentials from database"""
    from app.models.settings import SystemSettings
    from app.database import async_session_maker as session_maker
    
    # Check if database is initialized
    if session_maker is None:
        print("DEBUG: Database not initialized, using config defaults")
        return settings.redfish_username, settings.redfish_password
    
    async with session_maker() as db:
        result = await db.execute(select(SystemSettings).limit(1))
        system_settings = result.scalar_one_or_none()
        
        if system_settings:
            print(f"DEBUG: Loaded credentials from database - username: {system_settings.redfish_username}")
            return system_settings.redfish_username, system_settings.redfish_password
        else:
            # Return defaults from config if not in database
            print("DEBUG: No settings in database, using config defaults")
            return settings.redfish_username, settings.redfish_password


class RedfishClient:
    def __init__(self, ip_address: str, username: str = None, password: str = None):
        self.base_url = f"https://{ip_address}:8080"
        self.username = username
        self.password = password
        self.verify_ssl = settings.redfish_verify_ssl
        
    async def _make_request(self, endpoint: str, retries: int = 3) -> Optional[Dict[Any, Any]]:
        """Make an async HTTP request to the Redfish API with retry logic"""
        import asyncio
        
        for attempt in range(retries):
            try:
                url = f"{self.base_url}{endpoint}"
                if attempt == 0:
                    print(f"DEBUG: Making request to {url} with username={self.username}")
                else:
                    print(f"DEBUG: Retry {attempt}/{retries-1} for {endpoint}")
                    
                async with httpx.AsyncClient(verify=self.verify_ssl) as client:
                    response = await client.get(
                        url,
                        auth=(self.username, self.password),
                        timeout=10.0
                    )
                    print(f"DEBUG: Response status: {response.status_code}")
                    response.raise_for_status()
                    return response.json()
            except Exception as e:
                if attempt == retries - 1:
                    # Last attempt failed
                    print(f"Error making Redfish request to {endpoint} after {retries} attempts: {e}")
                    return None
                # Wait before retrying (exponential backoff)
                wait_time = 0.5 * (2 ** attempt)
                await asyncio.sleep(wait_time)
        
        return None
    
    async def test_connection(self) -> bool:
        """Test connection to Redfish API"""
        try:
            data = await self._make_request("/redfish/v1")
            return data is not None
        except:
            return False
    
    async def get_thermal_data(self) -> Optional[Dict[str, Any]]:
        """Get thermal data (temperature and fans)"""
        try:
            data = await self._make_request("/redfish/v1/Chassis/1/Thermal")
            if not data:
                return None
            
            # Parse temperatures
            temperatures = data.get("Temperatures", [])
            avg_temp = 0
            if temperatures:
                temps = [t.get("ReadingCelsius", 0) for t in temperatures if t.get("ReadingCelsius")]
                avg_temp = sum(temps) / len(temps) if temps else 0
            
            # Parse fans
            fans = data.get("Fans", [])
            avg_fan_speed = 0
            if fans:
                speeds = [f.get("Reading", 0) for f in fans if f.get("Reading")]
                avg_fan_speed = sum(speeds) / len(speeds) if speeds else 0
            
            return {
                "temperature": round(avg_temp, 1),
                "fan_speed": int(avg_fan_speed),
                "raw_data": data
            }
        except Exception as e:
            print(f"Error getting thermal data: {e}")
            return None
    
    async def get_power_data(self) -> float:
        """Get power consumption data"""
        try:
            data = await self._make_request("/redfish/v1/Chassis/1/Power")
            if not data:
                return 0.0
            
            power_control = data.get("PowerControl", [])
            if power_control:
                return round(power_control[0].get("PowerConsumedWatts", 0.0), 1)
            return 0.0
        except Exception as e:
            print(f"Error getting power data: {e}")
            return 0.0
    
    async def get_all_sensor_data(self) -> Optional[Dict[str, Any]]:
        """Get all sensor data"""
        try:
            thermal_data = await self.get_thermal_data()
            if not thermal_data:
                return None
            
            power = await self.get_power_data()
            
            return {
                "temperature": thermal_data.get("temperature", 0),
                "fan_speed": thermal_data.get("fan_speed", 0),
                "power_consumption": power,
                "raw_data": thermal_data.get("raw_data")
            }
        except Exception as e:
            print(f"Error getting all sensor data: {e}")
            return None
    
    async def get_manager_info(self) -> Optional[Dict[str, Any]]:
        """Get R-SCM manager information"""
        try:
            data = await self._make_request("/redfish/v1/Managers/RackManager")
            if not data:
                return None
            
            # Extract required fields
            manager_info = {
                "manager_type": data.get("ManagerType"),
                "model": data.get("Model"),
                "firmware_version": data.get("FirmwareVersion"),
                "status_state": data.get("Status", {}).get("State"),
                "status_health": data.get("Status", {}).get("Health"),
                "hostname": data.get("Oem", {}).get("Microsoft", {}).get("HostName"),
                "unique_id": data.get("Oem", {}).get("Microsoft", {}).get("UniqueId"),
                "time_since_boot": data.get("Oem", {}).get("Microsoft", {}).get("TimeSinceLastBoot")
            }
            
            return manager_info
        except Exception as e:
            print(f"Error getting manager info: {e}")
            return None
    
    async def get_cdu_status(self) -> Optional[Dict[str, Any]]:
        """Get CDU Controller status"""
        try:
            data = await self._make_request("/redfish/v1/Chassis/CDU")
            if not data:
                return None
            
            # Extract relevant information (exclude FRU and @Message.ExtendedInfo)
            cdu_info = {
                "chassis_status": {
                    "state": data.get("Status", {}).get("State"),
                    "health": data.get("Status", {}).get("Health")
                },
                "controller_status": data.get("Oem", {}).get("Microsoft", {}).get("ControllerStatus", [{}])[0] if data.get("Oem", {}).get("Microsoft", {}).get("ControllerStatus") else {},
                "fan_alarms": data.get("Oem", {}).get("Microsoft", {}).get("FanAlarms"),
                "pump_alarms": data.get("Oem", {}).get("Microsoft", {}).get("PumpAlarms"),
                "sensor_alarms": data.get("Oem", {}).get("Microsoft", {}).get("SensorAlarms"),
                "leak_alarms": data.get("Oem", {}).get("Microsoft", {}).get("LeakAlarms")
            }
            
            return cdu_info
        except Exception as e:
            print(f"Error getting CDU status: {e}")
            return None
    
    async def get_fan_status(self) -> Optional[list]:
        """Get individual fan status information"""
        try:
            data = await self._make_request("/redfish/v1/Chassis/CDU/ThermalSubsystem/Fans")
            if not data:
                return None
            
            fans = data.get("Members", [])
            
            # Create tasks for all fan requests to run concurrently
            async def fetch_fan_data(fan_ref):
                fan_id = fan_ref.get("@odata.id", "").split("/")[-1]
                fan_data = await self._make_request(fan_ref.get("@odata.id", ""))
                if fan_data:
                    return {
                        "id": fan_id,
                        "name": fan_data.get("Name", fan_id),
                        "state": fan_data.get("Status", {}).get("State"),
                        "health": fan_data.get("Status", {}).get("Health"),
                        "speed_percent": fan_data.get("SpeedPercent", {}).get("Reading")
                    }
                return None
            
            # Fetch all fans concurrently
            import asyncio
            fan_tasks = [fetch_fan_data(fan_ref) for fan_ref in fans]
            fan_details = await asyncio.gather(*fan_tasks, return_exceptions=True)
            
            # Filter out None values and exceptions
            fan_details = [fan for fan in fan_details if fan and not isinstance(fan, Exception)]
            
            return fan_details
        except Exception as e:
            print(f"Error getting fan status: {e}")
            return None
    
    async def get_pump_status(self) -> Optional[list]:
        """Get individual pump status information"""
        try:
            data = await self._make_request("/redfish/v1/ThermalEquipment/CDUs/1/Pumps")
            if not data:
                return None
            
            pumps = data.get("Members", [])
            
            # Create tasks for all pump requests to run concurrently
            async def fetch_pump_data(pump_ref):
                pump_id = pump_ref.get("@odata.id", "").split("/")[-1]
                # Get device status from Oem/Microsoft/DeviceStatus endpoint
                device_status_url = f"{pump_ref.get('@odata.id', '')}/Oem/Microsoft/DeviceStatus"
                pump_data = await self._make_request(device_status_url)
                if pump_data:
                    return {
                        "id": pump_id,
                        "name": f"Pump {pump_id}",
                        "status": pump_data.get("PumpStatus"),
                        "speed": pump_data.get("Speed"),
                        "requested_speed": pump_data.get("RequestedPumpSpeed"),
                        "flow_liquid": pump_data.get("FlowLiquid"),
                        "pressure_supply": pump_data.get("PressureLiquidSupply"),
                        "pressure_return": pump_data.get("PressureLiquidReturn"),
                        "pressure_diff": pump_data.get("PressureDiffLiquidSupplyReturn"),
                        "error_code": pump_data.get("ErrorCode"),
                        "liquid_ph": pump_data.get("LiquidPHValue")
                    }
                return None
            
            # Fetch all pumps concurrently
            import asyncio
            pump_tasks = [fetch_pump_data(pump_ref) for pump_ref in pumps]
            pump_details = await asyncio.gather(*pump_tasks, return_exceptions=True)
            
            # Filter out None values and exceptions
            pump_details = [pump for pump in pump_details if pump and not isinstance(pump, Exception)]
            
            return pump_details
        except Exception as e:
            print(f"Error getting pump status: {e}")
            return None
