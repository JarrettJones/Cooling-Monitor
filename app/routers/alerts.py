from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_
from datetime import datetime
from typing import List, Optional

from app.database import get_session
from app.models.alert import Alert, AlertResponse, AlertAcknowledge, AlertResolve, AlertComment
from app.models.heat_exchanger import HeatExchanger
from app.models.user import User
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("/", response_model=List[AlertResponse])
async def get_alerts(
    heat_exchanger_id: Optional[int] = Query(None),
    acknowledged: Optional[bool] = Query(None),
    resolved: Optional[bool] = Query(None),
    severity: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get all alerts with optional filters"""
    query = select(Alert, HeatExchanger.name).join(
        HeatExchanger, Alert.heat_exchanger_id == HeatExchanger.id
    )
    
    # Apply filters
    filters = []
    if heat_exchanger_id is not None:
        filters.append(Alert.heat_exchanger_id == heat_exchanger_id)
    if acknowledged is not None:
        filters.append(Alert.acknowledged == acknowledged)
    if resolved is not None:
        filters.append(Alert.resolved == resolved)
    if severity is not None:
        filters.append(Alert.severity == severity)
    
    if filters:
        query = query.where(and_(*filters))
    
    # Order by newest first
    query = query.order_by(desc(Alert.created_at)).limit(limit)
    
    result = await db.execute(query)
    rows = result.all()
    
    # Build response with heat exchanger name
    alerts = []
    for alert, he_name in rows:
        alert_dict = {
            "id": alert.id,
            "heat_exchanger_id": alert.heat_exchanger_id,
            "heat_exchanger_name": he_name,
            "type": alert.type,
            "severity": alert.severity,
            "title": alert.title,
            "description": alert.description,
            "pump_id": alert.pump_id,
            "pump_name": alert.pump_name,
            "flow_rate": alert.flow_rate,
            "threshold": alert.threshold,
            "acknowledged": alert.acknowledged,
            "resolved": alert.resolved,
            "acknowledged_by": alert.acknowledged_by,
            "resolved_by": alert.resolved_by,
            "comments": alert.comments,
            "created_at": alert.created_at,
            "acknowledged_at": alert.acknowledged_at,
            "resolved_at": alert.resolved_at
        }
        alerts.append(AlertResponse(**alert_dict))
    
    return alerts


@router.get("/count")
async def get_alert_count(
    acknowledged: Optional[bool] = Query(None),
    resolved: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get count of alerts matching filters"""
    query = select(Alert)
    
    filters = []
    if acknowledged is not None:
        filters.append(Alert.acknowledged == acknowledged)
    if resolved is not None:
        filters.append(Alert.resolved == resolved)
    
    if filters:
        query = query.where(and_(*filters))
    
    result = await db.execute(query)
    alerts = result.scalars().all()
    
    return {"count": len(alerts)}


@router.put("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: int,
    data: AlertAcknowledge,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Acknowledge an alert"""
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    if alert.acknowledged:
        raise HTTPException(status_code=400, detail="Alert already acknowledged")
    
    alert.acknowledged = True
    alert.acknowledged_by = current_user.username
    alert.acknowledged_at = datetime.utcnow()
    
    if data.comments:
        if alert.comments:
            alert.comments += f"\n\n[{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}] {current_user.username}: {data.comments}"
        else:
            alert.comments = f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}] {current_user.username}: {data.comments}"
    
    await db.commit()
    
    return {"message": "Alert acknowledged", "alert_id": alert_id}


@router.put("/{alert_id}/resolve")
async def resolve_alert(
    alert_id: int,
    data: AlertResolve,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Resolve an alert"""
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    if alert.resolved:
        raise HTTPException(status_code=400, detail="Alert already resolved")
    
    # Auto-acknowledge if not already acknowledged
    if not alert.acknowledged:
        alert.acknowledged = True
        alert.acknowledged_by = current_user.username
        alert.acknowledged_at = datetime.utcnow()
    
    alert.resolved = True
    alert.resolved_by = current_user.username
    alert.resolved_at = datetime.utcnow()
    
    if data.comments:
        if alert.comments:
            alert.comments += f"\n\n[{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}] {current_user.username} (RESOLVED): {data.comments}"
        else:
            alert.comments = f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}] {current_user.username} (RESOLVED): {data.comments}"
    
    await db.commit()
    
    return {"message": "Alert resolved", "alert_id": alert_id}


@router.post("/{alert_id}/comment")
async def add_comment(
    alert_id: int,
    data: AlertComment,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Add a comment to an alert"""
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    comment = f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}] {current_user.username}: {data.comments}"
    
    if alert.comments:
        alert.comments += f"\n\n{comment}"
    else:
        alert.comments = comment
    
    await db.commit()
    
    return {"message": "Comment added", "alert_id": alert_id}


@router.delete("/heat-exchanger/{heat_exchanger_id}/clear-all")
async def clear_all_alerts(
    heat_exchanger_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Clear (resolve) all alerts for a specific heat exchanger - Admin only"""
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Verify heat exchanger exists
    result = await db.execute(
        select(HeatExchanger).where(HeatExchanger.id == heat_exchanger_id)
    )
    heat_exchanger = result.scalar_one_or_none()
    
    if not heat_exchanger:
        raise HTTPException(status_code=404, detail="Heat exchanger not found")
    
    # Get all unresolved alerts for this heat exchanger
    result = await db.execute(
        select(Alert).where(
            and_(
                Alert.heat_exchanger_id == heat_exchanger_id,
                Alert.resolved == False
            )
        )
    )
    alerts = result.scalars().all()
    
    # Mark all as resolved
    now = datetime.utcnow()
    count = 0
    for alert in alerts:
        alert.resolved = True
        alert.resolved_by = current_user.username
        alert.resolved_at = now
        if not alert.acknowledged:
            alert.acknowledged = True
            alert.acknowledged_by = current_user.username
            alert.acknowledged_at = now
        count += 1
    
    await db.commit()
    
    return {
        "message": f"Cleared {count} alert(s) for {heat_exchanger.name}",
        "count": count,
        "heat_exchanger_name": heat_exchanger.name
    }
