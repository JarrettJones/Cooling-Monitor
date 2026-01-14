"""Migration script to create alerts table"""
import sqlite3

def migrate():
    conn = sqlite3.connect('cooling_monitor.db')
    cursor = conn.cursor()
    
    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='alerts'")
    if cursor.fetchone():
        print("  Table 'alerts' already exists, skipping creation")
        conn.close()
        return
    
    # Create alerts table
    cursor.execute("""
        CREATE TABLE alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            heat_exchanger_id INTEGER NOT NULL,
            type VARCHAR NOT NULL,
            severity VARCHAR NOT NULL DEFAULT 'critical',
            title VARCHAR NOT NULL,
            description TEXT,
            pump_id VARCHAR,
            pump_name VARCHAR,
            flow_rate REAL,
            threshold REAL,
            acknowledged INTEGER DEFAULT 0,
            resolved INTEGER DEFAULT 0,
            acknowledged_by VARCHAR,
            resolved_by VARCHAR,
            comments TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            acknowledged_at TIMESTAMP,
            resolved_at TIMESTAMP,
            FOREIGN KEY (heat_exchanger_id) REFERENCES heat_exchangers (id)
        )
    """)
    
    # Create indexes for performance
    cursor.execute("CREATE INDEX idx_alerts_heat_exchanger ON alerts(heat_exchanger_id)")
    cursor.execute("CREATE INDEX idx_alerts_acknowledged ON alerts(acknowledged)")
    cursor.execute("CREATE INDEX idx_alerts_resolved ON alerts(resolved)")
    cursor.execute("CREATE INDEX idx_alerts_created_at ON alerts(created_at DESC)")
    
    conn.commit()
    conn.close()
    
    print("✅ Created alerts table with indexes")

if __name__ == '__main__':
    migrate()
