"""AI rewrite of an inbox item into a draft Post.

Pipeline: pick LLMConfig (rule-specified or default active) -> build prompt
-> call LLM -> parse loose JSON -> persist Post + assets -> mark inbox item used.

Prompt is intentionally lightweight; the model returns a JSON object with
title/body/tags so we don't need to scrape free-form output.
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decrypt
from app.db.models import (
    InboxItem,
    InboxItemStatus,
    LLMConfig,
    Post,
    PostAsset,
    PostStatus,
    RewriteRule,
)
from app.llm.base import ChatMessage
from app.llm.registry import build_provider

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """你是资深自媒体编辑。把用户给的原始素材改写为一条可直接发布的图文草稿。
要求：
1. 不要照抄原文；保留事实但用自己的话表达。
2. 输出严格 JSON，键固定为 title / body / tags（tags 为字符串数组，最多 6 个）。
3. body 使用纯文本或轻量 Markdown，长度控制在用户指定平台的合理区间。
4. 不要输出 JSON 以外的任何文字。"""


def _pick_llm(db: Session, rule: RewriteRule | None) -> LLMConfig | None:
    if rule and rule.llm_config_id:
        cfg = db.get(LLMConfig, rule.llm_config_id)
        if cfg:
            return cfg
    return db.scalar(select(LLMConfig).where(LLMConfig.is_active.is_(True)).limit(1))


def _extract_json(text: str) -> dict:
    text = text.strip()
    # strip ```json fences if present
    fence = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, re.DOTALL)
    if fence:
        text = fence.group(1)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            return json.loads(m.group(0))
        raise


def _build_user_prompt(item: InboxItem, rule: RewriteRule | None) -> str:
    target_platforms = (rule.target_platforms_json if rule else []) or []
    style = (rule.style_prompt if rule else "") or ""
    parts = [
        f"原标题: {item.title}",
        f"原内容:\n{item.content}",
    ]
    if item.url:
        parts.append(f"原链接: {item.url}")
    if target_platforms:
        parts.append(f"目标发布平台: {', '.join(target_platforms)}")
    if style:
        parts.append(f"风格要求: {style}")
    parts.append('请输出 JSON: {"title": "...", "body": "...", "tags": ["..."]}')
    return "\n\n".join(parts)


async def rewrite_inbox_item(
    db: Session,
    item: InboxItem,
    rule: RewriteRule | None = None,
) -> Post:
    cfg = _pick_llm(db, rule)
    if cfg is None:
        raise RuntimeError("No active LLM config; configure one before rewriting.")

    provider = build_provider(
        cfg.provider,
        api_key=decrypt(cfg.api_key_encrypted),
        model=cfg.model,
        base_url=cfg.base_url,
    )

    raw = await provider.chat(
        [
            ChatMessage(role="system", content=SYSTEM_PROMPT),
            ChatMessage(role="user", content=_build_user_prompt(item, rule)),
        ],
        temperature=0.7,
        max_tokens=1500,
    )

    try:
        data = _extract_json(raw)
    except json.JSONDecodeError:
        logger.warning("LLM returned non-JSON, falling back to raw body")
        data = {"title": item.title or "", "body": raw, "tags": []}

    post = Post(
        title=str(data.get("title") or item.title or "")[:256],
        body_md=str(data.get("body") or ""),
        cover_url=item.image_url,
        status=PostStatus.draft.value,
    )
    db.add(post)
    db.flush()

    if item.image_url:
        db.add(PostAsset(post_id=post.id, url=item.image_url, type="image", order=0))

    item.status = InboxItemStatus.used.value
    item.rewritten_post_id = post.id
    db.commit()
    db.refresh(post)
    logger.info("rewrote inbox_item=%s -> post=%s (rule=%s)", item.id, post.id, rule.id if rule else None)
    return post


# ---------- Rule matching ----------


def _matches(item: InboxItem, rule: RewriteRule) -> bool:
    if rule.source_ids_json and item.source_id not in rule.source_ids_json:
        return False

    keywords = [k.lower() for k in (rule.keywords_json or []) if k]
    if keywords:
        haystack = f"{item.title}\n{item.content}".lower()
        if not any(k in haystack for k in keywords):
            return False

    rule_tags = {t.lower() for t in (rule.tags_json or []) if t}
    if rule_tags:
        item_tags = {str(t).lower() for t in (item.tags_json or [])}
        if rule_tags.isdisjoint(item_tags):
            return False

    return True


async def apply_rules_to_new_items(db: Session) -> int:
    """Find inbox items in `new` status, run them through enabled rules, rewrite first match."""
    rules = db.scalars(select(RewriteRule).where(RewriteRule.enabled.is_(True))).all()
    if not rules:
        return 0
    new_items = db.scalars(select(InboxItem).where(InboxItem.status == InboxItemStatus.new.value)).all()
    rewritten = 0
    for item in new_items:
        for rule in rules:
            if _matches(item, rule):
                try:
                    await rewrite_inbox_item(db, item, rule)
                    rewritten += 1
                except Exception:  # noqa: BLE001
                    logger.exception("auto-rewrite failed for item=%s rule=%s", item.id, rule.id)
                break  # one rule per item
    return rewritten
