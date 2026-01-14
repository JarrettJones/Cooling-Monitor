"""
Migration: Add monitoring_enabled column to system_settings table
"""
import sqlite3

def migrate():
    conn = sqlite3.connect('cooling_monitor.db')
    cursor = conn.cursor()
    
    try:
        # Check if column exists
        cursor.execute("PRAGMA table_info(system_settings)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'monitoring_enabled' not in columns:
            # Add monitoring_enabled column with default True
            cursor.execute("""
                ALTER TABLE system_settings 
                ADD COLUMN monitoring_enabled INTEGER DEFAULT 1
            """)
            conn.commit()
            print("✅ Successfully added 'monitoring_enabled' column to system_settings table.")
            print("   Default value: True (monitoring enabled)")
        else:
            print("ℹ️  Column 'monitoring_enabled' already exists.")
    
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
