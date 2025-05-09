import os
import fitz  # PyMuPDF
from utils.ocr import ocr_image_from_pdf
from docx import Document
from pptx import Presentation
from bs4 import BeautifulSoup  # For HTML parsing
from email import policy
from email.parser import BytesParser

def extract_text_from_file(filepath):
    ext = os.path.splitext(filepath)[1].lower()

    if ext in [".txt", ".md", ".log"]:
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception as e:
            print(f"❌ Failed to read plain text/markdown: {e}")
            return ""

    elif ext == ".html":
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                soup = BeautifulSoup(f, "html.parser")
                return soup.get_text(separator="\n")
        except Exception as e:
            print(f"❌ Failed to read HTML: {e}")
            return ""

    elif ext == ".eml":
        try:
            with open(filepath, "rb") as f:
                msg = BytesParser(policy=policy.default).parse(f)
                body = msg.get_body(preferencelist=('plain'))
                return "\n".join([
                    f"From: {msg['From']}",
                    f"To: {msg['To']}",
                    f"Subject: {msg['Subject']}",
                    f"Date: {msg['Date']}",
                    f"\n{body.get_content() if body else '(No plain text body)'}"
                ])
        except Exception as e:
            print(f"❌ Failed to read EML: {e}")
            return ""

    elif ext == ".pdf":
        try:
            doc = fitz.open(filepath)
            text = "\n".join(page.get_text() for page in doc)
            if text.strip():
                return text
            return ocr_image_from_pdf(filepath)
        except Exception as e:
            print(f"❌ PDF extraction failed, falling back to OCR: {e}")
            return ocr_image_from_pdf(filepath)

    elif ext == ".docx":
        try:
            doc = Document(filepath)
            return "\n".join(p.text for p in doc.paragraphs)
        except Exception as e:
            print(f"❌ Failed to read DOCX: {e}")
            return ""

    elif ext == ".pptx":
        try:
            prs = Presentation(filepath)
            return "\n".join(
                shape.text for slide in prs.slides for shape in slide.shapes if hasattr(shape, "text")
            )
        except Exception as e:
            print(f"❌ Failed to read PPTX: {e}")
            return ""

    elif ext in [".json", ".xml", ".rtf"]:
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception as e:
            print(f"❌ Failed to read structured text: {e}")
            return ""

    else:
        print(f"⚠️ Unsupported file type: {ext}")
        return ""
