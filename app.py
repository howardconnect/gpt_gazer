from flask import Flask, render_template, send_file
import sqlite3
import os
from dotenv import load_dotenv

app = Flask(__name__)
DB_PATH = "database.db"

load_dotenv()  # ✅ ensure .env is loaded for WATCH_FOLDER

@app.route("/open/<filename>")
def open_file(filename):
    path = os.path.join(os.getenv("WATCH_FOLDER"), filename)
    return send_file(path, as_attachment=False)

def fetch_documents():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    docs = conn.execute("SELECT * FROM documents WHERE archived = 0 ORDER BY date_added DESC").fetchall()
    conn.close()
    return docs

@app.route("/")
def index():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    docs = conn.execute("SELECT * FROM documents WHERE archived = 0 ORDER BY date_added DESC").fetchall()
    conn.close()
    return render_template("index.html", documents=docs)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
