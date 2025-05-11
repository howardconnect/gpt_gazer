import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from dotenv import load_dotenv
from logger import logger
from handler import process_file, remove_from_db
from sync import run_startup_sync

load_dotenv()
WATCH_FOLDER = os.getenv("WATCH_FOLDER")

class NewFileHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.lower().endswith((
            ".txt", ".pdf", ".docx", ".pptx", ".md", ".log", ".json", ".xml", ".rtf", ".html", ".eml")):
            logger.info(f"🆕 New file detected: {event.src_path}")
            process_file(event.src_path, source="watcher")

    def on_deleted(self, event):
        if not event.is_directory and event.src_path.lower().endswith((
            ".txt", ".pdf", ".docx", ".pptx", ".md", ".log", ".json", ".xml", ".rtf", ".html", ".eml")):
            filename = os.path.basename(event.src_path)
            logger.info(f"🗑 File deleted: {filename}")
            remove_from_db(filename)

if __name__ == "__main__":
    if not os.path.exists(WATCH_FOLDER):
        logger.error(f"⚠️ Watch folder does not exist: {WATCH_FOLDER}")
        exit(1)

    run_startup_sync()  # 🟢 sync the folder and DB before watching

    observer = Observer()
    observer.schedule(NewFileHandler(), WATCH_FOLDER, recursive=False)
    observer.start()
    logger.info(f"👀 Watching for new files in: {WATCH_FOLDER}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
