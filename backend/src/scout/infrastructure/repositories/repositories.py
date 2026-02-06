"""
Specialized Repositories for Scout entities
"""
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, and_, or_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from scout.infrastructure.database.models import (
    User, Asset, Incident, Vulnerability,
    AgentRun, AgentMemory, ScanResult, Notification,
    ApiKey,
)
from scout.infrastructure.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        query = select(User).where(User.email == email)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        query = select(User).where(User.username == username)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_active_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all active users"""
        query = (
            select(User)
            .where(User.is_active == True)
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_users(
        self,
        skip: int = 0,
        limit: int = 50,
        is_active: Optional[bool] = None,
        q: Optional[str] = None,
    ) -> List[User]:
        """List users with optional filters (admin)."""
        query = select(User).order_by(desc(User.created_at))
        if is_active is not None:
            query = query.where(User.is_active == is_active)
        if q and q.strip():
            term = f"%{q.strip()}%"
            query = query.where(or_(User.email.ilike(term), User.username.ilike(term)))
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_users(
        self,
        is_active: Optional[bool] = None,
        q: Optional[str] = None,
    ) -> int:
        """Count users with same filters as list_users."""
        query = select(func.count()).select_from(User)
        if is_active is not None:
            query = query.where(User.is_active == is_active)
        if q and q.strip():
            term = f"%{q.strip()}%"
            query = query.where(or_(User.email.ilike(term), User.username.ilike(term)))
        result = await self.session.execute(query)
        return result.scalar() or 0


class AssetRepository(BaseRepository[Asset]):
    """Repository for Asset operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Asset, session)
    
    async def get_by_ip(self, user_id: UUID, ip: str) -> Optional[Asset]:
        """Get asset by IP address"""
        query = select(Asset).where(
            and_(Asset.user_id == user_id, Asset.ip_address == ip)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_type(
        self, 
        user_id: UUID, 
        asset_type: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Asset]:
        """Get assets by type"""
        query = (
            select(Asset)
            .where(and_(Asset.user_id == user_id, Asset.asset_type == asset_type))
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_critical_assets(self, user_id: UUID) -> List[Asset]:
        """Get high-risk assets"""
        query = (
            select(Asset)
            .where(
                and_(
                    Asset.user_id == user_id,
                    or_(
                        Asset.criticality == "critical",
                        Asset.criticality == "high"
                    )
                )
            )
            .order_by(desc(Asset.risk_score))
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_vulnerable_assets(self, user_id: UUID, limit: int = 10) -> List[Asset]:
        """Get assets with vulnerabilities"""
        query = (
            select(Asset)
            .where(
                and_(
                    Asset.user_id == user_id,
                    Asset.vulnerability_count > 0
                )
            )
            .order_by(desc(Asset.vulnerability_count))
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())


class IncidentRepository(BaseRepository[Incident]):
    """Repository for Incident operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Incident, session)
    
    async def get_open_incidents(
        self, 
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Incident]:
        """Get all open incidents"""
        query = (
            select(Incident)
            .where(
                and_(
                    Incident.user_id == user_id,
                    Incident.status.in_(["new", "investigating", "contained"])
                )
            )
            .order_by(desc(Incident.detected_at))
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_by_severity(
        self, 
        user_id: UUID, 
        severity: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Incident]:
        """Get incidents by severity"""
        query = (
            select(Incident)
            .where(and_(Incident.user_id == user_id, Incident.severity == severity))
            .order_by(desc(Incident.detected_at))
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_recent(
        self, 
        user_id: UUID, 
        hours: int = 24,
        limit: int = 50
    ) -> List[Incident]:
        """Get incidents from last N hours"""
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        query = (
            select(Incident)
            .where(
                and_(
                    Incident.user_id == user_id,
                    Incident.detected_at >= cutoff
                )
            )
            .order_by(desc(Incident.detected_at))
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_stats(self, user_id: UUID) -> dict:
        """Get incident statistics"""
        from sqlalchemy import func
        
        total = await self.count_by_user(user_id)
        
        # Count by status
        status_query = (
            select(Incident.status, func.count(Incident.id))
            .where(Incident.user_id == user_id)
            .group_by(Incident.status)
        )
        status_result = await self.session.execute(status_query)
        by_status = dict(status_result.all())
        
        # Count by severity
        severity_query = (
            select(Incident.severity, func.count(Incident.id))
            .where(Incident.user_id == user_id)
            .group_by(Incident.severity)
        )
        severity_result = await self.session.execute(severity_query)
        by_severity = dict(severity_result.all())
        
        return {
            "total": total,
            "by_status": by_status,
            "by_severity": by_severity
        }


class AgentRunRepository(BaseRepository[AgentRun]):
    """Repository for Agent Run operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(AgentRun, session)
    
    async def get_running(self, user_id: UUID) -> List[AgentRun]:
        """Get currently running agents"""
        query = (
            select(AgentRun)
            .where(
                and_(
                    AgentRun.user_id == user_id,
                    AgentRun.status == "running"
                )
            )
            .order_by(desc(AgentRun.started_at))
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_by_agent(
        self, 
        user_id: UUID, 
        agent_name: str,
        limit: int = 50
    ) -> List[AgentRun]:
        """Get runs for specific agent"""
        query = (
            select(AgentRun)
            .where(
                and_(
                    AgentRun.user_id == user_id,
                    AgentRun.agent_name == agent_name
                )
            )
            .order_by(desc(AgentRun.created_at))
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_failed(self, user_id: UUID, limit: int = 20) -> List[AgentRun]:
        """Get failed agent runs"""
        query = (
            select(AgentRun)
            .where(
                and_(
                    AgentRun.user_id == user_id,
                    AgentRun.status.in_(["failed", "timeout"])
                )
            )
            .order_by(desc(AgentRun.created_at))
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())


class NotificationRepository(BaseRepository[Notification]):
    """Repository for Notification operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Notification, session)
    
    async def get_unread(self, user_id: UUID, limit: int = 50) -> List[Notification]:
        """Get unread notifications"""
        query = (
            select(Notification)
            .where(
                and_(
                    Notification.user_id == user_id,
                    Notification.is_read == False
                )
            )
            .order_by(desc(Notification.created_at))
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def mark_as_read(self, notification_id: UUID) -> bool:
        """Mark notification as read"""
        notification = await self.get(notification_id)
        if notification:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            await self.session.flush()
            return True
        return False
    
    async def mark_all_read(self, user_id: UUID) -> int:
        """Mark all notifications as read"""
        from sqlalchemy import update
        query = (
            update(Notification)
            .where(
                and_(
                    Notification.user_id == user_id,
                    Notification.is_read == False
                )
            )
            .values(is_read=True, read_at=datetime.utcnow())
        )
        result = await self.session.execute(query)
        return result.rowcount


class ApiKeyRepository(BaseRepository[ApiKey]):
    """Repository for API key operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(ApiKey, session)

    async def list_by_user(self, user_id: UUID, skip: int = 0, limit: int = 50) -> List[ApiKey]:
        """List API keys for a user."""
        return await self.get_by_user(user_id, skip=skip, limit=limit)
