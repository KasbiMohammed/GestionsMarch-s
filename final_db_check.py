import sqlite3

db_path = 'marches_publics.db'

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check markets table
    cursor.execute("PRAGMA table_info(markets)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    
    result = f"Total columns: {len(columns)}\n"
    result += f"Column names: {column_names}\n"
    result += f"Has planning_id: {'planning_id' in column_names}\n"
    
    if 'planning_id' not in column_names:
        result += "ERROR: planning_id column is missing!\n"
        result += "Adding it now...\n"
        cursor.execute("ALTER TABLE markets ADD COLUMN planning_id INTEGER")
        conn.commit()
        result += "Column added\n"
        
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_markets_planning_id ON markets(planning_id)")
        conn.commit()
        result += "Index created\n"
        
        # Verify again
        cursor.execute("PRAGMA table_info(markets)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        result += f"After fix - Has planning_id: {'planning_id' in column_names}\n"
    else:
        result += "OK: planning_id column exists\n"
    
    conn.close()
    
    # Write to file
    with open('final_db_check_result.txt', 'w') as f:
        f.write(result)
    
    print("Check complete. See final_db_check_result.txt")
    
except Exception as e:
    with open('final_db_check_result.txt', 'w') as f:
        f.write(f"ERROR: {e}")
    print(f"ERROR: {e}")
