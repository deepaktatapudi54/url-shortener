import os
import uuid

import pytest
from fastapi.testclient import TestClient

import app.config as config
import app.database as database
from app.main import app
from app.service import create_link, update_link_destination

client = TestClient(app)


@pytest.fixture(autouse=True)
def isolated_db(monkeypatch, tmp_path):
    db_path = tmp_path / "shortener.db"
    monkeypatch.setattr(database, "DB_PATH", str(db_path))
    monkeypatch.setattr(config, "DB_PATH", str(db_path))
    database.init_db()
    yield


def test_home_page_renders_ui():
    response = client.get("/")
    assert response.status_code == 200
    assert "URL Shortener" in response.text


def test_create_short_link_and_resolve_it():
    response = client.post(
        "/api/v1/links",
        json={"original_url": "https://example.com/very/long/path?query=1"},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["original_url"] == "https://example.com/very/long/path?query=1"
    assert payload["short_code"]
    assert payload["short_url"].startswith("http://testserver/")

    resolve_response = client.get(f"/{payload['short_code']}", allow_redirects=False)
    assert resolve_response.status_code == 307
    assert resolve_response.headers["location"] == "https://example.com/very/long/path?query=1"


def test_public_base_url_is_used_when_configured(monkeypatch):
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://deepak.com")
    alias = f"mail-{uuid.uuid4().hex[:8]}"

    response = client.post(
        "/api/v1/links",
        json={"original_url": "https://example.com/custom-domain", "custom_alias": alias},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["short_url"] == f"https://deepak.com/{alias}"
    assert payload["short_code"] == alias


def test_create_short_link_rejects_invalid_url():
    response = client.post(
        "/api/v1/links",
        json={"original_url": "not-a-valid-url"},
    )

    assert response.status_code == 422


def test_duplicate_alias_is_rejected():
    alias = f"unique-alias-{uuid.uuid4().hex[:8]}"
    payload = {"original_url": "https://example.com/duplicate", "custom_alias": alias}
    first_response = client.post("/api/v1/links", json=payload)
    assert first_response.status_code == 201

    second_response = client.post("/api/v1/links", json=payload)
    assert second_response.status_code == 409
    assert "already in use" in second_response.json()["detail"]


def test_analytics_endpoint_reports_clicks():
    response = client.post(
        "/api/v1/links",
        json={"original_url": "https://example.com/analytics"},
    )
    assert response.status_code == 201
    short_code = response.json()["short_code"]

    client.get(f"/{short_code}", allow_redirects=False)
    analytics = client.get(f"/api/v1/links/{short_code}/analytics")

    assert analytics.status_code == 200
    assert analytics.json()["short_code"] == short_code
    assert analytics.json()["click_count"] >= 1


def test_admin_can_list_details_update_and_disable_links(monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "admin-secret")
    alias = f"manage-{uuid.uuid4().hex[:8]}"

    create_response = client.post(
        "/api/v1/links",
        json={"original_url": "https://www.flipkart.com", "custom_alias": alias},
    )
    assert create_response.status_code == 201

    list_response = client.get(
        "/api/v1/links",
        headers={"X-Admin-Key": "admin-secret"},
    )
    assert list_response.status_code == 200
    assert any(item["short_code"] == alias for item in list_response.json()["items"])

    detail_response = client.get(
        f"/api/v1/links/{alias}",
        headers={"X-Admin-Key": "admin-secret"},
    )
    assert detail_response.status_code == 200
    assert detail_response.json()["short_code"] == alias

    update_response = client.patch(
        f"/api/v1/links/{alias}",
        json={"original_url": "https://www.amazon.in"},
        headers={"X-Admin-Key": "admin-secret"},
    )
    assert update_response.status_code == 200
    body = update_response.json()
    assert body["short_code"] == alias
    assert body["original_url"] == "https://www.amazon.in"

    redirect_response = client.get(f"/{alias}", allow_redirects=False)
    assert redirect_response.status_code == 307
    assert redirect_response.headers["location"] == "https://www.amazon.in"

    delete_response = client.delete(
        f"/api/v1/links/{alias}",
        headers={"X-Admin-Key": "admin-secret"},
    )
    assert delete_response.status_code == 200
    assert delete_response.json()["status"] == "disabled"

    disabled_redirect = client.get(f"/{alias}", allow_redirects=False)
    assert disabled_redirect.status_code == 404


def test_admin_api_requires_valid_key(monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "admin-secret")

    response = client.get(
        "/api/v1/links",
        headers={"X-Admin-Key": "wrong-key"},
    )
    assert response.status_code == 403

    unauthenticated = client.get("/api/v1/links")
    assert unauthenticated.status_code == 401


def test_link_management_rejects_invalid_destination(monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "admin-secret")
    alias = f"invalid-update-{uuid.uuid4().hex[:8]}"

    create_response = client.post(
        "/api/v1/links",
        json={"original_url": "https://example.com/keep-me", "custom_alias": alias},
    )
    assert create_response.status_code == 201

    update_response = client.patch(
        f"/api/v1/links/{alias}",
        json={"original_url": "not-a-valid-url"},
        headers={"X-Admin-Key": "admin-secret"},
    )
    assert update_response.status_code == 422


def test_rejects_unsupported_url_scheme():
    response = client.post(
        "/api/v1/links",
        json={"original_url": "ftp://example.com/file", "custom_alias": f"ftp-{uuid.uuid4().hex[:8]}"},
    )
    assert response.status_code in {400, 422}


def test_duplicate_alias_for_deactivated_link_is_rejected(monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "admin-secret")
    alias = f"deactivated-{uuid.uuid4().hex[:8]}"

    create_response = client.post(
        "/api/v1/links",
        json={"original_url": "https://example.com/first", "custom_alias": alias},
    )
    assert create_response.status_code == 201

    disable_response = client.delete(
        f"/api/v1/links/{alias}",
        headers={"X-Admin-Key": "admin-secret"},
    )
    assert disable_response.status_code == 200

    reuse_response = client.post(
        "/api/v1/links",
        json={"original_url": "https://example.com/second", "custom_alias": alias},
    )
    assert reuse_response.status_code == 409
    assert "already in use" in reuse_response.json()["detail"].lower()


def test_update_preserves_analytics_and_short_code(monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "admin-secret")
    alias = f"analytics-{uuid.uuid4().hex[:8]}"

    create_response = client.post(
        "/api/v1/links",
        json={"original_url": "https://example.com/first-target", "custom_alias": alias},
    )
    assert create_response.status_code == 201

    client.get(f"/{alias}", allow_redirects=False)

    update_response = client.patch(
        f"/api/v1/links/{alias}",
        json={"original_url": "https://example.com/second-target"},
        headers={"X-Admin-Key": "admin-secret"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["short_code"] == alias
    assert update_response.json()["original_url"] == "https://example.com/second-target"

    analytics = client.get(f"/api/v1/links/{alias}/analytics")
    assert analytics.status_code == 200
    assert analytics.json()["click_count"] == 1
    assert analytics.json()["short_code"] == alias


def test_deactivation_preserves_analytics_and_blocks_redirects(monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "admin-secret")
    alias = f"deactivate-{uuid.uuid4().hex[:8]}"

    create_response = client.post(
        "/api/v1/links",
        json={"original_url": "https://example.com/deactivate-me", "custom_alias": alias},
    )
    assert create_response.status_code == 201

    client.get(f"/{alias}", allow_redirects=False)

    delete_response = client.delete(
        f"/api/v1/links/{alias}",
        headers={"X-Admin-Key": "admin-secret"},
    )
    assert delete_response.status_code == 200

    blocked = client.get(f"/{alias}", allow_redirects=False)
    assert blocked.status_code == 404

    analytics = client.get(f"/api/v1/links/{alias}/analytics")
    assert analytics.status_code == 200
    assert analytics.json()["click_count"] == 1
    assert analytics.json()["is_active"] is False


def test_unknown_short_code_is_rejected():
    missing_redirect = client.get("/notreal-short-code", allow_redirects=False)
    assert missing_redirect.status_code == 404

    missing_analytics = client.get("/api/v1/links/notreal-short-code/analytics")
    assert missing_analytics.status_code == 404


def test_service_rejects_unsupported_scheme_directly():
    with pytest.raises(ValueError, match="http|https"):
        create_link("ftp://example.com/file", "ftp-direct")

    created = create_link("https://example.com/start", "scheme-test")
    assert created["short_code"] == "scheme-test"

    with pytest.raises(ValueError, match="http|https"):
        update_link_destination("scheme-test", "mailto:hello@example.com")
