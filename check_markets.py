import sqlite3

conn = sqlite3.connect('marches_publics.db')
cursor = conn.cursor()

# Check if markets table exists and has data
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='markets'")
table_exists = cursor.fetchone()

if table_exists:
    cursor.execute("SELECT COUNT(*) FROM markets")
    count = cursor.fetchone()[0]
    print(f"Markets table exists with {count} records")
    
    if count > 0:
        cursor.execute("SELECT id, market_number, object, status FROM markets LIMIT 5")
        markets = cursor.fetchall()
        print("\nSample markets:")
        for market in markets:
            print(f"  ID: {market[0]}, Number: {market[1]}, Object: {market[2]}, Status: {market[3]}")
    else:
        print("No markets found in database")
else:
    print("Markets table does not exist")

conn.close()
