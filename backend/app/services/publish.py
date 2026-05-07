from __future__ import annotations

import json
import logging
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.security import decrypt
from app.db.base import SessionLocal
from app.db.models import Account, MetricSnapshot, Post, PostStatus, PostTarget, TargetStatus
from app.platforms.registry import build_adapter

logger = logging.getLogger(__name__)


def _credentials_for(account: Account) -> dict:
    raw = decrypt(account.credentials_encrypted)
    return json.loads(raw)


async def publish_target(target_id: int) -> None:
    """Publish a single PostTarget. Used both for immediate publish and APScheduler jobs."""
    db: Session = SessionLocal()
    try:
        target = db.get(PostTarget, target_id)
        if target is None:
            logger.warning("publish_target: target %s not found", target_id)
            return
        post = db.get(Post, target.post_id)
        account = db.get(Account, target.account_id)
        if post is None or account is None:
            target.status = TargetStatus.failed.value
            target.error_msg = "post or account missing"
            db.commit()
            return

        target.status = TargetStatus.publishing.value
        post.status = PostStatus.publishing.value
        db.commit()

        try:
            adapter = build_adapter(account.platform, _credentials_for(account))
            content = adapter.adapt_content(post)
            result = await adapter.publish(post, target, content)
        except Exception as e:  # noqa: BLE001
            target.status = TargetStatus.failed.value
            target.error_msg = str(e)[:2000]
            target.retry_count += 1
            db.commit()
            logger.exception("publish failed: target=%s", target_id)
            # mark post failed only if all targets failed
            remaining = [t for t in post.targets if t.status not in {TargetStatus.failed.value, TargetStatus.published.value}]
            if not remaining and not any(t.status == TargetStatus.published.value for t in post.targets):
                post.status = PostStatus.failed.value
                db.commit()
            return

        target.status = TargetStatus.published.value
        target.published_at = datetime.utcnow()
        target.remote_id = result.remote_id
        target.remote_url = result.remote_url
        target.error_msg = None
        post.status = PostStatus.published.value
        db.commit()
        logger.info("published target=%s remote=%s", target_id, result.remote_id)
    finally:
        db.close()


async def fetch_metrics(target_id: int) -> None:
    db: Session = SessionLocal()
    try:
        target = db.get(PostTarget, target_id)
        if target is None or not target.remote_id:
            return
        account = db.get(Account, target.account_id)
        if account is None:
            return
        adapter = build_adapter(account.platform, _credentials_for(account))
        m = await adapter.fetch_metrics(target)
        db.add(
            MetricSnapshot(
                post_target_id=target.id,
                views=m.views,
                likes=m.likes,
                comments=m.comments,
                shares=m.shares,
                raw_json=m.raw,
            )
        )
        db.commit()
    finally:
        db.close()
