# logger.py
import logging
import os
import sys
from logging.handlers import RotatingFileHandler

LOG_DIR = "logs"
LOG_PATH = os.path.join(LOG_DIR, "watcher.log")
os.makedirs(LOG_DIR, exist_ok=True)

logger = logging.getLogger("watcher_logger")
logger.setLevel(logging.INFO)

formatter = logging.Formatter(
    fmt="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# File handler (still writes emojis just fine)
file_handler = RotatingFileHandler(LOG_PATH, maxBytes=1_000_000, backupCount=5, encoding="utf-8")
file_handler.setFormatter(formatter)

# Console handler (fixes UnicodeEncodeError)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
console_handler.setStream(open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1))

logger.addHandler(file_handler)
logger.addHandler(console_handler)
