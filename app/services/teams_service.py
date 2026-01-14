"""Microsoft Teams notification service"""
import httpx
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.settings import SystemSettings


class TeamsService:
    @staticmethod
    async def send_urgent_alarm_teams(
        db: AsyncSession,
        heat_exchanger_name: str,
        pump_id: str,
        flow_rate: float
    ):
        """Send urgent alarm notification to Microsoft Teams"""
        # Get Teams settings from database
        result = await db.execute(select(SystemSettings).limit(1))
        settings = result.scalar_one_or_none()
        
        if not settings or not settings.teams_enabled or not settings.teams_webhook_url:
            print(f"⚠️ URGENT ALARM: {heat_exchanger_name} - Pump {pump_id} flow rate critically low: {flow_rate} L/min (Teams disabled)")
            return
        
        try:
            threshold = settings.pump_flow_critical_threshold or 10.0
            
            # Create adaptive card message for Teams
            card = {
                "@type": "MessageCard",
                "@context": "https://schema.org/extensions",
                "themeColor": "FF0000",  # Red
                "summary": f"🚨 URGENT: Low Flow Rate Alert - {heat_exchanger_name}",
                "sections": [
                    {
                        "activityTitle": "🚨 URGENT ALARM - IMMEDIATE ATTENTION REQUIRED",
                        "activitySubtitle": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
                        "activityImage": "https://raw.githubusercontent.com/microsoft/fluentui-emoji/main/assets/Warning/3D/warning_3d.png",
                        "facts": [
                            {
                                "name": "Heat Exchanger:",
                                "value": heat_exchanger_name
                            },
                            {
                                "name": "Pump ID:",
                                "value": pump_id
                            },
                            {
                                "name": "Current Flow Rate:",
                                "value": f"⚠️ {flow_rate} L/min"
                            },
                            {
                                "name": "Critical Threshold:",
                                "value": f"{threshold} L/min"
                            },
                            {
                                "name": "Status:",
                                "value": "🔴 **CRITICALLY LOW**"
                            }
                        ],
                        "markdown": True
                    },
                    {
                        "text": "**Action Required:** Please investigate immediately to prevent equipment damage."
                    }
                ]
            }
            
            # Send to Teams webhook
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    settings.teams_webhook_url,
                    json=card
                )
                response.raise_for_status()
            
            print(f"✅ Urgent alarm Teams message sent for {heat_exchanger_name} - Pump {pump_id}")
            
        except Exception as e:
            print(f"❌ Failed to send Teams notification: {e}")


teams_service = TeamsService()
