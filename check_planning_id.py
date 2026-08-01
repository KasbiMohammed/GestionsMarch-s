import sqlite3

conn = sqlite3.connect('marches_publics.db')
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(markets)")
columns = cursor.fetchall()
column_names = [col[1] for col in columns]

with open('db_check_result.txt', 'w') as f:
    f.write(f"Total columns: {len(columns)}\n")
    f.write(f"Column names: {column_names}\n")
    f.write(f"Has planning_id: {'planning_id' in column_names}\n")
    
    if 'planning_id' not in column_names:
        f.write("ERROR: planning_id column is missing!\n")
        f.write("Adding it now...\n")
        cursor.execute("ALTER TABLE markets ADD COLUMN planning_id INTEGER")
        conn.commit()
        f.write("Column added\n")
        
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_markets_planning_id ON markets(planning_id)")
        conn.commit()
        f.write("Index created\n")
        
        # Verify again
        cursor.execute("PRAGMA table_info(markets)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        f.write(f"After fix - Has planning_id: {'planning_id' in column_names}\n")
    else:
        f.write("OK: planning_id column exists\n")

conn.close()
print("Check db_check_result.txt for results")
