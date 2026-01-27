from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings
from app.database import init_db, close_db
from app.routers import heat_exchangers, monitoring, settings as settings_router, auth, alerts, users
from app.routers.auth import get_current_user, require_admin
from app.models.user import User
from app.services.websocket_manager import manager
from app.services.monitoring_service import monitoring_service


# Scheduler for background tasks
scheduler = AsyncIOScheduler()


def reschedule_polling_job(interval_seconds: int):
    """Reschedule the polling job with a new interval"""
    try:
        scheduler.reschedule_job(
            'poll_heat_exchangers',
            trigger='interval',
            seconds=interval_seconds
        )
        print(f"[RESCHEDULE] Rescheduled polling job to {interval_seconds}s interval")
    except Exception as e:
        print(f"[WARNING] Failed to reschedule polling job: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    await init_db()
    
    # Give database a moment to fully initialize
    import asyncio
    await asyncio.sleep(0.5)
    
    # Start monitoring scheduler
    scheduler.add_job(
        monitoring_service.poll_all_heat_exchangers,
        'interval',
        seconds=settings.polling_interval_seconds,
        id='poll_heat_exchangers'
    )
    scheduler.start()
    print(f"[OK] Monitoring service started (interval: {settings.polling_interval_seconds}s)")
    
    yield
    
    # Shutdown
    scheduler.shutdown()
    await close_db()


app = FastAPI(
    title="Cooling Monitor API",
    description="Real-time Heat Exchanger Monitoring System",
    version="1.0.0",
    lifespan=lifespan
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(heat_exchangers.router)
app.include_router(monitoring.router)
app.include_router(settings_router.router)
app.include_router(alerts.router)


# Health check
@app.get("/api/health")
async def health_check():
    from datetime import datetime
    return {
        "status": "OK",
        "timestamp": datetime.utcnow().isoformat()
    }


# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# Frontend routes
@app.get("/landing", response_class=HTMLResponse)
async def landing_page(request: Request):
    """Landing page for non-authenticated users"""
    return templates.TemplateResponse("landing.html", {"request": request})


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Dashboard - redirects to landing if not authenticated"""
    try:
        # Check if user has valid session
        from app.routers.auth import get_current_user_optional
        user = await get_current_user_optional(request)
        if not user:
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url=str(request.url_for("landing_page")), status_code=302)
    except:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=str(request.url_for("landing_page")), status_code=302)
    
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/heat-exchanger/{heat_exchanger_id}", response_class=HTMLResponse)
async def heat_exchanger_detail(request: Request, heat_exchanger_id: str):
    return templates.TemplateResponse("detail.html", {
        "request": request,
        "heat_exchanger_id": heat_exchanger_id
    })


@app.get("/heat-exchanger-form", response_class=HTMLResponse)
async def heat_exchanger_form(request: Request, id: str = None):
    """Heat exchanger form - requires admin privileges"""
    token = request.cookies.get("access_token")
    if not token:
        return templates.TemplateResponse("login.html", {"request": request})
    
    try:
        from app.database import async_session_maker
        async with async_session_maker() as db:
            user = await require_admin(await get_current_user(request, db))
            if not user:
                return templates.TemplateResponse("login.html", {"request": request})
    except Exception as e:
        return templates.TemplateResponse("login.html", {"request": request})
    
    return templates.TemplateResponse("form.html", {
        "request": request,
        "heat_exchanger_id": id
    })


@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """Settings page - requires admin privileges"""
    token = request.cookies.get("access_token")
    if not token:
        return templates.TemplateResponse("login.html", {"request": request})
    
    try:
        from app.database import async_session_maker
        async with async_session_maker() as db:
            user = await require_admin(await get_current_user(request, db))
            if not user:
                return templates.TemplateResponse("login.html", {"request": request})
    except Exception as e:
        return templates.TemplateResponse("login.html", {"request": request})
    
    return templates.TemplateResponse("settings.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/users", response_class=HTMLResponse)
async def users_page(request: Request):
    """User management page - requires admin privileges"""
    token = request.cookies.get("access_token")
    if not token:
        return templates.TemplateResponse("login.html", {"request": request})
    
    try:
        from app.database import async_session_maker
        async with async_session_maker() as db:
            user = await require_admin(await get_current_user(request, db))
            if not user:
                return templates.TemplateResponse("login.html", {"request": request})
    except Exception as e:
        return templates.TemplateResponse("login.html", {"request": request})
    
    return templates.TemplateResponse("users.html", {"request": request})


@app.get("/alerts", response_class=HTMLResponse)
async def alerts_page(request: Request):
    """Alerts management page"""
    return templates.TemplateResponse("alerts.html", {"request": request})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )
