import secrets
import sqlite3
import string
from datetime import datetime, timezone
from urllib.parse import urlsplit

from app.database import get_connection

CHARSET = string.ascii_letters + string.digits


def generate_short_code(length: int = 7) -> str:
    return "".join(secrets.choice(CHARSET) for _ in range(length))


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_url(value: str) -> str:
    if not value:
        raise ValueError("Destination URL is required")

    normalized = value.strip()
    parsed = urlsplit(normalized)

    if parsed.scheme.lower() not in {"http", "https"}:
        raise ValueError("Destination URL must use http or https")
    if not parsed.netloc:
        raise ValueError("Destination URL must include a valid hostname")

    if parsed.path in {"", "/"} and not parsed.query and not parsed.fragment:
        return f"{parsed.scheme.lower()}://{parsed.netloc}"

    return normalized


def create_link(original_url: str, custom_alias: str | None = None) -> dict:
    original_url = normalize_url(original_url)

    if custom_alias:
        short_code = custom_alias.strip()
    else:
        short_code = generate_short_code()

    now = _utc_now()

    for _ in range(10):
        with get_connection() as connection:
            try:
                connection.execute(
                    "INSERT INTO links (short_code, original_url, created_at, updated_at, click_count, is_active) VALUES (?, ?, ?, ?, 0, 1)",
                    (short_code, original_url, now, now),
                )
                connection.commit()
                return {
                    "short_code": short_code,
                    "original_url": original_url,
                    "created_at": now,
                    "updated_at": now,
                    "click_count": 0,
                    "is_active": True,
                }
            except sqlite3.IntegrityError:
                connection.rollback()
                if custom_alias:
                    raise ValueError(f"Alias '{custom_alias}' is already in use and cannot be reused after deactivation") from None
                short_code = generate_short_code()

    raise ValueError("Unable to generate a unique short code")


def list_links(limit: int = 50, offset: int = 0) -> tuple[list[dict], int]:
    if limit < 1:
        limit = 50
    if offset < 0:
        offset = 0

    with get_connection() as connection:
        total = connection.execute("SELECT COUNT(*) AS total FROM links").fetchone()["total"]
        rows = connection.execute(
            """
            SELECT short_code, original_url, created_at, updated_at, click_count, is_active
            FROM links
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        ).fetchall()

    items = [
        {
            "short_code": row["short_code"],
            "original_url": row["original_url"],
            "short_url": row["short_code"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "click_count": row["click_count"],
            "is_active": bool(row["is_active"]),
        }
        for row in rows
    ]
    return items, total


def get_link_details(short_code: str) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT short_code, original_url, created_at, updated_at, click_count, is_active
            FROM links WHERE short_code = ?
            """,
            (short_code,),
        ).fetchone()
        if not row:
            return None

        return {
            "short_code": row["short_code"],
            "original_url": row["original_url"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "click_count": row["click_count"],
            "is_active": bool(row["is_active"]),
        }


def update_link_destination(short_code: str, new_original_url: str) -> dict | None:
    new_original_url = normalize_url(new_original_url)
    now = _utc_now()
    with get_connection() as connection:
        row = connection.execute(
            "SELECT short_code, original_url, created_at, updated_at, click_count, is_active FROM links WHERE short_code = ?",
            (short_code,),
        ).fetchone()
        if not row:
            return None

        connection.execute(
            "UPDATE links SET original_url = ?, updated_at = ? WHERE short_code = ?",
            (new_original_url, now, short_code),
        )
        connection.commit()

        return {
            "short_code": row["short_code"],
            "original_url": new_original_url,
            "created_at": row["created_at"],
            "updated_at": now,
            "click_count": row["click_count"],
            "is_active": bool(row["is_active"]),
        }


def disable_link(short_code: str) -> dict | None:
    now = _utc_now()
    with get_connection() as connection:
        row = connection.execute(
            "SELECT short_code, original_url, created_at, updated_at, click_count, is_active FROM links WHERE short_code = ?",
            (short_code,),
        ).fetchone()
        if not row:
            return None

        connection.execute(
            "UPDATE links SET is_active = 0, updated_at = ? WHERE short_code = ?",
            (now, short_code),
        )
        connection.commit()

        return {
            "short_code": row["short_code"],
            "original_url": row["original_url"],
            "created_at": row["created_at"],
            "updated_at": now,
            "click_count": row["click_count"],
            "is_active": False,
        }


def resolve_link(short_code: str) -> str | None:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT original_url FROM links WHERE short_code = ? AND is_active = 1",
            (short_code,),
        ).fetchone()
        if not row:
            return None

        original_url = normalize_url(row["original_url"])

        connection.execute(
            "UPDATE links SET click_count = click_count + 1 WHERE short_code = ?",
            (short_code,),
        )
        connection.execute(
            "INSERT INTO link_events (short_code, accessed_at) VALUES (?, ?)",
            (short_code, _utc_now()),
        )
        connection.commit()
        return original_url


def get_analytics(short_code: str) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT short_code, original_url, created_at, updated_at, click_count, is_active FROM links WHERE short_code = ?",
            (short_code,),
        ).fetchone()
        if not row:
            return None

        return {
            "short_code": row["short_code"],
            "original_url": row["original_url"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "click_count": row["click_count"],
            "is_active": bool(row["is_active"]),
        }
