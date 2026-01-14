import sqlite3

conn = sqlite3.connect('cooling_monitor.db')
cursor = conn.cursor()

cursor.execute('SELECT COUNT(*) FROM alerts')
print(f'Total alerts in DB: {cursor.fetchone()[0]}')

cursor.execute('SELECT id, type, severity, acknowledged, resolved, created_at FROM alerts ORDER BY created_at DESC LIMIT 10')
print('\nRecent alerts:')
for row in cursor.fetchall():
    print(f'  ID:{row[0]} Type:{row[1]} Severity:{row[2]} Ack:{row[3]} Res:{row[4]} Created:{row[5]}')

conn.close()
