"""Migration script to add SMTP settings columns to system_settings table"""
import sqlite3

def migrate():
    conn = sqlite3.connect('cooling_monitor.db')
    cursor = conn.cursor()
    
    # Check existing columns
    cursor.execute("SELECT name FROM pragma_table_info('system_settings')")
    existing_columns = [row[0] for row in cursor.fetchall()]
    
    # Columns to add
    columns_to_add = [
        ('smtp_enabled', 'INTEGER DEFAULT 0'),
        ('smtp_server', 'TEXT DEFAULT "smtp.office365.com"'),
        ('smtp_port', 'INTEGER DEFAULT 587'),
        ('smtp_username', 'TEXT DEFAULT ""'),
        ('smtp_password', 'TEXT DEFAULT ""'),
        ('smtp_from_email', 'TEXT DEFAULT ""'),
        ('smtp_to_emails', 'TEXT DEFAULT ""'),
        ('smtp_use_tls', 'INTEGER DEFAULT 1'),
        ('pump_flow_critical_threshold', 'REAL DEFAULT 10.0')
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
