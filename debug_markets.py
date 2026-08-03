import sqlite3
import sys

db_path = 'marches_publics.db'

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if markets table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='markets'")
    table_exists = cursor.fetchone()
    
    if not table_exists:
        print("ERROR: Markets table does not exist")
        sys.exit(1)
    
    # Count markets
    cursor.execute("SELECT COUNT(*) FROM markets")
    count = cursor.fetchone()[0]
    
    print(f"Total markets in database: {count}")
    
    if count > 0:
        cursor.execute("SELECT id, market_number, object, master_of_work, market_type, estimated_amount, status, progress_percentage FROM markets LIMIT 10")
        markets = cursor.fetchall()
        print("\nMarkets in database:")
        print("ID | Number | Object | Master | Type | Amount | Status | Progress")
        print("-" * 80)
        for market in markets:
            print(f"{market[0]} | {market[1]} | {market[2][:20]} | {market[3][:15]} | {market[4]} | {market[5]} | {market[6]} | {market[7]}%")
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
    import traceback
    traceback.print_exc()
