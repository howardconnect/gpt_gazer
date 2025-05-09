import sqlite3

conn = sqlite3.connect("database.db")
cur = conn.cursor()

# Check if the 'archived' column exists
cur.execute("PRAGMA table_info(documents)")
columns = [col[1] for col in cur.fetchall()]
print(f"📋 Columns in DB: {columns}")

# Show all non-archived entries (what the web UI shows)
print("\n🌐 Visible documents (archived = 0):")
for row in cur.execute("SELECT filename FROM documents WHERE archived = 0"):
    print(f" - {row[0]}")

# Show any archived entries if they exist
if "archived" in columns:
    print("\n🗃 Archived documents:")
    for row in cur.execute("SELECT filename FROM documents WHERE archived = 1"):
        print(f" - {row[0]}")

conn.close()
