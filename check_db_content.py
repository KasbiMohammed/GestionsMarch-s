import sqlite3
import os

db_path = 'marches_publics.db'

print(f"Database exists: {os.path.exists(db_path)}")
print(f"Database size: {os.path.getsize(db_path) if os.path.exists(db_path) else 0} bytes")

if not os.path.exists(db_path):
    print("ERROR: Database file does not exist")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print(f"\nTables in database: {[t[0] for t in tables]}")

# Check markets table
if 'markets' in [t[0] for t in tables]:
    cursor.execute("SELECT COUNT(*) FROM markets")
    count = cursor.fetchone()[0]
    print(f"\nMarkets count: {count}")
    
    if count > 0:
        cursor.execute("SELECT id, market_number, object, status FROM markets LIMIT 5")
        markets = cursor.fetchall()
        print("\nSample markets:")
        for m in markets:
            print(f"  ID: {m[0]}, Number: {m[1]}, Object: {m[2]}, Status: {m[3]}")
    else:
        print("No markets in database")
else:
    print("Markets table does not exist")

conn.close()
