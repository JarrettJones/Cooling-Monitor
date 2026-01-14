"""
Test script to create a sample alert for testing the alerts page
"""
import asyncio
from app.database import async_session_maker, init_db
from app.models.alert import Alert
from sqlalchemy import select
from app.models.heat_exchanger import HeatExchanger

async def create_test_alert():
    await init_db()
    
    async with async_session_maker() as db:
        # Get first heat exchanger
        result = await db.execute(select(HeatExchanger).limit(1))
        he = result.scalar_one_or_none()
        
        if not he:
            print("❌ No heat exchangers found. Add one first.")
            return
        
        # Create test alert
        alert = Alert(
            heat_exchanger_id=he.id,
            type="CRITICAL_LOW_FLOW",
            severity="critical",
            title=f"TEST: Critical Low Flow - Pump 1",
            description=f"TEST ALERT: Pump flow rate (5.2 L/min) dropped below critical threshold (10.0 L/min)",
            pump_id="1",
            pump_name="Pump 1",
            flow_rate=5.2,
            threshold=10.0,
            acknowledged=False,
            resolved=False
        )
        
        db.add(alert)
        await db.commit()
        
        print(f"✅ Created test alert for heat exchanger: {he.name}")
        print(f"   Alert ID: {alert.id}")
        print(f"   Title: {alert.title}")
        print(f"\nGo to http://localhost:8000/alerts to see it!")

if __name__ == "__main__":
    asyncio.run(create_test_alert())
