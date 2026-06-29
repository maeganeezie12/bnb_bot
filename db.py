import sqlite3
import json
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent / "trophies.db"


def _conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    with _conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS entries (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id      TEXT    NOT NULL,
                username     TEXT    NOT NULL,
                trophies     INTEGER NOT NULL,
                submitted_at DATETIME NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS summaries (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                posted_at     DATETIME NOT NULL,
                snapshot_json TEXT     NOT NULL
            )
        """)


def add_entry(user_id: str, username: str, trophies: int, submitted_at: datetime | None = None):
    ts = (submitted_at or datetime.now(timezone.utc)).isoformat()
    with _conn() as conn:
        conn.execute(
            "INSERT INTO entries (user_id, username, trophies, submitted_at) VALUES (?, ?, ?, ?)",
            (user_id, username, trophies, ts),
        )


def find_user_id_by_name(name: str) -> str | None:
    """Return the existing user_id for a given display name, or None if not found."""
    with _conn() as conn:
        row = conn.execute(
            "SELECT user_id FROM entries WHERE LOWER(username) = LOWER(?) LIMIT 1",
            (name,),
        ).fetchone()
    return row[0] if row else None


def get_current_standings():
    """Latest submission per user, sorted by trophies descending."""
    with _conn() as conn:
        rows = conn.execute("""
            SELECT user_id, username, trophies, submitted_at
            FROM entries
            WHERE id IN (
                SELECT MAX(id) FROM entries GROUP BY user_id
            )
            ORDER BY trophies DESC
        """).fetchall()
    return rows  # [(user_id, username, trophies, submitted_at)]


def get_user_history(user_id: str):
    with _conn() as conn:
        rows = conn.execute(
            "SELECT trophies, submitted_at FROM entries WHERE user_id = ? ORDER BY submitted_at",
            (user_id,),
        ).fetchall()
    return rows  # [(trophies, submitted_at)]


def save_summary(snapshot: list):
    with _conn() as conn:
        conn.execute(
            "INSERT INTO summaries (posted_at, snapshot_json) VALUES (?, ?)",
            (datetime.now(timezone.utc).isoformat(), json.dumps(snapshot)),
        )


def get_recent_summaries(limit: int = 4):
    """Returns up to `limit` most recent summaries, oldest first."""
    with _conn() as conn:
        rows = conn.execute(
            "SELECT posted_at, snapshot_json FROM summaries ORDER BY posted_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return list(reversed(rows))
