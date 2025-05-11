import openai
import os
import json
from dotenv import load_dotenv
from logger import logger  # ✅ use shared logger

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def summarize_with_gpt(text_chunk):
    prompt = f"""
You are a file assistant. Based on the document content, provide:
- A suggested filename (e.g., Verizon_Receipt.pdf)
- A readable/common name/title
- A 1–2 sentence summary
- A keyword
- A suggested category (Finance, Insurance, Medical, etc.)

Content:
\"\"\"
{text_chunk[:3000]}
\"\"\"
Respond in JSON format with keys: filename, common_name, summary, keyword, category.
"""

    try:
        logger.info("🔎 Sending chunk to GPT for summarization...")
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful file summarization assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4
        )
        result = json.loads(response["choices"][0]["message"]["content"])
        logger.info(f"✅ GPT summary received: {result.get('filename', 'no-filename')} | {result.get('category', 'uncategorized')}")
        return result
    except Exception as e:
        logger.exception(f"❌ GPT request failed: {e}")
        return {
            "filename": "Untitled_File.txt",
            "common_name": "Untitled",
            "summary": "No summary provided.",
            "keyword": "Unknown",
            "category": "Unsorted"
        }
