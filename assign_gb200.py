import sqlite3

conn = sqlite3.connect('cooling_monitor.db')
cursor = conn.cursor()

# Update all heat exchangers to GB200 program
cursor.execute("""
    UPDATE heat_exchangers 
    SET program_id = (SELECT id FROM programs WHERE name = 'GB200')
""")

affected = cursor.rowcount
conn.commit()
conn.close()

print(f'Updated {affected} heat exchangers to GB200')
