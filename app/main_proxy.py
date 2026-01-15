"""
Proxy wrapper for mounting the Cooling Monitor app at /cooling-monitor
Use this when running behind nginx reverse proxy
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database and services when app starts"""
    # Import here to ensure proper initialization order
    from app.database import init_db, close_db
    from app.services.monitoring_service import MonitoringService
    from app.core.config import settings
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    
    # Initialize database
    await init_db()
    print("✓ Database initialized (proxy mode)")
    
    # Initialize monitoring service
    monitoring_service = MonitoringService()
    scheduler = AsyncIOScheduler()
    
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
    print(f"✓ Monitoring service started (interval: {settings.polling_interval_seconds}s)")
    
    yield
    
    # Shutdown
    scheduler.shutdown()
    await close_db()

# Create parent app with lifespan
app = FastAPI(
    title="Cooling Monitor Proxy Wrapper",
    lifespan=lifespan
)

# Import the cooling monitor app WITHOUT lifespan (to avoid double initialization)
from app.main import app as cooling_monitor_app

# Mount the cooling monitor app at /cooling-monitor
app.mount("/cooling-monitor", cooling_monitor_app)

print("✓ Mounted cooling_monitor_app at /cooling-monitor")
print(f"✓ Available routes:")
for route in app.routes:
    print(f"  - {route.path}")

@app.get("/")
async def root():
    """Redirect root to cooling-monitor"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/cooling-monitor/")
