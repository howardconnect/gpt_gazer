from flask import Flask, render_template, send_file
import sqlite3
import os
from dotenv import load_dotenv
from flask import request, redirect
from datetime import datetime


app = Flask(__name__)
DB_PATH = "database.db"

load_dotenv()  # ✅ ensure .env is loaded for WATCH_FOLDER

WATCH_FOLDER = os.getenv("WATCH_FOLDER")

@app.route("/conflicts")
def conflicts():
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    rows = cur.execute("SELECT * FROM conflicts WHERE status = 'pending' ORDER BY date_added DESC").fetchall()
    conn.close()
    return render_template("conflicts.html", conflicts=rows)

@app.route("/api/documents")
def api_documents():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    docs = conn.execute("SELECT * FROM documents ORDER BY date_added DESC").fetchall()
    conn.close()
    return [dict(doc) for doc in docs]

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


@app.route("/resolve_conflict", methods=["POST"])
def resolve_conflict():
    data = request.form
    conflict_id = data.get("conflict_id")
    action = data.get("action")  # keep_old, replace, keep_both

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT * FROM conflicts WHERE id = ?", (conflict_id,))
    conflict = cur.fetchone()

    if action == "keep_old":
        os.remove(os.path.join(WATCH_FOLDER, conflict["new_filename"]))
        cur.execute("UPDATE conflicts SET status = 'resolved', action_taken = 'keep_old' WHERE id = ?", (conflict_id,))

    elif action == "replace":
        cur.execute("""
            UPDATE documents SET
                summary = ?, common_name = ?, keyword = ?, category = ?,
                date_added = ?
            WHERE filename = ?
        """, (
            conflict["new_summary"],  # replace with new
            conflict["new_filename"].replace(".pdf", ""),  # optional common_name logic
            "Replaced",  # or use GPT keyword/category if available
            "Updated",
            datetime.now().isoformat(),
            conflict["existing_filename"]
        ))
        os.remove(os.path.join(WATCH_FOLDER, conflict["new_filename"]))
        cur.execute("UPDATE conflicts SET status = 'resolved', action_taken = 'replace' WHERE id = ?", (conflict_id,))

    elif action == "keep_both":
        new_name = f"Duplicate_{datetime.now().strftime('%Y%m%d%H%M%S')}_{conflict['new_filename']}"
        os.rename(
            os.path.join(WATCH_FOLDER, conflict["new_filename"]),
            os.path.join(WATCH_FOLDER, new_name)
        )
        cur.execute("UPDATE conflicts SET status = 'resolved', action_taken = 'keep_both' WHERE id = ?", (conflict_id,))

    conn.commit()
    conn.close()
    return redirect("/conflicts")
