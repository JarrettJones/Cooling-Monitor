"""
Migration script to add type column to heat_exchangers table
"""
import sqlite3
import sys

def migrate():
    try:
        conn = sqlite3.connect('cooling_monitor.db')
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(heat_exchangers)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'type' in columns:
            print("✅ Column 'type' already exists")
            conn.close()
            return
        
        # Add type column
        cursor.execute("""
            ALTER TABLE heat_exchangers 
            ADD COLUMN type TEXT
        """)
        
        conn.commit()
        conn.close()
        
        print("✅ Successfully added 'type' column to heat_exchangers table")
        print("   Type can be: Callan or Atlas")
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    migrate()
