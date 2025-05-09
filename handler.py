import sys
import os
import sqlite3
import time
from datetime import datetime
from dotenv import load_dotenv
from utils.extractors import extract_text_from_file
from utils.gpt_client import summarize_with_gpt
from utils.file_ops import generate_thumbnail, hash_file, rename_file

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
            print(f"⏳ File is locked, retrying: {filepath}")
            time.sleep(1)
    else:
        print(f"❌ File remained locked: {filepath}")
        return

    try:
        ext = os.path.splitext(filepath)[1].lower()
        if ext not in VALID_EXTENSIONS:
            print(f"⚠️ Unsupported file type: {filepath}")
            return

        print(f"\n📄 Processing ({source}): {filepath}")
        filename = os.path.basename(filepath)
        file_size = os.path.getsize(filepath)

        text = extract_text_from_file(filepath)
        if not text.strip():
            print(f"❌ No text extracted from {filename}")
            return

        chunks = chunk_text(text, max_tokens=3000)
        result = summarize_with_gpt(chunks[0])
        print(f"🤖 GPT Result: {result}")

        new_name    = result.get("filename", filename)
        common_name = result.get("common_name", os.path.splitext(filename)[0])
        summary     = result.get("summary", "No summary provided.")
        keyword     = result.get("keyword", "Uncategorized")
        category    = result.get("category", "Unsorted")

        new_path   = rename_file(filepath, new_name)
        final_path = new_path

        thumb_path, preview_path = generate_thumbnail(final_path)
        file_hash = hash_file(final_path)

        save_or_update_document(
            final_path, common_name, summary, keyword,
            file_size, category, file_hash, thumb_path, preview_path
        )

        print(f"✅ Indexed and saved: {final_path}")

    except Exception as e:
        print(f"❌ Error processing file {filepath}: {e}")

def chunk_text(text, max_tokens=3000):
    chunk_size = max_tokens * 4
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

def save_or_update_document(filepath, common_name, summary, keyword, file_size, category, file_hash, thumb, preview):
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        # 🧠 Check if this exact hash is already in the DB under another filename
        cur.execute("SELECT filename FROM documents WHERE hash = ?", (file_hash,))
        dupe = cur.fetchone()
        if dupe and dupe[0] != os.path.basename(filepath):
            print(f"⚠️ Duplicate content detected — already saved as: {dupe[0]}")
            conn.close()
            return

        # Check if filename already exists
        cur.execute("SELECT 1 FROM documents WHERE filename = ?", (os.path.basename(filepath),))
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
                os.path.basename(filepath)
            ))
            print(f"🔄 Updated record: {filepath}")
        else:
            cur.execute("""
                INSERT INTO documents 
                (filename, common_name, summary, keyword, file_size, category, hash, thumbnail_path, preview_path, date_added)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                os.path.basename(filepath), common_name, summary, keyword,
                file_size, category, file_hash, thumb, preview,
                datetime.now().isoformat()
            ))
            print(f"🆕 Inserted new record: {filepath}")

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"❌ Failed to save/update DB for {filepath}: {e}")
