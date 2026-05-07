import asyncio

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.schemas import PostCreate, PostOut, PostUpdate, PublishRequest, TargetOut
from app.core.scheduler import get_scheduler
from app.db.base import get_db
from app.db.models import Account, Post, PostAsset, PostStatus, PostTarget, TargetStatus
from app.services.publish import publish_target

router = APIRouter(prefix="/api/posts", tags=["posts"])


def _replace_assets(db: Session, post: Post, assets):
    for old in list(post.assets):
        db.delete(old)
    for a in assets or []:
        db.add(PostAsset(post_id=post.id, url=a.url, type=a.type, order=a.order))


@router.get("", response_model=list[PostOut])
def list_posts(db: Session = Depends(get_db), limit: int = 100):
    return db.scalars(select(Post).order_by(Post.id.desc()).limit(limit)).all()


@router.post("", response_model=PostOut)
def create_post(payload: PostCreate, db: Session = Depends(get_db)):
    post = Post(title=payload.title, body_md=payload.body_md, cover_url=payload.cover_url)
    db.add(post)
    db.flush()
    _replace_assets(db, post, payload.assets)
    db.commit()
    db.refresh(post)
    return post


@router.get("/{post_id}", response_model=PostOut)
def get_post(post_id: int, db: Session = Depends(get_db)):
    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(404, "post not found")
    return post


@router.patch("/{post_id}", response_model=PostOut)
def update_post(post_id: int, payload: PostUpdate, db: Session = Depends(get_db)):
    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(404, "post not found")
    if payload.title is not None:
        post.title = payload.title
    if payload.body_md is not None:
        post.body_md = payload.body_md
    if payload.cover_url is not None:
        post.cover_url = payload.cover_url
    if payload.assets is not None:
        _replace_assets(db, post, payload.assets)
    db.commit()
    db.refresh(post)
    return post


@router.delete("/{post_id}")
def delete_post(post_id: int, db: Session = Depends(get_db)):
    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(404, "post not found")
    db.delete(post)
    db.commit()
    return {"ok": True}


@router.post("/{post_id}/publish", response_model=list[TargetOut])
async def publish_post(
    post_id: int,
    payload: PublishRequest,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
):
    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(404, "post not found")

    accounts = db.scalars(select(Account).where(Account.id.in_(payload.account_ids))).all()
    if len(accounts) != len(payload.account_ids):
        raise HTTPException(400, "some accounts missing")

    targets: list[PostTarget] = []
    for acc in accounts:
        t = PostTarget(
            post_id=post.id,
            account_id=acc.id,
            platform=acc.platform,
            scheduled_at=payload.scheduled_at,
            status=TargetStatus.scheduled.value if payload.scheduled_at else TargetStatus.pending.value,
        )
        db.add(t)
        targets.append(t)
    post.status = PostStatus.queued.value
    db.commit()
    for t in targets:
        db.refresh(t)

    if payload.scheduled_at is None:
        # fire-and-forget; runs in background loop
        for t in targets:
            background.add_task(_run_publish, t.id)
    else:
        scheduler = get_scheduler()
        for t in targets:
            scheduler.add_job(
                publish_target,
                trigger="date",
                run_date=payload.scheduled_at,
                args=[t.id],
                id=f"publish:{t.id}",
                replace_existing=True,
            )
    return targets


def _run_publish(target_id: int):
    """Run async publish_target from a sync background-task context."""
    asyncio.run(publish_target(target_id))
