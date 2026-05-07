"""Twitter list-timeline fetcher (read-only).

Config keys:
    bearer_token (required)
    list_id (required)
    max_results (optional, default 50)
"""
from __future__ import annotations

import asyncio

import tweepy

from app.inbox.base import FetchedItem, InboxFetcher


class TwitterListFetcher(InboxFetcher):
    type_name = "twitter_list"

    def _client(self) -> tweepy.Client:
        return tweepy.Client(bearer_token=self.config["bearer_token"], wait_on_rate_limit=False)

    async def fetch(self) -> list[FetchedItem]:
        list_id = self.config["list_id"]
        max_results = int(self.config.get("max_results", 50))
        client = self._client()

        resp = await asyncio.to_thread(
            client.get_list_tweets,
            id=list_id,
            max_results=min(max_results, 100),
            tweet_fields=["created_at", "author_id", "public_metrics", "entities"],
            expansions=["author_id"],
            user_fields=["username", "name"],
        )

        users = {u.id: u for u in (resp.includes or {}).get("users", [])}
        items: list[FetchedItem] = []
        for tw in resp.data or []:
            author = users.get(tw.author_id)
            handle = author.username if author else None
            url = f"https://x.com/{handle}/status/{tw.id}" if handle else f"https://x.com/i/status/{tw.id}"
            items.append(
                FetchedItem(
                    external_id=str(tw.id),
                    title=(tw.text or "")[:120],
                    content=tw.text or "",
                    url=url,
                    author=handle,
                    published_at=tw.created_at,
                    raw={"id": str(tw.id), "metrics": dict(tw.public_metrics or {})},
                )
            )
        return items
