"""Test script for SMTP email configuration"""
import sqlite3
import json
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import smtplib
import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.utils.encryption import decrypt_value


def get_smtp_settings():
    """Get SMTP settings from database"""
    conn = sqlite3.connect('cooling_monitor.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT smtp_enabled, smtp_server, smtp_port, smtp_username, 
               smtp_password, smtp_from_email, smtp_to_emails, smtp_use_tls
        FROM system_settings
        LIMIT 1
    """)
    
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        print("❌ No SMTP settings found in database. Please configure via Settings page.")
        return None
    
    return {
        'enabled': bool(row[0]),
        'server': row[1],
        'port': row[2],
        'username': row[3],
        'password': row[4],  # Encrypted
        'from_email': row[5],
        'to_emails': json.loads(row[6]) if row[6] else [],
        'use_tls': bool(row[7])
    }


def send_test_email():
    """Send a test email using database SMTP settings"""
    print("📧 SMTP Email Configuration Test")
    print("=" * 50)
    
    # Load settings
    print("\n1️⃣ Loading SMTP settings from database...")
    settings = get_smtp_settings()
    
    if not settings:
        return False
    
    # Check if enabled
    if not settings['enabled']:
        print("⚠️  Email alerts are DISABLED in settings")
        print("   Enable them via the Settings page first")
        return False
    
    print(f"✓ SMTP Server: {settings['server']}:{settings['port']}")
    print(f"✓ Username: {settings['username']}")
    print(f"✓ From: {settings['from_email']}")
    print(f"✓ To: {', '.join(settings['to_emails'])}")
    print(f"✓ TLS: {'Enabled' if settings['use_tls'] else 'Disabled'}")
    
    if not settings['to_emails']:
        print("❌ No recipient emails configured!")
        return False
    
    # Decrypt password
    print("\n2️⃣ Decrypting password...")
    try:
        decrypted_password = decrypt_value(settings['password']) if settings['password'] else ""
        if not decrypted_password:
            print("❌ No password configured!")
            return False
        print(f"✓ Password decrypted successfully ({len(decrypted_password)} chars)")
    except Exception as e:
        print(f"❌ Failed to decrypt password: {e}")
        return False
    
    # Create test message
    print("\n3️⃣ Creating test message...")
    message = MIMEMultipart()
    message["From"] = settings['from_email']
    message["To"] = ", ".join(settings['to_emails'])
    message["Subject"] = "🧪 Test Email - Cooling Monitor System"
    
    body = f"""
This is a TEST EMAIL from the Cooling Monitor system.

If you received this email, your SMTP configuration is working correctly!

Configuration Details:
- SMTP Server: {settings['server']}:{settings['port']}
- From: {settings['from_email']}
- Username: {settings['username']}
- TLS: {'Enabled' if settings['use_tls'] else 'Disabled'}

Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

You can safely delete this test email.
"""
    
    message.attach(MIMEText(body, "plain"))
    print(f"✓ Test message created")
    
    # Send email
    print("\n4️⃣ Connecting to SMTP server...")
    try:
        with smtplib.SMTP(settings['server'], settings['port'], timeout=10) as server:
            server.set_debuglevel(0)  # Set to 1 for verbose debugging
            
            if settings['use_tls']:
                print("✓ Starting TLS...")
                server.starttls()
                print("✓ TLS established")
            
            print("✓ Authenticating...")
            server.login(settings['username'], decrypted_password)
            print("✓ Authentication successful")
            
            print("✓ Sending email...")
            server.send_message(message)
            print("✓ Email sent successfully!")
        
        print("\n" + "=" * 50)
        print("✅ SUCCESS! Test email sent successfully!")
        print("=" * 50)
        print(f"\nCheck your inbox at: {', '.join(settings['to_emails'])}")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"\n❌ Authentication failed!")
        print(f"   Error: {e}")
        print("\n   Possible fixes:")
        print("   - Verify username is correct")
        print("   - Use an App Password (not regular password) for Microsoft 365")
        print("   - Check if MFA is enabled (requires app password)")
        return False
        
    except smtplib.SMTPException as e:
        print(f"\n❌ SMTP error: {e}")
        return False
        
    except Exception as e:
        print(f"\n❌ Failed to send email: {e}")
        return False


if __name__ == '__main__':
    try:
        success = send_test_email()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
