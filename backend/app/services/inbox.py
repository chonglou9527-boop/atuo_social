from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import InboxItem, InboxSource
from app.inbox.registry import build_fetcher

logger = logging.getLogger(__name__)


async def ingest_source(db: Session, source: InboxSource) -> tuple[int, int]:
    """Fetch a source and persist new items. Returns (fetched, new)."""
    fetcher = build_fetcher(source.type, dict(source.config_json or {}))
    try:
        items = await fetcher.fetch()
    except Exception as e:  # noqa: BLE001
        source.last_error = str(e)[:1000]
        source.last_fetched_at = datetime.utcnow()
        db.commit()
        logger.exception("inbox fetch failed for source %s", source.id)
        raise

    new_count = 0
    for fi in items:
        exists = db.scalar(
            select(InboxItem.id).where(
                InboxItem.source_id == source.id,
                InboxItem.external_id == fi.external_id,
            )
        )
        if exists:
            continue
        db.add(
            InboxItem(
                source_id=source.id,
                external_id=fi.external_id,
                title=fi.title or "",
                content=fi.content or "",
                summary=fi.summary,
                url=fi.url,
                author=fi.author,
                image_url=fi.image_url,
                tags_json=list(fi.tags or []),
                published_at=fi.published_at,
                raw_json=fi.raw,
            )
        )
        new_count += 1
    source.last_fetched_at = datetime.utcnow()
    source.last_error = None
    db.commit()
    return len(items), new_count


async def ingest_all_enabled(db: Session) -> dict[int, tuple[int, int]]:
    sources = db.scalars(select(InboxSource).where(InboxSource.enabled.is_(True))).all()
    results: dict[int, tuple[int, int]] = {}
    for s in sources:
        try:
            results[s.id] = await ingest_source(db, s)
        except Exception:  # noqa: BLE001
            results[s.id] = (0, 0)
    return results
