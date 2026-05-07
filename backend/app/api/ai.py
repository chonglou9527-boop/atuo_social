from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.api.schemas import AIChatRequest, AIChatResponse, LLMConfigCreate, LLMConfigOut
from app.core.security import decrypt, encrypt
from app.db.base import get_db
from app.db.models import LLMConfig
from app.llm.base import ChatMessage
from app.llm.registry import build_provider, list_providers

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.get("/providers")
def providers() -> dict:
    return {"providers": list_providers()}


@router.get("/configs", response_model=list[LLMConfigOut])
def list_configs(db: Session = Depends(get_db)):
    return db.scalars(select(LLMConfig).order_by(LLMConfig.id.desc())).all()


@router.post("/configs", response_model=LLMConfigOut)
def create_config(payload: LLMConfigCreate, db: Session = Depends(get_db)):
    if payload.provider not in list_providers():
        raise HTTPException(400, f"unknown provider: {payload.provider}")
    cfg = LLMConfig(
        provider=payload.provider,
        model=payload.model,
        api_key_encrypted=encrypt(payload.api_key),
        base_url=payload.base_url,
        is_active=payload.is_active,
    )
    if payload.is_active:
        db.execute(update(LLMConfig).values(is_active=False))
    db.add(cfg)
    db.commit()
    db.refresh(cfg)
    return cfg


@router.post("/configs/{cfg_id}/activate", response_model=LLMConfigOut)
def activate_config(cfg_id: int, db: Session = Depends(get_db)):
    cfg = db.get(LLMConfig, cfg_id)
    if not cfg:
        raise HTTPException(404, "config not found")
    db.execute(update(LLMConfig).values(is_active=False))
    cfg.is_active = True
    db.commit()
    db.refresh(cfg)
    return cfg


@router.delete("/configs/{cfg_id}")
def delete_config(cfg_id: int, db: Session = Depends(get_db)):
    cfg = db.get(LLMConfig, cfg_id)
    if not cfg:
        raise HTTPException(404, "config not found")
    db.delete(cfg)
    db.commit()
    return {"ok": True}


@router.post("/chat", response_model=AIChatResponse)
async def chat(payload: AIChatRequest, db: Session = Depends(get_db)):
    cfg = (
        db.get(LLMConfig, payload.llm_config_id)
        if payload.llm_config_id
        else db.scalar(select(LLMConfig).where(LLMConfig.is_active.is_(True)))
    )
    if cfg is None:
        raise HTTPException(400, "No active LLM config")
    provider = build_provider(cfg.provider, decrypt(cfg.api_key_encrypted), cfg.model, cfg.base_url)
    messages = []
    if payload.system:
        messages.append(ChatMessage(role="system", content=payload.system))
    messages.append(ChatMessage(role="user", content=payload.prompt))
    text = await provider.chat(messages)
    return AIChatResponse(text=text)
