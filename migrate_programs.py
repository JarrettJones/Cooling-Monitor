"""
Migration script to add programs table and program_id to heat_exchangers
"""
import sqlite3
import os

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), "cooling_monitor.db")

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Create programs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS programs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("[OK] Created programs table")
        
        # Add default programs
        default_programs = ["GB200", "GB300", "VR-NVL72", "Maia200", "Maia300"]
        for program in default_programs:
            cursor.execute("INSERT OR IGNORE INTO programs (name) VALUES (?)", (program,))
        print(f"[OK] Added {len(default_programs)} default programs")
        
        # Check if program_id column exists in heat_exchangers
        cursor.execute("PRAGMA table_info(heat_exchangers)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if "program_id" not in columns:
            cursor.execute("ALTER TABLE heat_exchangers ADD COLUMN program_id INTEGER")
            print("[OK] Added program_id column to heat_exchangers")
        else:
            print("[SKIP] program_id column already exists")
        
        conn.commit()
        print("\n[OK] Migration completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] Migration failed: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
