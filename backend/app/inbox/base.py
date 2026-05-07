from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class FetchedItem:
    external_id: str
    title: str = ""
    content: str = ""
    summary: str | None = None
    url: str | None = None
    author: str | None = None
    image_url: str | None = None
    tags: list[str] = field(default_factory=list)
    published_at: datetime | None = None
    raw: dict | None = None


class InboxFetcher(ABC):
    type_name: str = ""

    def __init__(self, config: dict):
        self.config = config

    @abstractmethod
    async def fetch(self) -> list[FetchedItem]: ...
