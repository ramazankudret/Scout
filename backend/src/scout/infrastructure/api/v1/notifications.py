"""
Notifications API – list and mark as read.
"""
from uuid import UUID
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from scout.infrastructure.database import get_db, User
from scout.infrastructure.repositories import NotificationRepository
from scout.infrastructure.api.v1.auth import get_current_user

router = APIRouter(prefix="/notifications", tags=["Notifications"])


class NotificationResponse(BaseModel):
    id: UUID
    notification_type: str
    title: str
    message: str | None
    severity: str
    is_read: bool
    created_at: str | None

    class Config:
        from_attributes = True


@router.get("", response_model=list[NotificationResponse])
async def list_notifications(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """List notifications for current user."""
    from sqlalchemy.ext.asyncio import AsyncSession
    repo = NotificationRepository(db)
    notifications = await repo.get_by_user(current_user.id, skip=skip, limit=limit)
    return [
        NotificationResponse(
            id=n.id,
            notification_type=n.notification_type,
            title=n.title,
            message=n.message,
            severity=n.severity,
            is_read=n.is_read,
            created_at=n.created_at.isoformat() if getattr(n, "created_at", None) else None,
        )
        for n in notifications
    ]


@router.post("/{notification_id}/read")
async def mark_notification_read(
    notification_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Mark a notification as read."""
    repo = NotificationRepository(db)
    ok = await repo.mark_as_read(notification_id)
    if ok:
        await db.commit()
    return {"ok": ok}


@router.post("/read-all")
async def mark_all_read(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Mark all notifications as read."""
    repo = NotificationRepository(db)
    count = await repo.mark_all_read(current_user.id)
    await db.commit()
    return {"marked": count}