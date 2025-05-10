import os
import sqlite3
from dotenv import load_dotenv
from handler import process_file

load_dotenv()
WATCH_FOLDER = os.getenv("WATCH_FOLDER")
DB_PATH = "database.db"

def run_startup_sync():
    print("🔄 Starting folder/database sync...")

    if not os.path.exists(WATCH_FOLDER):
        print(f"❌ Folder not found: {WATCH_FOLDER}")
        return

    actual_files = {
        f for f in os.listdir(WATCH_FOLDER)
        if f.lower().endswith((".pdf", ".txt", ".docx", ".md", ".html", ".eml", ".pptx", ".log", ".xml", ".rtf"))
    }

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT filename, thumbnail_path, summary FROM documents")
    db_rows = cur.fetchall()

    db_index = {row[0]: {"thumbnail": row[1], "summary": row[2]} for row in db_rows}

    for file in actual_files:
        full_path = os.path.join(WATCH_FOLDER, file)

        if file not in db_index:
            print(f"🆕 File not in DB: {file}")
            process_file(full_path, source="sync")
        else:
            needs_update = not db_index[file]["thumbnail"] or not db_index[file]["summary"]
            if needs_update:
                print(f"🔁 Incomplete metadata, reprocessing: {file}")
                process_file(full_path, source="sync")
            else:
                print(f"✅ Already complete: {file}")

    # 🗑 Permanently delete DB entries for missing files
    db_filenames = set(db_index.keys())
    missing_files = db_filenames - actual_files

    if missing_files:
        print(f"🗑 Deleting {len(missing_files)} missing files from DB...")
        for missing in missing_files:
            cur.execute("DELETE FROM documents WHERE filename = ?", (missing,))
            print(f"❌ Deleted from DB: {missing}")
        conn.commit()

    conn.close()
    print("✅ Sync complete.")
