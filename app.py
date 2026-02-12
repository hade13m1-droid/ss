from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template, request

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "portfolio.db"

app = Flask(__name__)

DEFAULT_CONFIG: dict[str, Any] = {
    "name": "Hade",
    "description": "Cinematic web creator building immersive interfaces and premium digital vibes.",
    "place": "Morocco",
    "availability": "AVAILABLE NOW",
    "pfp": "/static/assets/pfp.svg",
    "video": "",
    "music": "",
    "accentColor": "#8e77ff",
    "links": [
        {"label": "Instagram", "url": "#"},
        {"label": "GitHub", "url": "#"},
        {"label": "TikTok", "url": "#"},
    ],
    "skills": ["UI/UX", "Motion", "Frontend", "Branding", "Creative Coding"],
    "projects": [
        {
            "title": "Cinematic Identity Landing",
            "description": "Dark visual-first personal page with premium interactions.",
        },
        {
            "title": "Creator Profile System",
            "description": "Customizable social-first portfolio with backend-powered content.",
        },
    ],
}


def get_db() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    with get_db() as conn:
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
        row = conn.execute("SELECT value FROM settings WHERE key = 'config'").fetchone()
        if row is None:
            conn.execute(
                "INSERT INTO settings (key, value, updated_at) VALUES (?, ?, ?)",
                ("config", json.dumps(DEFAULT_CONFIG), now_iso()),
            )


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_config() -> dict[str, Any]:
    with get_db() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key='config'").fetchone()
    if row is None:
        return DEFAULT_CONFIG.copy()

    try:
        stored = json.loads(row["value"])
        if not isinstance(stored, dict):
            return DEFAULT_CONFIG.copy()
        merged = {**DEFAULT_CONFIG, **stored}
        return merged
    except json.JSONDecodeError:
        return DEFAULT_CONFIG.copy()


def save_config(data: dict[str, Any]) -> None:
    merged = {**DEFAULT_CONFIG, **data}
    payload = json.dumps(merged)
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO settings (key, value, updated_at)
            VALUES ('config', ?, ?)
            ON CONFLICT(key)
            DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
            """,
            (payload, now_iso()),
        )


@app.get("/")
def home() -> str:
    return render_template("index.html")


@app.get("/admin")
def admin() -> str:
    return render_template("admin.html")


@app.get("/api/config")
def api_get_config():
    return jsonify(load_config())


@app.post("/api/config")
def api_save_config():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Invalid JSON payload."}), 400

    save_config(payload)
    return jsonify({"ok": True})


@app.post("/api/contact")
def api_contact():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Invalid JSON payload."}), 400

    name = str(payload.get("name", "")).strip()
    email = str(payload.get("email", "")).strip()
    message = str(payload.get("message", "")).strip()

    if len(name) < 2 or len(email) < 5 or len(message) < 4:
        return jsonify({"error": "Please fill all fields with valid values."}), 400

    with get_db() as conn:
        conn.execute(
            "INSERT INTO contact_messages (name, email, message, created_at) VALUES (?, ?, ?, ?)",
            (name, email, message, now_iso()),
        )

    return jsonify({"ok": True, "message": "Message sent successfully."})


@app.get("/api/messages")
def api_messages():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, name, email, message, created_at FROM contact_messages ORDER BY id DESC LIMIT 100"
        ).fetchall()

    messages = [dict(row) for row in rows]
    return jsonify(messages)


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
