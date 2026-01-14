"""Test script for Microsoft Teams webhook"""
import sqlite3
import json
import asyncio
import httpx
from datetime import datetime
import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def get_teams_settings():
    """Get Teams settings from database"""
    conn = sqlite3.connect('cooling_monitor.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT teams_enabled, teams_webhook_url
        FROM system_settings
        LIMIT 1
    """)
    
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        print("❌ No settings found in database. Please configure via Settings page.")
        return None
    
    return {
        'enabled': bool(row[0]),
        'webhook_url': row[1]
    }


async def send_test_teams_message():
    """Send a test message to Teams webhook"""
    print("💬 Microsoft Teams Webhook Test")
    print("=" * 50)
    
    # Load settings
    print("\n1️⃣ Loading Teams settings from database...")
    settings = get_teams_settings()
    
    if not settings:
        return False
    
    # Check if enabled
    if not settings['enabled']:
        print("⚠️  Teams notifications are DISABLED in settings")
        print("   Enable them via the Settings page first")
        return False
    
    if not settings['webhook_url']:
        print("❌ No webhook URL configured!")
        print("   Configure it via the Settings page")
        return False
    
    print(f"✓ Webhook URL: {settings['webhook_url'][:50]}...")
    
    # Create test message
    print("\n2️⃣ Creating test message...")
    card = {
        "@type": "MessageCard",
        "@context": "https://schema.org/extensions",
        "themeColor": "0078D4",  # Blue for test
        "summary": "🧪 Test Message - Cooling Monitor System",
        "sections": [
            {
                "activityTitle": "🧪 Test Notification",
                "activitySubtitle": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
                "facts": [
                    {
                        "name": "Status:",
                        "value": "✅ Teams webhook is working!"
                    },
                    {
                        "name": "System:",
                        "value": "Cooling Monitor"
                    },
                    {
                        "name": "Type:",
                        "value": "Test Message"
                    }
                ],
                "markdown": True
            },
            {
                "text": "If you see this message, your Teams webhook is configured correctly and urgent alarms will be delivered to this channel."
            }
        ]
    }
    print("✓ Test message created")
    
    # Send to Teams
    print("\n3️⃣ Sending to Teams webhook...")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                settings['webhook_url'],
                json=card
            )
            response.raise_for_status()
        
        print("✓ Message sent successfully!")
        print("\n" + "=" * 50)
        print("✅ SUCCESS! Check your Teams channel for the test message!")
        print("=" * 50)
        return True
        
    except httpx.HTTPStatusError as e:
        print(f"\n❌ HTTP error: {e.response.status_code}")
        print(f"   Response: {e.response.text}")
        print("\n   Possible fixes:")
        print("   - Verify the webhook URL is correct")
        print("   - Make sure the webhook hasn't been deleted in Teams")
        print("   - Check if you have permission to post to the channel")
        return False
        
    except Exception as e:
        print(f"\n❌ Failed to send Teams message: {e}")
        return False


if __name__ == '__main__':
    try:
        success = asyncio.run(send_test_teams_message())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
