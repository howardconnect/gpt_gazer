import openai
import os
from dotenv import load_dotenv

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

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful file summarization assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.4
    )

    import json
    return json.loads(response["choices"][0]["message"]["content"])

