from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.db.models import Account, Post, PostTarget


@dataclass
class AdaptedContent:
    title: str = ""
    body: str = ""
    images: list[str] = field(default_factory=list)
    extra: dict = field(default_factory=dict)


@dataclass
class PublishResult:
    remote_id: str
    remote_url: str | None = None
    raw: dict | None = None


@dataclass
class Metrics:
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    raw: dict | None = None


class PlatformAdapter(ABC):
    platform: str = ""

    def __init__(self, credentials: dict):
        self.credentials = credentials

    @abstractmethod
    async def publish(self, post: "Post", target: "PostTarget", content: AdaptedContent) -> PublishResult: ...

    @abstractmethod
    async def fetch_metrics(self, target: "PostTarget") -> Metrics: ...

    async def login_check(self, account: "Account") -> bool:
        return True

    def adapt_content(self, post: "Post") -> AdaptedContent:
        """Default 1:1 mapping; subclasses override to enforce platform limits (length, image count, tags)."""
        images = [a.url for a in sorted(post.assets, key=lambda a: a.order) if a.type == "image"]
        return AdaptedContent(title=post.title, body=post.body_md, images=images)
