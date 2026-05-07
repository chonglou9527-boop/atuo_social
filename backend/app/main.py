from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import accounts as accounts_api
from app.api import ai as ai_api
from app.api import inbox as inbox_api
from app.api import posts as posts_api
from app.config import get_settings
from app.core.scheduler import shutdown_scheduler, start_scheduler
from app.db.base import SessionLocal, init_db
from app.db.models import InboxSource
from app.services.inbox import ingest_source
from app.services.rewrite import apply_rules_to_new_items


def _schedule_inbox_jobs() -> None:
    """Register one APScheduler job per enabled inbox source + a global rules-runner."""
    from app.core.scheduler import get_scheduler

    scheduler = get_scheduler()
    db = SessionLocal()
    try:
        sources = db.query(InboxSource).filter(InboxSource.enabled.is_(True)).all()
        for s in sources:
            scheduler.add_job(
                _run_ingest,
                trigger="interval",
                minutes=max(1, s.fetch_interval_min),
                args=[s.id],
                id=f"inbox:{s.id}",
                replace_existing=True,
                next_run_time=None,
            )
        scheduler.add_job(
            _run_rules,
            trigger="interval",
            minutes=10,
            id="inbox:rules",
            replace_existing=True,
        )
    finally:
        db.close()


async def _run_ingest(source_id: int) -> None:
    db = SessionLocal()
    try:
        s = db.get(InboxSource, source_id)
        if s and s.enabled:
            await ingest_source(db, s)
    finally:
        db.close()


async def _run_rules() -> None:
    db = SessionLocal()
    try:
        await apply_rules_to_new_items(db)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    start_scheduler()
    _schedule_inbox_jobs()
    yield
    shutdown_scheduler()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(accounts_api.router)
    app.include_router(posts_api.router)
    app.include_router(ai_api.router)
    app.include_router(inbox_api.router)

    @app.get("/api/health")
    def health() -> dict:
        return {"status": "ok"}

    return app


app = create_app()
