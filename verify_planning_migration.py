import sqlite3

conn = sqlite3.connect('marches_publics.db')
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(market_plannings)")
columns = cursor.fetchall()
column_names = [col[1] for col in columns]

print("Market_plannings table columns:")
for col in columns:
    print(f"  {col[1]} ({col[2]})")

print(f"\nTotal columns: {len(columns)}")
print(f"Has master_of_work: {'master_of_work' in column_names}")
print(f"Has progress_percentage: {'progress_percentage' in column_names}")

conn.close()
