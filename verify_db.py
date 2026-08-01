import sqlite3

conn = sqlite3.connect('marches_publics.db')
cursor = conn.cursor()

# Check markets table
cursor.execute("PRAGMA table_info(markets)")
columns = cursor.fetchall()
column_names = [col[1] for col in columns]

print("Markets table columns:")
for col in columns:
    print(f"  {col[1]} ({col[2]})")

print(f"\nTotal columns: {len(columns)}")
print(f"Has planning_id: {'planning_id' in column_names}")

conn.close()
