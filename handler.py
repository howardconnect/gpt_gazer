import sys
import os
import sqlite3
import time
from datetime import datetime
from dotenv import load_dotenv
from utils.extractors import extract_text_from_file
from utils.gpt_client import summarize_with_gpt
from utils.file_ops import generate_thumbnail, hash_file, rename_file
from logger import logger  # ✅ added logger

# Load environment and check watch folder
load_dotenv()
DB_PATH = "database.db"
WATCH_FOLDER = os.getenv("WATCH_FOLDER")

if not WATCH_FOLDER:
    raise ValueError("❌ WATCH_FOLDER is not set in .env")

if not os.path.exists(WATCH_FOLDER):
    raise FileNotFoundError(f"❌ WATCH_FOLDER path does not exist: {WATCH_FOLDER}")

if not os.access(WATCH_FOLDER, os.R_OK | os.W_OK):
    raise PermissionError(f"❌ WATCH_FOLDER is not readable or writable: {WATCH_FOLDER}")

VALID_EXTENSIONS = (
    ".txt", ".pdf", ".docx", ".pptx", ".md",
    ".log", ".json", ".xml", ".rtf", ".html", ".eml"
)

def process_file(filepath, source="watcher"):
    for _ in range(5):
        try:
            with open(filepath, "rb"):
                break
        except PermissionError:
            logger.warning(f"⏳ File is locked, retrying: {filepath}")
            time.sleep(1)
    else:
        logger.error(f"❌ File remained locked: {filepath}")
        return

    try:
        ext = os.path.splitext(filepath)[1].lower()
        if ext not in VALID_EXTENSIONS:
            logger.warning(f"⚠️ Unsupported file type: {filepath}")
            return

        logger.info(f"📄 Processing ({source}): {filepath}")
        filename = os.path.basename(filepath)
        file_size = os.path.getsize(filepath)

        text = extract_text_from_file(filepath)
        if not text.strip():
            logger.error(f"❌ No text extracted from {filename}")
            return

        chunks = chunk_text(text, max_tokens=3000)
        result = summarize_with_gpt(chunks[0])
        logger.info(f"🤖 GPT title: {result.get('filename')} | summary preview: {result.get('summary', '')[:100]}...")

        new_name    = result.get("filename", filename)
        common_name = result.get("common_name", os.path.splitext(filename)[0])
        summary     = result.get("summary", "No summary provided.")
        keyword     = result.get("keyword", "Uncategorized")
        category    = result.get("category", "Unsorted")

        final_path = rename_file(filepath, new_name)
        filename = os.path.basename(final_path)  # ✅ normalized filename used for DB

        thumb_path, preview_path = generate_thumbnail(final_path)

        if not thumb_path or not preview_path:
            logger.warning(f"⚠️ Thumbnails not generated for: {filename}")

        file_hash = hash_file(final_path)

        save_or_update_document(
            filename, final_path, common_name, summary, keyword,
            file_size, category, file_hash, thumb_path, preview_path
        )

        logger.info(f"✅ Indexed and saved: {final_path}")

    except Exception as e:
        logger.exception(f"❌ Error processing file {filepath}: {e}")

def chunk_text(text, max_tokens=3000):
    chunk_size = max_tokens * 4
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

def save_or_update_document(filename, filepath, common_name, summary, keyword, file_size, category, file_hash, thumb, preview):
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        # 🧠 Check if this exact hash is already in the DB under another filename
        cur.execute("SELECT filename FROM documents WHERE hash = ?", (file_hash,))
        dupe = cur.fetchone()
        if dupe and dupe[0] != filename:
            logger.warning(f"⚠️ Duplicate content detected — already saved as: {dupe[0]}")
            conn.close()
            return

        # Check if filename already exists
        cur.execute("SELECT 1 FROM documents WHERE filename = ?", (filename,))
        exists = cur.fetchone()

        if exists:
            cur.execute("""
                UPDATE documents SET
                    common_name = ?,
                    summary = ?,
                    keyword = ?,
                    file_size = ?,
                    category = ?,
                    hash = ?,
                    thumbnail_path = ?,
                    preview_path = ?,
                    date_added = ?
                WHERE filename = ?
            """, (
                common_name, summary, keyword, file_size, category,
                file_hash, thumb, preview, datetime.now().isoformat(),
                filename
            ))
            logger.info(f"🔄 Updated record: {filepath}")
        else:
            cur.execute("""
                INSERT INTO documents 
                (filename, common_name, summary, keyword, file_size, category, hash, thumbnail_path, preview_path, date_added)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                filename, common_name, summary, keyword,
                file_size, category, file_hash, thumb, preview,
                datetime.now().isoformat()
            ))
            logger.info(f"🆕 Inserted new record: {filepath}")

        conn.commit()
        conn.close()
    except Exception as e:
        logger.exception(f"❌ Failed to save/update DB for {filepath}: {e}")

def remove_from_db(filename):
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("DELETE FROM documents WHERE filename = ?", (filename,))
        conn.commit()
        conn.close()
        logger.info(f"🗑 Removed from DB: {filename}")
    except Exception as e:
        logger.exception(f"❌ DB deletion error for {filename}: {e}")

def repair_thumbnails_for_db():
    logger.info("🛠️ Starting thumbnail repair...")
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT filename FROM documents")
        files = cur.fetchall()
        conn.close()

        for (filename,) in files:
            full_path = os.path.join(WATCH_FOLDER, filename)
            if not os.path.exists(full_path):
                logger.warning(f"❌ File missing for repair: {filename}")
                continue

            thumb_name = f"thumb_{filename}.jpg"
            preview_name = f"preview_{filename}.jpg"
            thumb_path = os.path.join("static/thumbnails", thumb_name)
            preview_path = os.path.join("static/thumbnails", preview_name)

            if not os.path.exists(thumb_path) or not os.path.exists(preview_path):
                logger.info(f"🔁 Regenerating thumbnails for: {filename}")
                new_thumb, new_preview = generate_thumbnail(full_path)
                if new_thumb and new_preview:
                    conn = sqlite3.connect(DB_PATH)
                    cur = conn.cursor()
                    cur.execute("""
                        UPDATE documents SET
                            thumbnail_path = ?,
                            preview_path = ?,
                            date_added = ?
                        WHERE filename = ?
                    """, (new_thumb, new_preview, datetime.now().isoformat(), filename))
                    conn.commit()
                    conn.close()
                    logger.info(f"✅ Thumbnails repaired: {filename}")
                else:
                    logger.warning(f"⚠️ Failed to regenerate thumbnails for: {filename}")

        logger.info("✅ Thumbnail repair complete.")

    except Exception as e:
        logger.exception(f"❌ Thumbnail repair failed: {e}")
