"""Migration script to add Teams webhook columns to system_settings table"""
import sqlite3

def migrate():
    conn = sqlite3.connect('cooling_monitor.db')
    cursor = conn.cursor()
    
    # Check existing columns
    cursor.execute("SELECT name FROM pragma_table_info('system_settings')")
    existing_columns = [row[0] for row in cursor.fetchall()]
    
    # Columns to add
    columns_to_add = [
        ('teams_enabled', 'INTEGER DEFAULT 0'),
        ('teams_webhook_url', 'TEXT DEFAULT ""')
    ]
    
    # Add missing columns
    added = []
    for col_name, col_type in columns_to_add:
        if col_name not in existing_columns:
            cursor.execute(f'ALTER TABLE system_settings ADD COLUMN {col_name} {col_type}')
            added.append(col_name)
            print(f'✓ Added column: {col_name}')
        else:
            print(f'  Skipped (already exists): {col_name}')
    
    conn.commit()
    conn.close()
    
    if added:
        print(f'\n✅ Migration complete! Added {len(added)} columns.')
    else:
        print('\n✅ Migration complete! All columns already exist.')

if __name__ == '__main__':
    migrate()
