import sqlite3

conn = sqlite3.connect('marches_publics.db')
cursor = conn.cursor()

# Check if planning_id column exists
cursor.execute("PRAGMA table_info(markets)")
columns = cursor.fetchall()
column_names = [col[1] for col in columns]

print("=" * 50)
print("DATABASE SCHEMA CHECK")
print("=" * 50)
print(f"Total columns in markets table: {len(columns)}")
print(f"Has planning_id: {'planning_id' in column_names}")
print("\nAll columns:")
for col in columns:
    print(f"  {col[1]} ({col[2]})")

if 'planning_id' not in column_names:
    print("\n" + "=" * 50)
    print("ERROR: planning_id column is MISSING!")
    print("=" * 50)
    print("Adding column...")
    cursor.execute("ALTER TABLE markets ADD COLUMN planning_id INTEGER")
    conn.commit()
    print("Column added")
    
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_markets_planning_id ON markets(planning_id)")
    conn.commit()
    print("Index created")
    
    # Verify
    cursor.execute("PRAGMA table_info(markets)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    print(f"\nAfter fix - Has planning_id: {'planning_id' in column_names}")
else:
    print("\n" + "=" * 50)
    print("OK: planning_id column EXISTS")
    print("=" * 50)

conn.close()
