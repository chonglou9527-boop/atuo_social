"""RSS / Atom fetcher.

Config keys:
    url (required)
    user_agent (optional)
"""
from __future__ import annotations

import asyncio
from datetime import datetime
from email.utils import parsedate_to_datetime

import httpx

from app.inbox.base import FetchedItem, InboxFetcher

try:
    import feedparser
except ImportError:  # pragma: no cover - optional until installed
    feedparser = None  # type: ignore[assignment]


def _parse_date(entry) -> datetime | None:
    for k in ("published", "updated", "created"):
        v = entry.get(k)
        if not v:
            continue
        try:
            return parsedate_to_datetime(v)
        except (TypeError, ValueError):
            continue
    if entry.get("published_parsed"):
        try:
            return datetime(*entry.published_parsed[:6])
        except (TypeError, ValueError):
            return None
    return None


def _extract_image(entry) -> str | None:
    for media in entry.get("media_content") or []:
        if media.get("url"):
            return media["url"]
    for enc in entry.get("enclosures") or []:
        if str(enc.get("type", "")).startswith("image/"):
            return enc.get("href") or enc.get("url")
    return None


class RSSFetcher(InboxFetcher):
    type_name = "rss"

    async def fetch(self) -> list[FetchedItem]:
        if feedparser is None:
            raise RuntimeError("feedparser not installed")
        url = self.config["url"]
        ua = self.config.get("user_agent", "atuo-social/0.1 (+rss)")
        async with httpx.AsyncClient(timeout=30, headers={"User-Agent": ua}, follow_redirects=True) as c:
            r = await c.get(url)
            r.raise_for_status()
            text = r.text

        parsed = await asyncio.to_thread(feedparser.parse, text)
        items: list[FetchedItem] = []
        for e in parsed.entries:
            ext_id = e.get("id") or e.get("guid") or e.get("link")
            if not ext_id:
                continue
            content = ""
            if e.get("content"):
                content = e.content[0].get("value", "")
            content = content or e.get("summary", "") or ""
            items.append(
                FetchedItem(
                    external_id=str(ext_id),
                    title=e.get("title", ""),
                    content=content,
                    summary=e.get("summary"),
                    url=e.get("link"),
                    author=e.get("author"),
                    image_url=_extract_image(e),
                    tags=[t.term for t in (e.get("tags") or []) if t.get("term")],
                    published_at=_parse_date(e),
                    raw={k: v for k, v in e.items() if isinstance(v, (str, int, float, list, dict, type(None)))},
                )
            )
        return items
