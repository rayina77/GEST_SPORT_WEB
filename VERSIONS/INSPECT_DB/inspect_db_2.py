import sqlite3

conn = sqlite3.connect("database/sport.db")

cursor = conn.cursor()

cursor.execute("SELECT * FROM athletes LIMIT 5")

print(cursor.fetchall())

conn.close()