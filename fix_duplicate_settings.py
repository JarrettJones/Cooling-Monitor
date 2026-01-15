#!/usr/bin/env python3
"""
Fix duplicate rows in system_settings table.
Keeps the most recently updated row and deletes the rest.
"""
import sqlite3
import sys

def fix_duplicate_settings(db_path='cooling_monitor.db'):
    """Remove duplicate system_settings rows, keeping only the most recent one."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check current state
        cursor.execute('SELECT COUNT(*) FROM system_settings')
        count = cursor.fetchone()[0]
        print(f"Current rows in system_settings: {count}")
        
        if count <= 1:
            print("No duplicates found. Database is clean.")
            return
        
        # Get all rows ordered by updated_at (most recent first)
        cursor.execute('''
            SELECT id, redfish_username, updated_at 
            FROM system_settings 
            ORDER BY updated_at DESC, id DESC
        ''')
        rows = cursor.fetchall()
        
        print("\nCurrent rows (newest first):")
        for row in rows:
            print(f"  ID: {row[0]}, Username: {row[1]}, Updated: {row[2]}")
        
        # Keep the first (most recent) row, delete the rest
        keep_id = rows[0][0]
        delete_ids = [row[0] for row in rows[1:]]
        
        print(f"\nKeeping row with ID: {keep_id}")
        print(f"Deleting rows with IDs: {delete_ids}")
        
        # Delete duplicate rows
        if delete_ids:
            placeholders = ','.join('?' * len(delete_ids))
            cursor.execute(f'DELETE FROM system_settings WHERE id IN ({placeholders})', delete_ids)
            conn.commit()
            print(f"\n✓ Successfully deleted {len(delete_ids)} duplicate row(s)")
        
        # Verify
        cursor.execute('SELECT COUNT(*) FROM system_settings')
        final_count = cursor.fetchone()[0]
        print(f"Final row count: {final_count}")
        
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}", file=sys.stderr)
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    db_path = sys.argv[1] if len(sys.argv) > 1 else 'cooling_monitor.db'
    print(f"Fixing duplicates in: {db_path}\n")
    fix_duplicate_settings(db_path)
