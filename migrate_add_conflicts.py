import sqlite3

conn = sqlite3.connect("database.db")
cur = conn.cursor()

try:
    cur.execute("""
        CREATE TABLE IF NOT EXISTS conflicts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            existing_filename TEXT,
            new_filename TEXT,
            existing_summary TEXT,
            new_summary TEXT,
            diff_summary TEXT,
            status TEXT DEFAULT 'pending',
            action_taken TEXT,
            date_added TEXT
        )
    """)
    print("✅ 'conflicts' table created or already exists.")
except Exception as e:
    print(f"❌ Error creating conflicts table: {e}")

conn.commit()
conn.close()
