"""
Migration script to add user role support
The existing is_admin field will be used:
- is_admin=1 means "admin" role
- is_admin=0 means "technician" role
"""
import sqlite3
import sys

def migrate():
    try:
        conn = sqlite3.connect('cooling_monitor.db')
        cursor = conn.cursor()
        
        # Check if users table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='users'
        """)
        
        if not cursor.fetchone():
            print("✅ Users table doesn't exist yet - will be created on first run")
            conn.close()
            return
        
        # Check current users
        cursor.execute("SELECT id, username, is_admin FROM users")
        users = cursor.fetchall()
        
        if not users:
            print("ℹ️ No users exist yet")
        else:
            print(f"✅ Found {len(users)} user(s):")
            for user_id, username, is_admin in users:
                role = "admin" if is_admin else "technician"
                print(f"   - {username}: {role}")
        
        conn.commit()
        conn.close()
        
        print("\n✅ User roles migration complete")
        print("   Admin role: is_admin=1")
        print("   Technician role: is_admin=0")
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    migrate()
