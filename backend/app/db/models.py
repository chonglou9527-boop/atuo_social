from datetime import datetime
from enum import Enum

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PostStatus(str, Enum):
    draft = "draft"
    queued = "queued"
    publishing = "publishing"
    published = "published"
    failed = "failed"


class TargetStatus(str, Enum):
    pending = "pending"
    scheduled = "scheduled"
    publishing = "publishing"
    published = "published"
    failed = "failed"


class Account(Base):
    __tablename__ = "account"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    platform: Mapped[str] = mapped_column(String(32), index=True)
    name: Mapped[str] = mapped_column(String(128))
    auth_type: Mapped[str] = mapped_column(String(16))  # "api" | "cookie"
    credentials_encrypted: Mapped[bytes] = mapped_column()
    status: Mapped[str] = mapped_column(String(16), default="active")
    last_check_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Post(Base):
    __tablename__ = "post"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(256), default="")
    body_md: Mapped[str] = mapped_column(Text, default="")
    cover_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default=PostStatus.draft.value)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    assets: Mapped[list["PostAsset"]] = relationship(back_populates="post", cascade="all, delete-orphan")
    targets: Mapped[list["PostTarget"]] = relationship(back_populates="post", cascade="all, delete-orphan")


class PostAsset(Base):
    __tablename__ = "post_asset"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("post.id", ondelete="CASCADE"))
    url: Mapped[str] = mapped_column(String(512))
    type: Mapped[str] = mapped_column(String(16), default="image")
    order: Mapped[int] = mapped_column(Integer, default=0)

    post: Mapped[Post] = relationship(back_populates="assets")


class PostTarget(Base):
    __tablename__ = "post_target"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("post.id", ondelete="CASCADE"))
    account_id: Mapped[int] = mapped_column(ForeignKey("account.id", ondelete="CASCADE"))
    platform: Mapped[str] = mapped_column(String(32), index=True)
    payload_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    remote_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    remote_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default=TargetStatus.pending.value)
    error_msg: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)

    post: Mapped[Post] = relationship(back_populates="targets")


class MetricSnapshot(Base):
    __tablename__ = "metric_snapshot"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    post_target_id: Mapped[int] = mapped_column(ForeignKey("post_target.id", ondelete="CASCADE"))
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    views: Mapped[int] = mapped_column(Integer, default=0)
    likes: Mapped[int] = mapped_column(Integer, default=0)
    comments: Mapped[int] = mapped_column(Integer, default=0)
    shares: Mapped[int] = mapped_column(Integer, default=0)
    raw_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class LLMConfig(Base):
    __tablename__ = "llm_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    provider: Mapped[str] = mapped_column(String(32))
    model: Mapped[str] = mapped_column(String(64))
    api_key_encrypted: Mapped[bytes] = mapped_column()
    base_url: Mapped[str | None] = mapped_column(String(256), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# ---------- Inbox / content ingestion ----------


class InboxSourceType(str, Enum):
    rss = "rss"
    twitter_list = "twitter_list"
    web = "web"


class InboxItemStatus(str, Enum):
    new = "new"
    read = "read"
    archived = "archived"
    used = "used"  # already turned into a Post


class InboxSource(Base):
    __tablename__ = "inbox_source"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    type: Mapped[str] = mapped_column(String(32), index=True)
    config_json: Mapped[dict] = mapped_column(JSON, default=dict)
    fetch_interval_min: Mapped[int] = mapped_column(Integer, default=30)
    enabled: Mapped[bool] = mapped_column(default=True)
    last_fetched_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class InboxItem(Base):
    __tablename__ = "inbox_item"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("inbox_source.id", ondelete="CASCADE"), index=True)
    external_id: Mapped[str] = mapped_column(String(256), index=True)  # dedup key per source
    title: Mapped[str] = mapped_column(String(512), default="")
    content: Mapped[str] = mapped_column(Text, default="")
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    author: Mapped[str | None] = mapped_column(String(128), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    tags_json: Mapped[list] = mapped_column(JSON, default=list)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    status: Mapped[str] = mapped_column(String(16), default=InboxItemStatus.new.value, index=True)
    raw_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    rewritten_post_id: Mapped[int | None] = mapped_column(ForeignKey("post.id", ondelete="SET NULL"), nullable=True)


class RewriteRule(Base):
    """When an inbox item matches keyword/tag/source filters, auto-trigger AI rewrite into a draft Post."""

    __tablename__ = "rewrite_rule"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    enabled: Mapped[bool] = mapped_column(default=True)
    # Match conditions (all AND'd; empty = ignored)
    source_ids_json: Mapped[list] = mapped_column(JSON, default=list)  # [int]
    keywords_json: Mapped[list] = mapped_column(JSON, default=list)  # [str], OR-match against title+content
    tags_json: Mapped[list] = mapped_column(JSON, default=list)  # [str], OR-match against item tags
    # Rewrite settings
    style_prompt: Mapped[str] = mapped_column(Text, default="")
    target_platforms_json: Mapped[list] = mapped_column(JSON, default=list)  # [str] hint for AI
    llm_config_id: Mapped[int | None] = mapped_column(ForeignKey("llm_config.id", ondelete="SET NULL"), nullable=True)
    auto_publish: Mapped[bool] = mapped_column(default=False)  # if true, also queue Post to targets
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
