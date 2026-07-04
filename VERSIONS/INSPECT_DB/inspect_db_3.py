import sqlite3

conn = sqlite3.connect("database/sport.db")

cursor = conn.cursor()

print("\n===== LIGUES =====\n")

cursor.execute("""
SELECT *
FROM ligues
LIMIT 5
""")

for row in cursor.fetchall():
    print(row)

print("\n===== FEDERATIONS =====\n")

cursor.execute("""
SELECT *
FROM federations
LIMIT 5
""")

for row in cursor.fetchall():
    print(row)

conn.close()