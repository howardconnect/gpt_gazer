import sqlite3

conn = sqlite3.connect("database.db")
cur = conn.cursor()

print("\n📄 Current Documents Table:")
for row in cur.execute("SELECT filename, hash, date_added FROM documents ORDER BY date_added DESC"):
    print(row)

conn.close()
