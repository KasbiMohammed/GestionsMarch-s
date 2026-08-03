import sqlite3

db_path = 'marches_publics.db'

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if markets table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='markets'")
    table_exists = cursor.fetchone()
    
    result = ""
    if table_exists:
        cursor.execute("SELECT COUNT(*) FROM markets")
        count = cursor.fetchone()[0]
        result += f"Markets table exists with {count} records\n"
        
        if count > 0:
            cursor.execute("SELECT id, market_number, object, status FROM markets LIMIT 5")
            markets = cursor.fetchall()
            result += "\nSample markets:\n"
            for market in markets:
                result += f"  ID: {market[0]}, Number: {market[1]}, Object: {market[2]}, Status: {market[3]}\n"
        else:
            result += "No markets found in database\n"
    else:
        result += "Markets table does not exist\n"
    
    conn.close()
    
    with open('markets_check_result.txt', 'w') as f:
        f.write(result)
    
    print("Check complete. See markets_check_result.txt")
    
except Exception as e:
    with open('markets_check_result.txt', 'w') as f:
        f.write(f"ERROR: {e}")
    print(f"ERROR: {e}")
