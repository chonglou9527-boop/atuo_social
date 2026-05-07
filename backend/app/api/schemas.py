from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class _ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------- Accounts ----------


class AccountCreate(BaseModel):
    platform: str
    name: str
    auth_type: str = "api"  # "api" | "cookie"
    credentials: dict  # plaintext, will be encrypted


class AccountOut(_ORM):
    id: int
    platform: str
    name: str
    auth_type: str
    status: str
    last_check_at: datetime | None
    created_at: datetime


# ---------- Posts ----------


class PostAssetIn(BaseModel):
    url: str
    type: str = "image"
    order: int = 0


class PostAssetOut(_ORM):
    id: int
    url: str
    type: str
    order: int


class PostCreate(BaseModel):
    title: str = ""
    body_md: str = ""
    cover_url: str | None = None
    assets: list[PostAssetIn] = Field(default_factory=list)


class PostUpdate(BaseModel):
    title: str | None = None
    body_md: str | None = None
    cover_url: str | None = None
    assets: list[PostAssetIn] | None = None


class PostOut(_ORM):
    id: int
    title: str
    body_md: str
    cover_url: str | None
    status: str
    created_at: datetime
    updated_at: datetime
    assets: list[PostAssetOut] = Field(default_factory=list)


# ---------- Targets / publish ----------


class TargetCreate(BaseModel):
    account_id: int
    scheduled_at: datetime | None = None
    payload: dict | None = None


class TargetOut(_ORM):
    id: int
    post_id: int
    account_id: int
    platform: str
    scheduled_at: datetime | None
    published_at: datetime | None
    remote_id: str | None
    remote_url: str | None
    status: str
    error_msg: str | None
    retry_count: int


class PublishRequest(BaseModel):
    account_ids: list[int]
    scheduled_at: datetime | None = None  # None = publish now


# ---------- LLM config ----------


class LLMConfigCreate(BaseModel):
    provider: str
    model: str
    api_key: str
    base_url: str | None = None
    is_active: bool = False


class LLMConfigOut(_ORM):
    id: int
    provider: str
    model: str
    base_url: str | None
    is_active: bool
    created_at: datetime


# ---------- Inbox ----------


class InboxSourceCreate(BaseModel):
    name: str
    type: str  # "rss" | "twitter_list"
    config: dict
    fetch_interval_min: int = 30
    enabled: bool = True


class InboxSourceOut(_ORM):
    id: int
    name: str
    type: str
    config_json: dict
    fetch_interval_min: int
    enabled: bool
    last_fetched_at: datetime | None
    last_error: str | None
    created_at: datetime


class InboxItemOut(_ORM):
    id: int
    source_id: int
    external_id: str
    title: str
    content: str
    summary: str | None
    url: str | None
    author: str | None
    image_url: str | None
    tags_json: list[Any]
    published_at: datetime | None
    fetched_at: datetime
    status: str
    rewritten_post_id: int | None


# ---------- Rewrite rules ----------


class RewriteRuleCreate(BaseModel):
    name: str
    enabled: bool = True
    source_ids: list[int] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    style_prompt: str = ""
    target_platforms: list[str] = Field(default_factory=list)
    llm_config_id: int | None = None
    auto_publish: bool = False


class RewriteRuleOut(_ORM):
    id: int
    name: str
    enabled: bool
    source_ids_json: list[int]
    keywords_json: list[str]
    tags_json: list[str]
    style_prompt: str
    target_platforms_json: list[str]
    llm_config_id: int | None
    auto_publish: bool
    created_at: datetime


# ---------- AI ----------


class AIChatRequest(BaseModel):
    prompt: str
    system: str | None = None
    llm_config_id: int | None = None  # if None, uses active config


class AIChatResponse(BaseModel):
    text: str
