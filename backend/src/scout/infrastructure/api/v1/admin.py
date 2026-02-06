"""
Admin API – user management (superuser only).
"""
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from scout.infrastructure.database import get_db, User
from scout.infrastructure.repositories import UserRepository
from scout.infrastructure.api.v1.auth import get_current_user, require_superuser

router = APIRouter(prefix="/admin", tags=["Admin"])


class AdminUserResponse(BaseModel):
    id: UUID
    email: str
    username: Optional[str]
    full_name: Optional[str]
    is_active: bool
    is_verified: bool
    is_superuser: bool
    last_login_at: Optional[str]
    created_at: Optional[str]

    class Config:
        from_attributes = True


class AdminUserListResponse(BaseModel):
    items: list[AdminUserResponse]
    total: int


class AdminUserUpdate(BaseModel):
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None


@router.get("/users", response_model=AdminUserListResponse)
async def list_users(
    current_user: Annotated[User, Depends(require_superuser)],
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    is_active: Optional[bool] = Query(None),
    q: Optional[str] = Query(None),
):
    """List users with pagination and filters (superuser only)."""
    repo = UserRepository(db)
    users = await repo.list_users(skip=skip, limit=limit, is_active=is_active, q=q)
    total = await repo.count_users(is_active=is_active, q=q)
    return AdminUserListResponse(
        items=[
            AdminUserResponse(
                id=u.id,
                email=u.email,
                username=u.username,
                full_name=u.full_name,
                is_active=u.is_active,
                is_verified=u.is_verified,
                is_superuser=u.is_superuser,
                last_login_at=u.last_login_at.isoformat() if u.last_login_at else None,
                created_at=u.created_at.isoformat() if getattr(u, "created_at", None) else None,
            )
            for u in users
        ],
        total=total,
    )


@router.patch("/users/{user_id}", response_model=AdminUserResponse)
async def update_user(
    user_id: UUID,
    body: AdminUserUpdate,
    current_user: Annotated[User, Depends(require_superuser)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update user is_active or is_superuser (superuser only)."""
    repo = UserRepository(db)
    user = await repo.get(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if body.is_active is not None:
        user.is_active = body.is_active
    if body.is_superuser is not None:
        user.is_superuser = body.is_superuser
    await db.commit()
    await db.refresh(user)
    return AdminUserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        is_active=user.is_active,
        is_verified=user.is_verified,
        is_superuser=user.is_superuser,
        last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
        created_at=user.created_at.isoformat() if getattr(user, "created_at", None) else None,
    )
