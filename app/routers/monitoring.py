from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
from datetime import datetime, timedelta

from app.database import get_session
from app.models.monitoring_data import MonitoringData, MonitoringDataResponse, MonitoringStats

router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])


@router.get("/latest", response_model=List[MonitoringDataResponse])
async def get_latest_monitoring_data(db: AsyncSession = Depends(get_session)):
    """Get latest monitoring data for all heat exchangers"""
    # Subquery to get latest timestamp for each heat exchanger
    subquery = (
        select(
            MonitoringData.heat_exchanger_id,
            func.max(MonitoringData.timestamp).label("max_timestamp")
        )
        .group_by(MonitoringData.heat_exchanger_id)
        .subquery()
    )
    
    # Join to get full records
    query = (
        select(MonitoringData)
        .join(
            subquery,
            (MonitoringData.heat_exchanger_id == subquery.c.heat_exchanger_id) &
            (MonitoringData.timestamp == subquery.c.max_timestamp)
        )
    )
    
    result = await db.execute(query)
    data = result.scalars().all()
    
    return data


@router.get("/{heat_exchanger_id}", response_model=List[MonitoringDataResponse])
async def get_monitoring_data(
    heat_exchanger_id: int,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = Query(default=100, le=1000),
    db: AsyncSession = Depends(get_session)
):
    """Get monitoring data for a specific heat exchanger"""
    query = select(MonitoringData).where(
        MonitoringData.heat_exchanger_id == heat_exchanger_id
    )
    
    # Add date range if provided
    if start_date:
        query = query.where(MonitoringData.timestamp >= datetime.fromisoformat(start_date.replace('Z', '+00:00')))
    if end_date:
        query = query.where(MonitoringData.timestamp <= datetime.fromisoformat(end_date.replace('Z', '+00:00')))
    
    query = query.order_by(MonitoringData.timestamp.desc()).limit(limit)
    
    result = await db.execute(query)
    data = result.scalars().all()
    
    return data


@router.get("/{heat_exchanger_id}/statistics", response_model=MonitoringStats)
async def get_statistics(
    heat_exchanger_id: int,
    hours: int = Query(default=24, ge=1, le=168),
    db: AsyncSession = Depends(get_session)
):
    """Get statistics for a heat exchanger"""
    start_time = datetime.utcnow() - timedelta(hours=hours)
    
    query = select(
        func.avg(MonitoringData.temperature).label("avg_temperature"),
        func.max(MonitoringData.temperature).label("max_temperature"),
        func.min(MonitoringData.temperature).label("min_temperature"),
        func.avg(MonitoringData.fan_speed).label("avg_fan_speed"),
        func.avg(MonitoringData.power_consumption).label("avg_power_consumption"),
        func.count(MonitoringData.id).label("total_data_points")
    ).where(
        MonitoringData.heat_exchanger_id == heat_exchanger_id,
        MonitoringData.timestamp >= start_time
    )
    
    result = await db.execute(query)
    stats = result.one_or_none()
    
    if not stats or stats.total_data_points == 0:
        return MonitoringStats(
            avg_temperature=0,
            max_temperature=0,
            min_temperature=0,
            avg_fan_speed=0,
            avg_power_consumption=0,
            total_data_points=0
        )
    
    return MonitoringStats(
        avg_temperature=float(stats.avg_temperature or 0),
        max_temperature=float(stats.max_temperature or 0),
        min_temperature=float(stats.min_temperature or 0),
        avg_fan_speed=float(stats.avg_fan_speed or 0),
        avg_power_consumption=float(stats.avg_power_consumption or 0),
        total_data_points=int(stats.total_data_points)
    )
