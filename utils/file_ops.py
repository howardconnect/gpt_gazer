import os
import time
import hashlib
from pdf2image import convert_from_path
from PIL import Image, ImageDraw, ImageFont
from docx import Document
from bs4 import BeautifulSoup
from email import policy
from email.parser import BytesParser

def generate_thumbnail(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    filename = os.path.basename(filepath)
    thumb_path = f"static/thumbnails/thumb_{filename}.jpg"
    preview_path = f"static/thumbnails/preview_{filename}.jpg"

    try:
        if ext == ".pdf":
            pages = convert_from_path(filepath, dpi=300, first_page=1, last_page=1)
            page = pages[0]

            small = page.copy()
            small.thumbnail((200, 200))
            small.save(thumb_path, "JPEG", quality=85)

            page.save(preview_path, "JPEG", quality=95)

        else:
            # Extract text content appropriately
            lines = []

            if ext in [".txt", ".md", ".log", ".json", ".xml", ".rtf"]:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.read().strip().splitlines()

            elif ext == ".docx":
                try:
                    doc = Document(filepath)
                    lines = [p.text for p in doc.paragraphs if p.text.strip()]
                except Exception as e:
                    print(f"❌ Failed to read DOCX for thumbnail: {e}")
                    lines = ["(Unreadable Word document)"]

            elif ext == ".html":
                try:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        soup = BeautifulSoup(f, "html.parser")
                        lines = soup.get_text(separator="\n").splitlines()
                except Exception as e:
                    print(f"❌ Failed to parse HTML for thumbnail: {e}")
                    lines = ["(Unreadable HTML document)"]

            elif ext == ".eml":
                try:
                    with open(filepath, "rb") as f:
                        msg = BytesParser(policy=policy.default).parse(f)
                        body = msg.get_body(preferencelist=('plain'))
                        content = body.get_content() if body else "(No plain text body)"
                        lines = content.splitlines()
                except Exception as e:
                    print(f"❌ Failed to parse EML for thumbnail: {e}")
                    lines = ["(Unreadable email)"]

            preview_text = "\n".join(lines[:25]) or "(Empty File)"
            img = Image.new("RGB", (800, 1000), color="white")
            draw = ImageDraw.Draw(img)

            try:
                font = ImageFont.truetype("arial.ttf", size=16)
            except:
                font = ImageFont.load_default()

            draw.multiline_text((20, 20), preview_text, fill="black", font=font, spacing=4)

            img.save(preview_path, "JPEG", quality=95)

            small = img.copy()
            small.thumbnail((200, 200))
            small.save(thumb_path, "JPEG", quality=85)

    except Exception as e:
        print(f"❌ Thumbnail error for {filename}: {e}")
        return "", ""

    return thumb_path, preview_path

def hash_file(filepath):
    hasher = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            buf = f.read()
            hasher.update(buf)
        return hasher.hexdigest()
    except Exception as e:
        print(f"❌ Hashing error for {filepath}: {e}")
        return ""

def rename_file(filepath, new_filename):
    folder = os.path.dirname(filepath)
    ext = os.path.splitext(filepath)[1]
    if not new_filename.endswith(ext):
        new_filename += ext
    new_path = os.path.join(folder, new_filename)

    if new_path == filepath:
        return filepath

    for attempt in range(5):
        try:
            os.rename(filepath, new_path)
            return new_path
        except PermissionError:
            print(f"⏳ File locked during rename, retrying: {filepath}")
            time.sleep(1)
        except Exception as e:
            print(f"❌ Rename error: {e}")
            break

    print(f"❌ Failed to rename after retries: {filepath}")
    return filepath
