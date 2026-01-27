"""
Run the Cooling Monitor application.

For local development: python run.py --local
For production behind nginx at /cooling-monitor: python run.py --proxy
"""
import sys
import uvicorn

if __name__ == "__main__":
    # Check if running behind proxy
    use_proxy = "--proxy" in sys.argv
    
    if use_proxy:
        # Import the proxy wrapper that mounts at /cooling-monitor
        from app.main_proxy import app
        print("[START] Starting Cooling Monitor in PROXY mode (mounted at /cooling-monitor)")
    else:
        # Import the regular app
        from app.main import app
        print("[START] Starting Cooling Monitor in LOCAL mode (mounted at /)")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload="--reload" in sys.argv
    )
