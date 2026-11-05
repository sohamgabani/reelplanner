"""SQLite storage for pages and reel ideas."""

import os
import sqlite3
from pathlib import Path

STATUSES = ("idea", "scripted", "filmed", "posted")

SCHEMA = """
CREATE TABLE IF NOT EXISTS pages (
    id INTEGER PRIMARY KEY,
    handle TEXT NOT NULL UNIQUE,
    niche TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS reels (
    id INTEGER PRIMARY KEY,
    page_id INTEGER NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    hook TEXT NOT NULL DEFAULT '',
    caption TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'idea',
    post_date TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def default_path() -> Path:
    env = os.environ.get("REELPLANNER_DB")
    if env:
        return Path(env)
    return Path.home() / ".reelplanner" / "reels.db"


def connect(path: Path | str | None = None) -> sqlite3.Connection:
    path = Path(path) if path else default_path()
    if str(path) != ":memory:":
        path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    return conn


def add_page(conn, handle: str, niche: str = "") -> int:
    handle = handle.lstrip("@").strip()
    if not handle:
        raise ValueError("handle cannot be empty")
    cur = conn.execute("INSERT INTO pages (handle, niche) VALUES (?, ?)", (handle, niche))
    conn.commit()
    return cur.lastrowid


def list_pages(conn):
    return conn.execute("SELECT * FROM pages ORDER BY handle").fetchall()


def get_page(conn, handle: str):
    row = conn.execute("SELECT * FROM pages WHERE handle = ?", (handle.lstrip("@"),)).fetchone()
    if row is None:
        raise LookupError(f"no page called @{handle.lstrip('@')}")
    return row


def add_reel(conn, handle: str, title: str, hook: str = "", caption: str = "") -> int:
    page = get_page(conn, handle)
    cur = conn.execute(
        "INSERT INTO reels (page_id, title, hook, caption) VALUES (?, ?, ?, ?)",
        (page["id"], title, hook, caption),
    )
    conn.commit()
    return cur.lastrowid


def list_reels(conn, handle: str | None = None, status: str | None = None):
    sql = "SELECT r.*, p.handle FROM reels r JOIN pages p ON p.id = r.page_id WHERE 1=1"
    args = []
    if handle:
        sql += " AND p.handle = ?"
        args.append(handle.lstrip("@"))
    if status:
        sql += " AND r.status = ?"
        args.append(status)
    sql += " ORDER BY COALESCE(r.post_date, '9999'), r.id"
    return conn.execute(sql, args).fetchall()


def get_reel(conn, reel_id: int):
    row = conn.execute(
        "SELECT r.*, p.handle FROM reels r JOIN pages p ON p.id = r.page_id WHERE r.id = ?",
        (reel_id,),
    ).fetchone()
    if row is None:
        raise LookupError(f"no reel with id {reel_id}")
    return row


def update_reel(conn, reel_id: int, **fields) -> None:
    allowed = {"title", "hook", "caption", "status", "post_date"}
    fields = {k: v for k, v in fields.items() if v is not None}
    bad = set(fields) - allowed
    if bad:
        raise ValueError(f"cannot update: {', '.join(sorted(bad))}")
    if "status" in fields and fields["status"] not in STATUSES:
        raise ValueError(f"status must be one of: {', '.join(STATUSES)}")
    if not fields:
        return
    get_reel(conn, reel_id)
    sets = ", ".join(f"{k} = ?" for k in fields)
    conn.execute(f"UPDATE reels SET {sets} WHERE id = ?", (*fields.values(), reel_id))
    conn.commit()


def delete_reel(conn, reel_id: int) -> None:
    get_reel(conn, reel_id)
    conn.execute("DELETE FROM reels WHERE id = ?", (reel_id,))
    conn.commit()
