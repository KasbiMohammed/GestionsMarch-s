import sqlite3

db_path = 'marches_publics.db'

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check markets table
    cursor.execute("SELECT COUNT(*) FROM markets")
    count = cursor.fetchone()[0]
    
    print(f"Total markets in database: {count}")
    
    if count > 0:
        cursor.execute("SELECT id, market_number, object, status, created_at FROM markets ORDER BY created_at DESC LIMIT 5")
        markets = cursor.fetchall()
        print("\nRecent markets:")
        for market in markets:
            print(f"  ID: {market[0]}, Number: {market[1]}, Object: {market[2]}, Status: {market[3]}, Created: {market[4]}")
    else:
        print("No markets found in database")
    
    # Check planning_id column
    cursor.execute("PRAGMA table_info(markets)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    print(f"\nHas planning_id column: {'planning_id' in column_names}")
    
    conn.close()
    
except Exception as e:
    print(f"ERROR: {e}")
