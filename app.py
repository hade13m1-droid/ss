from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from flask import Flask, jsonify, request, send_file, send_from_directory

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "portfolio.db"
UPLOADS_DIR = BASE_DIR / "uploads"
INDEX_PATH = BASE_DIR / "index.html"
ADMIN_PATH = BASE_DIR / "admin.html"

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024

DEFAULT_CONFIG = {
    "name": "hade133",
    "description": "Im boring",
    "aboutLines": [
        "Still I breathe like I’m okay,",
        "Same damn smile, different day.",
        "Heart in pieces, walk it straight,",
        "World keeps spinning... I imitate.",
    ],
    "place": "Earth",
    "views": 8,
    "availability": "ONLINE",
    "pfp": "/uploads/default-pfp.svg",
    "avatarDecoration": "",
    "video": "",
    "music": "",
    "musicTitle": "im tired",
    "musicCover": "",
    "accentColor": "#ffffff",
    "cardOpacity": 0.75,
    "weatherCity": "Hamah",
    "weatherTemp": "12°C",
    "weatherCondition": "Clear",
    "links": [
        {"label": "Guns.lol", "url": "https://guns.lol/_hade_"},
        {"label": "GitHub", "url": "https://github.com/hade14dev-prog"},
    ],
    "projects": [
        {"title": "Aesthetic Profile", "description": "Dark cinematic profile card.", "image": ""}
    ],
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_bootstrap_files() -> None:
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    default_pfp = UPLOADS_DIR / "default-pfp.svg"
    if not default_pfp.exists():
        default_pfp.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="320" height="320" viewBox="0 0 320 320"><rect width="320" height="320" rx="160" fill="#171B35"/><circle cx="160" cy="160" r="120" fill="#8E77FF"/><text x="160" y="190" text-anchor="middle" font-size="96" font-family="Arial" fill="#fff" font-weight="700">H</text></svg>',
            encoding="utf-8",
        )


def init_db() -> None:
    with db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
              key TEXT PRIMARY KEY,
              value TEXT NOT NULL,
              updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS contact_messages (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              name TEXT NOT NULL,
              email TEXT NOT NULL,
              message TEXT NOT NULL,
              created_at TEXT NOT NULL
            )
            """
        )
        row = conn.execute("SELECT value FROM settings WHERE key='config'").fetchone()
        if row is None:
            conn.execute(
                "INSERT INTO settings (key, value, updated_at) VALUES ('config', ?, ?)",
                (json.dumps(DEFAULT_CONFIG), now_iso()),
            )


def get_config() -> dict:
    with db() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key='config'").fetchone()
    if row is None:
        return dict(DEFAULT_CONFIG)
    try:
        raw = json.loads(row["value"])
        if not isinstance(raw, dict):
            return dict(DEFAULT_CONFIG)
        merged = {**DEFAULT_CONFIG, **raw}
        if not isinstance(merged.get("aboutLines"), list):
            merged["aboutLines"] = DEFAULT_CONFIG["aboutLines"]
        return merged
    except json.JSONDecodeError:
        return dict(DEFAULT_CONFIG)


def save_config(payload: dict) -> None:
    merged = {**DEFAULT_CONFIG, **payload}
    with db() as conn:
        conn.execute(
            """
            INSERT INTO settings (key, value, updated_at)
            VALUES ('config', ?, ?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
            """,
            (json.dumps(merged), now_iso()),
        )


@app.get("/")
def home():
    return send_file(INDEX_PATH)


@app.get("/admin")
def admin():
    return send_file(ADMIN_PATH)


@app.get("/uploads/<path:filename>")
def uploads(filename: str):
    return send_from_directory(UPLOADS_DIR, filename)


@app.get("/api/config")
def api_get_config():
    return jsonify(get_config())


@app.post("/api/config")
def api_save_config():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Invalid JSON payload"}), 400
    save_config(payload)
    return jsonify({"ok": True})


@app.post("/api/upload")
def api_upload():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename is None or file.filename.strip() == "":
        return jsonify({"error": "Empty filename"}), 400

    ext = Path(file.filename).suffix.lower()
    allowed = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".mp4", ".mp3"}
    if ext not in allowed:
        return jsonify({"error": "Unsupported file type"}), 400

    filename = f"{uuid4().hex}{ext}"
    path = UPLOADS_DIR / filename
    file.save(path)
    return jsonify({"ok": True, "url": f"/uploads/{filename}"})


@app.post("/api/contact")
def api_contact():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Invalid JSON payload"}), 400

    name = str(payload.get("name", "")).strip()
    email = str(payload.get("email", "")).strip()
    message = str(payload.get("message", "")).strip()

    if len(name) < 2 or len(email) < 5 or len(message) < 4:
        return jsonify({"error": "Please provide valid name/email/message"}), 400

    with db() as conn:
        conn.execute(
            "INSERT INTO contact_messages (name, email, message, created_at) VALUES (?, ?, ?, ?)",
            (name, email, message, now_iso()),
        )

    return jsonify({"ok": True})


@app.get("/api/messages")
def api_messages():
    with db() as conn:
        rows = conn.execute(
            "SELECT id, name, email, message, created_at FROM contact_messages ORDER BY id DESC LIMIT 100"
        ).fetchall()
    return jsonify([dict(row) for row in rows])


ensure_bootstrap_files()
init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
