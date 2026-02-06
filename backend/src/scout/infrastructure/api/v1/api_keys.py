"""
API Keys – list, create, delete (current user).
"""
import hashlib
import secrets
from uuid import UUID
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from scout.infrastructure.database import get_db, User, ApiKey
from scout.infrastructure.repositories.repositories import ApiKeyRepository
from scout.infrastructure.api.v1.auth import get_current_user

router = APIRouter(prefix="/api-keys", tags=["API Keys"])


class ApiKeyResponse(BaseModel):
    id: UUID
    name: str
    key_prefix: str | None
    created_at: str | None
    last_used_at: str | None

    class Config:
        from_attributes = True


class ApiKeyCreateResponse(BaseModel):
    id: UUID
    name: str
    key_prefix: str
    key: str


class ApiKeyCreate(BaseModel):
    name: str


@router.get("", response_model=list[ApiKeyResponse])
async def list_api_keys(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List current user's API keys (no secret)."""
    repo = ApiKeyRepository(db)
    keys = await repo.get_by_user(current_user.id)
    return [
        ApiKeyResponse(
            id=k.id,
            name=k.name,
            key_prefix=k.key_prefix,
            created_at=k.created_at.isoformat() if getattr(k, "created_at", None) else None,
            last_used_at=k.last_used_at.isoformat() if k.last_used_at else None,
        )
        for k in keys
    ]


@router.post("", response_model=ApiKeyCreateResponse)
async def create_api_key(
    body: ApiKeyCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create API key. The raw key is returned only once."""
    raw_key = "sk_" + secrets.token_urlsafe(32)
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    key_prefix = raw_key[:12]
    repo = ApiKeyRepository(db)
    key = await repo.create(
        user_id=current_user.id,
        name=body.name,
        key_prefix=key_prefix,
        key_hash=key_hash,
    )
    await db.commit()
    await db.refresh(key)
    return ApiKeyCreateResponse(
        id=key.id,
        name=key.name,
        key_prefix=key_prefix,
        key=raw_key,
    )


@router.delete("/{key_id}")
async def delete_api_key(
    key_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Revoke/delete an API key (own only)."""
    repo = ApiKeyRepository(db)
    key = await repo.get(key_id)
    if not key or key.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
    await db.delete(key)
    await db.commit()
    return {"ok": True}
