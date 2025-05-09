import sqlite3

conn = sqlite3.connect("database.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT,
    common_name TEXT,
    summary TEXT,
    keyword TEXT,
    file_size INTEGER,
    category TEXT,
    hash TEXT,
    archived BOOLEAN DEFAULT 0,
    thumbnail_path TEXT,
    preview_path TEXT,
    date_added TEXT
)
""")

conn.commit()
conn.close()

print("✅ database.db initialized successfully.")
