"""
Migration script to add polling_interval_seconds column to system_settings table
"""
import sqlite3
import sys

def migrate():
    try:
        conn = sqlite3.connect('cooling_monitor.db')
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("PRAGMA table_info(system_settings)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'polling_interval_seconds' in columns:
            print("⚠️  Column 'polling_interval_seconds' already exists in system_settings table")
            return
        
        # Add the column with default value of 30 seconds
        cursor.execute("""
            ALTER TABLE system_settings 
            ADD COLUMN polling_interval_seconds INTEGER DEFAULT 30
        """)
        
        conn.commit()
        print("✅ Successfully added 'polling_interval_seconds' column to system_settings table")
        print("   Default value: 30 seconds")
        
    except sqlite3.Error as e:
        print(f"❌ Error during migration: {e}")
        sys.exit(1)
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    migrate()
