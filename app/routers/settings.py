from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import json

from app.database import get_session
from app.models.settings import (
    SystemSettings, 
    RedfishCredentialsUpdate, 
    RedfishCredentialsResponse,
    SMTPSettingsUpdate,
    SMTPSettingsResponse
)
from app.routers.auth import require_admin
from app.models.user import User
from app.utils.encryption import encrypt_value, decrypt_value

router = APIRouter(prefix="/api/settings", tags=["settings"])


async def get_or_create_settings(db: AsyncSession) -> SystemSettings:
    """Get settings or create default if not exists"""
    result = await db.execute(select(SystemSettings).limit(1))
    settings = result.scalar_one_or_none()
    
    if not settings:
        settings = SystemSettings(
            redfish_username="admin",
            redfish_password="admin"
        )
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
    
    return settings


@router.get("/redfish-credentials", response_model=RedfishCredentialsResponse)
async def get_redfish_credentials(db: AsyncSession = Depends(get_session)):
    """Get current Redfish credentials (username only, not password)"""
    settings = await get_or_create_settings(db)
    return RedfishCredentialsResponse(
        username=settings.redfish_username,
        updated_at=settings.updated_at
    )


@router.put("/redfish-credentials")
async def update_redfish_credentials(
    credentials: RedfishCredentialsUpdate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin)
):
    """Update Redfish API credentials (admin only)"""
    print(f"DEBUG: Updating Redfish credentials - username: {credentials.username}, password: {'*' * len(credentials.password)}")
    settings = await get_or_create_settings(db)
    
    settings.redfish_username = credentials.username
    settings.redfish_password = credentials.password
    
    await db.commit()
    
    print(f"DEBUG: Credentials saved - username: {settings.redfish_username}, password: {'*' * len(settings.redfish_password)}")
    
    return {
        "message": "Redfish credentials updated successfully",
        "username": settings.redfish_username
    }


@router.get("/smtp", response_model=SMTPSettingsResponse)
async def get_smtp_settings(db: AsyncSession = Depends(get_session)):
    """Get current SMTP and Teams notification settings (without password)"""
    settings = await get_or_create_settings(db)
    
    # Parse email list from JSON string
    try:
        to_emails = json.loads(settings.smtp_to_emails) if settings.smtp_to_emails else []
    except:
        to_emails = []
    
    return SMTPSettingsResponse(
        smtp_enabled=settings.smtp_enabled or False,
        smtp_server=settings.smtp_server or "smtp.office365.com",
        smtp_port=settings.smtp_port or 587,
        smtp_username=settings.smtp_username or "",
        smtp_from_email=settings.smtp_from_email or "",
        smtp_to_emails=to_emails,
        smtp_use_tls=settings.smtp_use_tls if settings.smtp_use_tls is not None else True,
        teams_enabled=settings.teams_enabled or False,
        teams_webhook_url=settings.teams_webhook_url or "",
        pump_flow_critical_threshold=settings.pump_flow_critical_threshold or 10.0,
        updated_at=settings.updated_at
    )


@router.put("/smtp")
async def update_smtp_settings(
    smtp_settings: SMTPSettingsUpdate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin)
):
    """Update SMTP email and Teams notification settings (admin only)"""
    settings = await get_or_create_settings(db)
    
    # Update SMTP settings
    settings.smtp_enabled = smtp_settings.smtp_enabled
    settings.smtp_server = smtp_settings.smtp_server
    settings.smtp_port = smtp_settings.smtp_port
    settings.smtp_username = smtp_settings.smtp_username
    settings.smtp_from_email = smtp_settings.smtp_from_email
    settings.smtp_to_emails = json.dumps(smtp_settings.smtp_to_emails)
    settings.smtp_use_tls = smtp_settings.smtp_use_tls
    settings.pump_flow_critical_threshold = smtp_settings.pump_flow_critical_threshold
    
    # Update Teams settings
    settings.teams_enabled = smtp_settings.teams_enabled
    settings.teams_webhook_url = smtp_settings.teams_webhook_url
    
    # Encrypt password before storing
    if smtp_settings.smtp_password:
        settings.smtp_password = encrypt_value(smtp_settings.smtp_password)
    
    await db.commit()
    
    return {
        "message": "Notification settings updated successfully",
        "smtp_enabled": settings.smtp_enabled,
        "teams_enabled": settings.teams_enabled
    }


@router.get("/monitoring")
async def get_monitoring_setting(db: AsyncSession = Depends(get_session)):
    """Get monitoring enabled status and polling interval"""
    settings = await get_or_create_settings(db)
    return {
        "monitoring_enabled": settings.monitoring_enabled,
        "polling_interval_seconds": settings.polling_interval_seconds or 30
    }


@router.put("/monitoring")
async def update_monitoring_setting(
    data: dict,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin)
):
    """Update monitoring enabled status and polling interval (admin only)"""
    settings = await get_or_create_settings(db)
    
    settings.monitoring_enabled = data.get("monitoring_enabled", True)
    
    # Update polling interval if provided
    if "polling_interval_seconds" in data:
        polling_interval = data["polling_interval_seconds"]
        settings.polling_interval_seconds = polling_interval
        
        # Reschedule polling job with new interval
        from app.main import reschedule_polling_job
        reschedule_polling_job(polling_interval)
    
    settings.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(settings)
    
    status = "enabled" if settings.monitoring_enabled else "disabled"
    print(f"📊 Monitoring {status} by {current_user.username}")
    
    return {
        "message": f"Monitoring settings updated successfully",
        "monitoring_enabled": settings.monitoring_enabled,
        "polling_interval_seconds": settings.polling_interval_seconds
    }
