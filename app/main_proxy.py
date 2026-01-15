"""
Proxy wrapper for mounting the Cooling Monitor app at /cooling-monitor
Use this when running behind nginx reverse proxy
"""
from fastapi import FastAPI
from app.main import app as cooling_monitor_app

# Create parent app
app = FastAPI(title="Cooling Monitor Proxy Wrapper")

# Mount the cooling monitor app at /cooling-monitor
app.mount("/cooling-monitor", cooling_monitor_app)

@app.get("/")
async def root():
    """Redirect root to cooling-monitor"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/cooling-monitor/")
