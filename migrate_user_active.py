"""
Migration script to add is_active column to users table
Run this once: python migrate_user_active.py
"""
import sqlite3
import sys

def migrate(db_path='cooling_monitor.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'is_active' not in columns:
            print("Adding is_active column to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN is_active INTEGER DEFAULT 0")
            
            # Set existing users to active (they're already in the system)
            cursor.execute("UPDATE users SET is_active = 1")
            
            conn.commit()
            print("✓ Migration completed successfully")
            print("✓ All existing users set to active")
        else:
            print("✓ Column is_active already exists")
            
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else 'cooling_monitor.db'
    migrate(db_path)
