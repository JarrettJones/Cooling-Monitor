import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json

from app.models.settings import SystemSettings
from app.utils.encryption import decrypt_value


class EmailService:
    @staticmethod
    async def send_urgent_alarm_email(
        db: AsyncSession,
        heat_exchanger_name: str, 
        pump_id: str, 
        flow_rate: float
    ):
        """Send urgent alarm email for low pump flow rate"""
        # Get SMTP settings from database
        result = await db.execute(select(SystemSettings).limit(1))
        settings = result.scalars().first()
        
        if not settings or not settings.smtp_enabled:
            print(f"⚠️ URGENT ALARM: {heat_exchanger_name} - Pump {pump_id} flow rate critically low: {flow_rate} L/min (Email disabled)")
            return
        
        # Parse recipient emails
        try:
            to_emails = json.loads(settings.smtp_to_emails) if settings.smtp_to_emails else []
        except:
            to_emails = []
        
        if not to_emails:
            print(f"⚠️ URGENT ALARM: {heat_exchanger_name} - Pump {pump_id} flow rate critically low: {flow_rate} L/min (No recipients configured)")
            return
        
        try:
            # Decrypt password
            smtp_password = decrypt_value(settings.smtp_password) if settings.smtp_password else ""
            
            # Create message
            message = MIMEMultipart()
            message["From"] = settings.smtp_from_email
            message["To"] = ", ".join(to_emails)
            message["Subject"] = f"🚨 URGENT: Low Flow Rate Alert - {heat_exchanger_name}"
            
            # Email body
            threshold = settings.pump_flow_critical_threshold or 10.0
            body = f"""
URGENT ALARM - IMMEDIATE ATTENTION REQUIRED

Heat Exchanger: {heat_exchanger_name}
Pump ID: {pump_id}
Current Flow Rate: {flow_rate} L/min
Critical Threshold: {threshold} L/min

Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

This is an automated alert from the Cooling Monitor system.
Please investigate immediately to prevent equipment damage.
"""
            
            message.attach(MIMEText(body, "plain"))
            
            # Send email
            with smtplib.SMTP(settings.smtp_server, settings.smtp_port) as server:
                if settings.smtp_use_tls:
                    server.starttls()
                if smtp_password:
                    server.login(settings.smtp_username, smtp_password)
                server.send_message(message)
            
            print(f"✅ Urgent alarm email sent for {heat_exchanger_name} - Pump {pump_id}")
        except Exception as e:
            print(f"❌ Failed to send urgent alarm email: {e}")


email_service = EmailService()
