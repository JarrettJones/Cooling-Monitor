"""
Migration script to add new user registration fields to users table
Run this once: python migrate_user_active.py
"""
import sqlite3
import sys

def migrate(db_path='cooling_monitor.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check existing columns
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        
        migrations_run = []
        
        # Add is_active column
        if 'is_active' not in columns:
            print("Adding is_active column...")
            cursor.execute("ALTER TABLE users ADD COLUMN is_active INTEGER DEFAULT 0")
            cursor.execute("UPDATE users SET is_active = 1")  # Set existing users to active
            migrations_run.append("is_active")
        
        # Add email column
        if 'email' not in columns:
            print("Adding email column...")
            cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")
            # Set default email for existing users (username@microsoft.com)
            cursor.execute("UPDATE users SET email = username || '@microsoft.com'")
            migrations_run.append("email")
        
        # Add first_name column
        if 'first_name' not in columns:
            print("Adding first_name column...")
            cursor.execute("ALTER TABLE users ADD COLUMN first_name TEXT")
            # Set default first name to username for existing users
            cursor.execute("UPDATE users SET first_name = username")
            migrations_run.append("first_name")
        
        # Add last_name column
        if 'last_name' not in columns:
            print("Adding last_name column...")
            cursor.execute("ALTER TABLE users ADD COLUMN last_name TEXT")
            migrations_run.append("last_name")
        
        # Add team column
        if 'team' not in columns:
            print("Adding team column...")
            cursor.execute("ALTER TABLE users ADD COLUMN team TEXT")
            migrations_run.append("team")
        
        # Add business_justification column
        if 'business_justification' not in columns:
            print("Adding business_justification column...")
            cursor.execute("ALTER TABLE users ADD COLUMN business_justification TEXT")
            migrations_run.append("business_justification")
        
        conn.commit()
        
        if migrations_run:
            print(f"[OK] Migration completed successfully")
            print(f"[OK] Added columns: {', '.join(migrations_run)}")
            print(f"[OK] All existing users set to active with default values")
        else:
            print("[OK] All columns already exist, no migration needed")
            
    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else 'cooling_monitor.db'
    migrate(db_path)
