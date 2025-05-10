import sqlite3
from datetime import datetime

conn = sqlite3.connect("database.db")
cur = conn.cursor()

cur.execute("""
    INSERT INTO conflicts (
        existing_filename, new_filename,
        existing_summary, new_summary,
        diff_summary, status, date_added
    ) VALUES (?, ?, ?, ?, ?, ?, ?)
""", (
    "Old_Report.pdf", "New_Report.pdf",
    "Old report summary about 2023 budget and tax info.",
    "Updated report with corrected tax bracket and new figure totals.",
    "GPT: New doc has updated figures and minor sentence revisions.",
    "pending",
    datetime.now().isoformat()
))

conn.commit()
conn.close()
