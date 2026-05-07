"""Twitter/X adapter using tweepy v2.

Credentials dict expected:
    consumer_key, consumer_secret, access_token, access_token_secret  (OAuth1 user context)
    bearer_token (optional, used for read-only metrics fallback)

Posting tweets with media requires the v1.1 media/upload endpoint via tweepy.API + OAuth1.
Posting the tweet itself uses tweepy.Client (v2). Up to 4 images per tweet.
Body text is truncated to 280 chars (counting URLs as 23 per Twitter rules — simplified here).
"""
from __future__ import annotations

import asyncio
import os
import tempfile
from typing import TYPE_CHECKING
from urllib.parse import urlparse

import httpx
import tweepy

from app.platforms.base import AdaptedContent, Metrics, PlatformAdapter, PublishResult

if TYPE_CHECKING:
    from app.db.models import Post, PostTarget

MAX_IMAGES = 4
MAX_TEXT = 280


class TwitterAdapter(PlatformAdapter):
    platform = "twitter"

    def _client(self) -> tweepy.Client:
        c = self.credentials
        return tweepy.Client(
            consumer_key=c["consumer_key"],
            consumer_secret=c["consumer_secret"],
            access_token=c["access_token"],
            access_token_secret=c["access_token_secret"],
            bearer_token=c.get("bearer_token"),
        )

    def _api_v1(self) -> tweepy.API:
        c = self.credentials
        auth = tweepy.OAuth1UserHandler(
            c["consumer_key"], c["consumer_secret"], c["access_token"], c["access_token_secret"]
        )
        return tweepy.API(auth)

    def adapt_content(self, post: "Post") -> AdaptedContent:
        images = [a.url for a in sorted(post.assets, key=lambda a: a.order) if a.type == "image"][:MAX_IMAGES]
        text = (post.title + "\n\n" + post.body_md).strip() if post.title else post.body_md
        if len(text) > MAX_TEXT:
            text = text[: MAX_TEXT - 1].rstrip() + "…"
        return AdaptedContent(title="", body=text, images=images)

    async def _download(self, url: str) -> str:
        if not url.startswith("http"):
            return url  # already local path
        suffix = os.path.splitext(urlparse(url).path)[1] or ".jpg"
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.get(url)
            r.raise_for_status()
            fd, path = tempfile.mkstemp(suffix=suffix)
            with os.fdopen(fd, "wb") as f:
                f.write(r.content)
        return path

    def _upload_media_sync(self, paths: list[str]) -> list[str]:
        api = self._api_v1()
        ids: list[str] = []
        for p in paths:
            media = api.media_upload(filename=p)
            ids.append(media.media_id_string)
        return ids

    async def publish(self, post: "Post", target: "PostTarget", content: AdaptedContent) -> PublishResult:
        media_ids: list[str] = []
        local_paths: list[str] = []
        try:
            if content.images:
                local_paths = await asyncio.gather(*(self._download(u) for u in content.images))
                media_ids = await asyncio.to_thread(self._upload_media_sync, list(local_paths))

            client = self._client()
            resp = await asyncio.to_thread(
                client.create_tweet,
                text=content.body,
                media_ids=media_ids or None,
            )
            tweet_id = str(resp.data["id"])
            return PublishResult(
                remote_id=tweet_id,
                remote_url=f"https://x.com/i/status/{tweet_id}",
                raw=dict(resp.data) if hasattr(resp, "data") else None,
            )
        finally:
            for p in local_paths:
                if p and p.startswith(tempfile.gettempdir()):
                    try:
                        os.unlink(p)
                    except OSError:
                        pass

    async def fetch_metrics(self, target: "PostTarget") -> Metrics:
        if not target.remote_id:
            return Metrics()
        client = self._client()
        resp = await asyncio.to_thread(
            client.get_tweet,
            id=target.remote_id,
            tweet_fields=["public_metrics"],
        )
        pm = (resp.data and resp.data.public_metrics) or {}
        return Metrics(
            views=pm.get("impression_count", 0),
            likes=pm.get("like_count", 0),
            comments=pm.get("reply_count", 0),
            shares=pm.get("retweet_count", 0) + pm.get("quote_count", 0),
            raw=dict(pm),
        )
