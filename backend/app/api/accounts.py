import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.schemas import AccountCreate, AccountOut
from app.core.security import encrypt
from app.db.base import get_db
from app.db.models import Account
from app.platforms.registry import supported_platforms

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


@router.get("/platforms")
def list_platforms() -> dict:
    return {"platforms": supported_platforms()}


@router.get("", response_model=list[AccountOut])
def list_accounts(db: Session = Depends(get_db)):
    return db.scalars(select(Account).order_by(Account.id.desc())).all()


@router.post("", response_model=AccountOut)
def create_account(payload: AccountCreate, db: Session = Depends(get_db)):
    if payload.platform not in supported_platforms():
        raise HTTPException(400, f"unsupported platform: {payload.platform}")
    acc = Account(
        platform=payload.platform,
        name=payload.name,
        auth_type=payload.auth_type,
        credentials_encrypted=encrypt(json.dumps(payload.credentials)),
        status="active",
        last_check_at=datetime.utcnow(),
    )
    db.add(acc)
    db.commit()
    db.refresh(acc)
    return acc


@router.delete("/{account_id}")
def delete_account(account_id: int, db: Session = Depends(get_db)):
    acc = db.get(Account, account_id)
    if not acc:
        raise HTTPException(404, "account not found")
    db.delete(acc)
    db.commit()
    return {"ok": True}
