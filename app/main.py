import os
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import get_admin_api_key, get_public_base_url
from app.database import init_db
from app.models import (
    CreateLinkRequest,
    LinkAnalytics,
    LinkDeleteResponse,
    LinkDetail,
    LinkListResponse,
    LinkResponse,
    UpdateLinkRequest,
)
from app.service import (
    create_link,
    disable_link,
    get_analytics,
    get_link_details,
    list_links,
    resolve_link,
    update_link_destination,
)

BASE_DIR = Path(__file__).resolve().parent.parent
app = FastAPI(title="AI URL Shortener", version="1.0.0")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

init_db()


def require_admin_key(x_admin_key: str | None = Header(default=None, alias="X-Admin-Key")) -> str:
    configured_key = get_admin_api_key()
    if configured_key is None:
        raise HTTPException(status_code=503, detail="Admin API key is not configured")
    if x_admin_key is None:
        raise HTTPException(status_code=401, detail="Missing admin API key")
    if x_admin_key != configured_key:
        raise HTTPException(status_code=403, detail="Invalid admin API key")
    return x_admin_key


@app.get("/", response_class=HTMLResponse)
def serve_frontend(request: Request):
    public_base_url = get_public_base_url(request)
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "request": request,
            "public_base_url": public_base_url,
            "custom_domain_warning": not public_base_url.startswith("http://127.0.0.1") and not public_base_url.startswith("http://localhost"),
        },
    )


@app.post("/api/v1/links", response_model=LinkResponse, status_code=201)
def create_short_link(payload: CreateLinkRequest, request: Request):
    original_url = str(payload.original_url)
    try:
        record = create_link(original_url, payload.custom_alias)
    except ValueError as exc:
        status_code = 409 if "already in use" in str(exc).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc

    base_url = get_public_base_url(request)
    return {
        "original_url": record["original_url"],
        "short_code": record["short_code"],
        "short_url": f"{base_url}/{record['short_code']}",
        "created_at": record["created_at"],
        "click_count": record["click_count"],
    }


@app.get("/api/v1/links", response_model=LinkListResponse)
def list_links_admin(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    _: str = Depends(require_admin_key),
):
    items, total = list_links(limit=limit, offset=offset)
    return {
        "items": [
            {
                "short_code": item["short_code"],
                "original_url": item["original_url"],
                "short_url": f"{get_public_base_url()}/{item['short_code']}",
                "created_at": item["created_at"],
                "updated_at": item.get("updated_at"),
                "click_count": item["click_count"],
                "is_active": item["is_active"],
            }
            for item in items
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@app.get("/api/v1/links/{short_code}", response_model=LinkDetail)
def get_link_detail(short_code: str, _: str = Depends(require_admin_key)):
    details = get_link_details(short_code)
    if details is None:
        raise HTTPException(status_code=404, detail="Short code not found")
    return {
        "short_code": details["short_code"],
        "original_url": details["original_url"],
        "short_url": f"{get_public_base_url()}/{details['short_code']}",
        "created_at": details["created_at"],
        "updated_at": details.get("updated_at"),
        "click_count": details["click_count"],
        "is_active": details["is_active"],
    }


@app.patch("/api/v1/links/{short_code}", response_model=LinkDetail)
def update_link(short_code: str, payload: UpdateLinkRequest, _: str = Depends(require_admin_key)):
    try:
        updated = update_link_destination(short_code, str(payload.original_url))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if updated is None:
        raise HTTPException(status_code=404, detail="Short code not found")
    return {
        "short_code": updated["short_code"],
        "original_url": updated["original_url"],
        "short_url": f"{get_public_base_url()}/{updated['short_code']}",
        "created_at": updated["created_at"],
        "updated_at": updated.get("updated_at"),
        "click_count": updated["click_count"],
        "is_active": updated["is_active"],
    }


@app.delete("/api/v1/links/{short_code}", response_model=LinkDeleteResponse)
def delete_link(short_code: str, _: str = Depends(require_admin_key)):
    record = disable_link(short_code)
    if record is None:
        raise HTTPException(status_code=404, detail="Short code not found")
    return {
        "short_code": record["short_code"],
        "status": "disabled",
        "message": "The link has been disabled and no longer redirects.",
    }


@app.get("/{short_code}")
def redirect_short_link(short_code: str):
    try:
        original_url = resolve_link(short_code)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if original_url is None:
        raise HTTPException(status_code=404, detail="Short code not found or disabled")
    return RedirectResponse(url=original_url, status_code=307)


@app.get("/api/v1/links/{short_code}/analytics", response_model=LinkAnalytics)
def get_link_analytics(short_code: str):
    analytics = get_analytics(short_code)
    if analytics is None:
        raise HTTPException(status_code=404, detail="Short code not found")
    return analytics


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)
