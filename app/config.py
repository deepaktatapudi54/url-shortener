import os
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "shortener.db"

DATA_DIR.mkdir(exist_ok=True)


def get_public_base_url(request=None) -> str:
    configured = os.getenv("PUBLIC_BASE_URL", "").strip()
    if configured:
        parsed = urlparse(configured)
        if parsed.scheme in {"http", "https"} and parsed.netloc:
            return configured.rstrip("/")
        return "http://127.0.0.1:8000"

    if request is not None:
        return str(request.base_url).rstrip("/")

    return "http://127.0.0.1:8000"


def get_admin_api_key() -> str | None:
    api_key = os.getenv("ADMIN_API_KEY", "").strip()
    return api_key or None
