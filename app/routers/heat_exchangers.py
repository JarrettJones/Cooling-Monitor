from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from typing import List
from datetime import datetime
import asyncio

from app.database import get_session
from app.models.heat_exchanger import (
    HeatExchanger,
    HeatExchangerCreate,
    HeatExchangerUpdate,
    HeatExchangerResponse
)
from app.models.user import User
from app.routers.auth import require_admin, get_current_user
from app.services.redfish_client import RedfishClient, get_redfish_credentials
from app.services.monitoring_service import MonitoringService

router = APIRouter(prefix="/api/heat-exchangers", tags=["heat-exchangers"])


@router.get("/", response_model=List[HeatExchangerResponse])
async def get_all_heat_exchangers(db: AsyncSession = Depends(get_session)):
    """Get all heat exchangers"""
    result = await db.execute(
        select(HeatExchanger).order_by(HeatExchanger.created_at.desc())
    )
    heat_exchangers = result.scalars().all()
    return [HeatExchangerResponse.from_orm_model(he) for he in heat_exchangers]


@router.get("/{heat_exchanger_id}", response_model=HeatExchangerResponse)
async def get_heat_exchanger(heat_exchanger_id: int, db: AsyncSession = Depends(get_session)):
    """Get heat exchanger by ID"""
    result = await db.execute(
        select(HeatExchanger).where(HeatExchanger.id == heat_exchanger_id)
    )
    heat_exchanger = result.scalar_one_or_none()
    
    if not heat_exchanger:
        raise HTTPException(status_code=404, detail="Heat exchanger not found")
    
    return HeatExchangerResponse.from_orm_model(heat_exchanger)


@router.post("/", response_model=HeatExchangerResponse, status_code=status.HTTP_201_CREATED)
async def create_heat_exchanger(
    heat_exchanger: HeatExchangerCreate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Create a new heat exchanger"""
    # Test Redfish connection
    username, password = await get_redfish_credentials()
    client = RedfishClient(heat_exchanger.rscm_ip, username, password)
    is_connected = await client.test_connection()
    
    if not is_connected:
        raise HTTPException(
            status_code=400,
            detail="Failed to connect to R-SCM device"
        )
    
    # Verify manager type is H7021_RPU
    manager_info = await client.get_manager_info()
    if not manager_info:
        raise HTTPException(
            status_code=400,
            detail="Failed to retrieve manager information from R-SCM device"
        )
    
    manager_type = manager_info.get("manager_type")
    if manager_type != "H7021_RPU":
        raise HTTPException(
            status_code=400,
            detail=f"Invalid device type. The IP address provided does not report as a RPU (Manager Type: {manager_type or 'Unknown'})"
        )
    
    # Create heat exchanger
    db_heat_exchanger = HeatExchanger(
        name=heat_exchanger.name,
        type=heat_exchanger.type,
        rscm_ip=heat_exchanger.rscm_ip,
        city=heat_exchanger.location.city,
        building=heat_exchanger.location.building,
        room=heat_exchanger.location.room,
        tile=heat_exchanger.location.tile,
        is_active=heat_exchanger.is_active
    )
    
    # Force SQLAlchemy to detect the type field change
    from sqlalchemy.orm import attributes
    attributes.flag_modified(db_heat_exchanger, "type")
    
    try:
        db.add(db_heat_exchanger)
        await db.commit()
        await db.refresh(db_heat_exchanger)
        
        # Trigger immediate background polling for this heat exchanger
        asyncio.create_task(
            MonitoringService().poll_heat_exchanger(db_heat_exchanger.id, db_heat_exchanger.rscm_ip)
        )
        print(f"✓ Heat exchanger {db_heat_exchanger.id} created. Initial polling started in background.")
        
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Heat exchanger with this name or IP already exists"
        )
    
    return HeatExchangerResponse.from_orm_model(db_heat_exchanger)


@router.put("/{heat_exchanger_id}", response_model=HeatExchangerResponse)
async def update_heat_exchanger(
    heat_exchanger_id: int,
    update: HeatExchangerUpdate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin)
):
    """Update a heat exchanger (admin only)"""
    result = await db.execute(
        select(HeatExchanger).where(HeatExchanger.id == heat_exchanger_id)
    )
    db_heat_exchanger = result.scalar_one_or_none()
    
    if not db_heat_exchanger:
        raise HTTPException(status_code=404, detail="Heat exchanger not found")
    
    # Test new IP if provided
    if update.rscm_ip and update.rscm_ip != db_heat_exchanger.rscm_ip:
        username, password = await get_redfish_credentials()
        client = RedfishClient(update.rscm_ip, username, password)
        is_connected = await client.test_connection()
        if not is_connected:
            raise HTTPException(
                status_code=400,
                detail="Failed to connect to R-SCM device"
            )
    
    # Update fields
    if update.name is not None:
        db_heat_exchanger.name = update.name
    if update.type is not None:
        db_heat_exchanger.type = update.type
    if update.rscm_ip is not None:
        db_heat_exchanger.rscm_ip = update.rscm_ip
    if update.location is not None:
        db_heat_exchanger.city = update.location.city
        db_heat_exchanger.building = update.location.building
        db_heat_exchanger.room = update.location.room
        db_heat_exchanger.tile = update.location.tile
    if update.is_active is not None:
        db_heat_exchanger.is_active = update.is_active
    
    db_heat_exchanger.updated_at = datetime.utcnow()
    
    # Force SQLAlchemy to detect the change
    from sqlalchemy.orm import attributes
    attributes.flag_modified(db_heat_exchanger, "type")
    
    try:
        await db.commit()
        await db.refresh(db_heat_exchanger)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Heat exchanger with this name or IP already exists"
        )
    
    return HeatExchangerResponse.from_orm_model(db_heat_exchanger)


@router.delete("/{heat_exchanger_id}")
async def delete_heat_exchanger(
    heat_exchanger_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin)
):
    """Delete a heat exchanger (admin only)"""
    result = await db.execute(
        select(HeatExchanger).where(HeatExchanger.id == heat_exchanger_id)
    )
    db_heat_exchanger = result.scalar_one_or_none()
    
    if not db_heat_exchanger:
        raise HTTPException(status_code=404, detail="Heat exchanger not found")
    
    await db.delete(db_heat_exchanger)
    await db.commit()
    
    return {"message": "Heat exchanger deleted successfully"}
