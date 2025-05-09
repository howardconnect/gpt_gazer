import sqlite3
conn = sqlite3.connect("database.db")
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM documents")
print("Rows:", cur.fetchone()[0])
conn.close()
