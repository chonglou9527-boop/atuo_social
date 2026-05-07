from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.schemas import (
    InboxItemOut,
    InboxSourceCreate,
    InboxSourceOut,
    PostOut,
    RewriteRuleCreate,
    RewriteRuleOut,
)
from app.db.base import get_db
from app.db.models import InboxItem, InboxItemStatus, InboxSource, RewriteRule
from app.inbox.registry import supported_types
from app.services.inbox import ingest_source
from app.services.rewrite import apply_rules_to_new_items, rewrite_inbox_item

router = APIRouter(prefix="/api/inbox", tags=["inbox"])


# ---------- sources ----------


@router.get("/source-types")
def source_types() -> dict:
    return {"types": supported_types()}


@router.get("/sources", response_model=list[InboxSourceOut])
def list_sources(db: Session = Depends(get_db)):
    return db.scalars(select(InboxSource).order_by(InboxSource.id.desc())).all()


@router.post("/sources", response_model=InboxSourceOut)
def create_source(payload: InboxSourceCreate, db: Session = Depends(get_db)):
    if payload.type not in supported_types():
        raise HTTPException(400, f"unsupported type: {payload.type}")
    s = InboxSource(
        name=payload.name,
        type=payload.type,
        config_json=payload.config,
        fetch_interval_min=payload.fetch_interval_min,
        enabled=payload.enabled,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


@router.delete("/sources/{source_id}")
def delete_source(source_id: int, db: Session = Depends(get_db)):
    s = db.get(InboxSource, source_id)
    if not s:
        raise HTTPException(404, "source not found")
    db.delete(s)
    db.commit()
    return {"ok": True}


@router.post("/sources/{source_id}/fetch")
async def fetch_now(source_id: int, db: Session = Depends(get_db)):
    s = db.get(InboxSource, source_id)
    if not s:
        raise HTTPException(404, "source not found")
    fetched, new = await ingest_source(db, s)
    return {"fetched": fetched, "new": new}


# ---------- items ----------


@router.get("/items", response_model=list[InboxItemOut])
def list_items(
    db: Session = Depends(get_db),
    status: str | None = None,
    source_id: int | None = None,
    limit: int = 100,
):
    q = select(InboxItem).order_by(InboxItem.id.desc())
    if status:
        q = q.where(InboxItem.status == status)
    if source_id is not None:
        q = q.where(InboxItem.source_id == source_id)
    q = q.limit(limit)
    return db.scalars(q).all()


@router.post("/items/{item_id}/rewrite", response_model=PostOut)
async def rewrite_item(item_id: int, rule_id: int | None = None, db: Session = Depends(get_db)):
    item = db.get(InboxItem, item_id)
    if not item:
        raise HTTPException(404, "item not found")
    rule = db.get(RewriteRule, rule_id) if rule_id else None
    post = await rewrite_inbox_item(db, item, rule)
    return post


@router.patch("/items/{item_id}/status")
def update_status(item_id: int, status: str, db: Session = Depends(get_db)):
    if status not in {s.value for s in InboxItemStatus}:
        raise HTTPException(400, "invalid status")
    item = db.get(InboxItem, item_id)
    if not item:
        raise HTTPException(404, "item not found")
    item.status = status
    db.commit()
    return {"ok": True}


# ---------- rules ----------


@router.get("/rules", response_model=list[RewriteRuleOut])
def list_rules(db: Session = Depends(get_db)):
    return db.scalars(select(RewriteRule).order_by(RewriteRule.id.desc())).all()


@router.post("/rules", response_model=RewriteRuleOut)
def create_rule(payload: RewriteRuleCreate, db: Session = Depends(get_db)):
    rule = RewriteRule(
        name=payload.name,
        enabled=payload.enabled,
        source_ids_json=payload.source_ids,
        keywords_json=payload.keywords,
        tags_json=payload.tags,
        style_prompt=payload.style_prompt,
        target_platforms_json=payload.target_platforms,
        llm_config_id=payload.llm_config_id,
        auto_publish=payload.auto_publish,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/rules/{rule_id}")
def delete_rule(rule_id: int, db: Session = Depends(get_db)):
    rule = db.get(RewriteRule, rule_id)
    if not rule:
        raise HTTPException(404, "rule not found")
    db.delete(rule)
    db.commit()
    return {"ok": True}


@router.post("/rules/run")
async def run_rules(db: Session = Depends(get_db)):
    n = await apply_rules_to_new_items(db)
    return {"rewritten": n}
