from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl, field_validator


class CreateLinkRequest(BaseModel):
    original_url: HttpUrl
    custom_alias: str | None = Field(default=None, min_length=3, max_length=32)

    @field_validator("custom_alias")
    @classmethod
    def validate_alias(cls, value: str | None) -> str | None:
        if value is None:
            return value
        cleaned = value.strip().lower()
        if not cleaned:
            raise ValueError("custom_alias cannot be empty")
        if any(ch not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for ch in cleaned):
            raise ValueError("custom_alias may only include letters, numbers, '-' and '_'")
        return cleaned


class UpdateLinkRequest(BaseModel):
    original_url: HttpUrl


class LinkResponse(BaseModel):
    original_url: str
    short_code: str
    short_url: str
    created_at: datetime
    click_count: int = 0


class LinkSummary(BaseModel):
    short_code: str
    original_url: str
    short_url: str
    created_at: datetime
    updated_at: datetime | None = None
    click_count: int = 0
    is_active: bool = True


class LinkDetail(LinkSummary):
    pass


class LinkListResponse(BaseModel):
    items: list[LinkSummary]
    total: int
    limit: int
    offset: int


class LinkDeleteResponse(BaseModel):
    short_code: str
    status: str
    message: str


class LinkAnalytics(BaseModel):
    short_code: str
    original_url: str
    created_at: datetime
    updated_at: datetime | None = None
    click_count: int
    is_active: bool = True
