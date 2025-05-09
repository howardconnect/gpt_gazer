from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import os

# ✅ Optional: explicitly set the path to the Tesseract binary
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def ocr_image_from_pdf(filepath):
    try:
        pages = convert_from_path(filepath, dpi=300)  # ✅ Higher DPI = better OCR accuracy
        text = ""
        print(f"🧠 Running OCR on: {filepath}")
        for i, page in enumerate(pages[:3]):  # ✅ Limit to first 3 pages
            page_text = pytesseract.image_to_string(page, config="--psm 3")
            text += f"\n--- Page {i+1} ---\n{page_text}"
        return text.strip()
    except Exception as e:
        print(f"❌ OCR error: {e}")
        return ""
