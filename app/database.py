import sqlite3
from contextlib import closing

from app.config import DB_PATH


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    with closing(get_connection()) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                short_code TEXT NOT NULL UNIQUE,
                original_url TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT,
                click_count INTEGER NOT NULL DEFAULT 0,
                is_active INTEGER NOT NULL DEFAULT 1
            )
            """
        )

        columns = [row[1] for row in connection.execute("PRAGMA table_info(links)").fetchall()]
        if "updated_at" not in columns:
            connection.execute("ALTER TABLE links ADD COLUMN updated_at TEXT")
        if "is_active" not in columns:
            connection.execute("ALTER TABLE links ADD COLUMN is_active INTEGER NOT NULL DEFAULT 1")

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS link_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                short_code TEXT NOT NULL,
                accessed_at TEXT NOT NULL,
                FOREIGN KEY(short_code) REFERENCES links(short_code)
            )
            """
        )

        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_links_is_active ON links(short_code, is_active)"
        )
        connection.commit()
