import os
import sqlite3
import glob
from dotenv import load_dotenv
from handler import process_file
from logger import logger  # ✅ unified logging

load_dotenv()
WATCH_FOLDER = os.getenv("WATCH_FOLDER")
DB_PATH = "database.db"
THUMBNAIL_DIR = "static/thumbnails"

def run_startup_sync():
    logger.info("🔄 Starting folder/database sync...")

    if not os.path.exists(WATCH_FOLDER):
        logger.error(f"❌ Folder not found: {WATCH_FOLDER}")
        return

    # 1. Get actual files
    actual_files = {
        f for f in os.listdir(WATCH_FOLDER)
        if f.lower().endswith((".pdf", ".txt", ".docx", ".md", ".html", ".eml", ".pptx", ".log", ".xml", ".rtf"))
    }

    # 2. First pass: get current DB index
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT filename, thumbnail_path, summary FROM documents")
    db_rows = cur.fetchall()
    conn.close()

    db_index = {row[0]: {"thumbnail": row[1], "summary": row[2]} for row in db_rows}

    # 3. Process files that need added or updated
    files_to_process = []
    for file in actual_files:
        if file not in db_index:
            logger.info(f"🆕 File not in DB: {file}")
            files_to_process.append(file)
        else:
            needs_update = not db_index[file]["thumbnail"] or not db_index[file]["summary"]
            if needs_update:
                logger.info(f"🔁 Incomplete metadata, reprocessing: {file}")
                files_to_process.append(file)
            else:
                logger.info(f"✅ Already complete: {file}")

    for file in files_to_process:
        full_path = os.path.join(WATCH_FOLDER, file)
        process_file(full_path, source="sync")

    # 4. Reconnect and update DB for missing files
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT filename FROM documents")
    db_filenames = set(row[0] for row in cur.fetchall())

    missing_files = db_filenames - actual_files
    if missing_files:
        logger.info(f"🗑 Deleting {len(missing_files)} missing files from DB...")
        for missing in missing_files:
            cur.execute("DELETE FROM documents WHERE filename = ?", (missing,))
            logger.warning(f"❌ Deleted from DB: {missing}")
        conn.commit()

    conn.close()

    # 5. ✅ Now safe to clean thumbnails
    cleanup_orphan_thumbnails()

    logger.info("✅ Sync complete.")

def cleanup_orphan_thumbnails(thumbnail_dir=THUMBNAIL_DIR):
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT filename FROM documents")
        valid_filenames = set(row[0] for row in cur.fetchall())
        conn.close()

        deleted = 0
        for thumb_path in glob.glob(os.path.join(thumbnail_dir, "*.jpg")):
            base = os.path.basename(thumb_path)
            normalized = base.replace("thumb_", "").replace("preview_", "")
            if normalized not in valid_filenames:
                os.remove(thumb_path)
                logger.info(f"🧹 Deleted orphaned thumbnail: {thumb_path}")
                deleted += 1

        if deleted == 0:
            logger.info("🧼 Thumbnail cleanup complete — no orphans found.")
        else:
            logger.info(f"🧼 Thumbnail cleanup removed {deleted} files.")
    except Exception as e:
        logger.exception(f"❌ Failed during thumbnail cleanup: {e}")
