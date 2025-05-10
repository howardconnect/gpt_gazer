import sqlite3
from datetime import datetime

conn = sqlite3.connect("database.db")
cur = conn.cursor()

# ✅ Create the conflicts table if it doesn't exist
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

# ✅ Insert a sample test conflict
cur.execute("""
    INSERT INTO conflicts (
        existing_filename, new_filename,
        existing_summary, new_summary,
        diff_summary, status, date_added
    ) VALUES (?, ?, ?, ?, ?, ?, ?)
""", (
    "Original_Syllabus.pdf", "Syllabus_New.pdf",
    "Original discusses Fall 2024 calendar and grading.",
    "Updated for Spring 2025 with new participation rules.",
    "GPT: Spring syllabus updates grading policy and dates.",
    "pending",
    datetime.now().isoformat()
))

conn.commit()
conn.close()
print("✅ Test conflict inserted and table ensured.")
