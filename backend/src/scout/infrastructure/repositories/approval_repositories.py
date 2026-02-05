"""
Approval Repositories.

Database access for HITL approval entities.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, and_, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from scout.infrastructure.database.models_approval import (
    PendingAction,
    ActionApprovalConfig,
)
from scout.infrastructure.repositories.base import BaseRepository


class PendingActionRepository(BaseRepository[PendingAction]):
    """Repository for PendingAction operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(PendingAction, session)

    async def get_by_user(
        self,
        user_id: UUID,
        status: str | None = None,
        severity: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[PendingAction]:
        """
        Get pending actions for a user with optional filters.

        Args:
            user_id: The user ID
            status: Optional status filter (e.g., "pending")
            severity: Optional severity filter (e.g., "critical")
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of matching PendingAction records
        """
        conditions = [PendingAction.user_id == user_id]

        if status:
            conditions.append(PendingAction.status == status)
        if severity:
            conditions.append(PendingAction.severity == severity)

        query = (
            select(PendingAction)
            .where(and_(*conditions))
            .order_by(PendingAction.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_expired(self) -> List[PendingAction]:
        """
        Get all expired pending actions that need processing.

        Returns:
            List of expired PendingAction records still in "pending" status
        """
        query = (
            select(PendingAction)
            .where(
                and_(
                    PendingAction.status == "pending",
                    PendingAction.expires_at <= datetime.utcnow(),
                )
            )
            .order_by(PendingAction.expires_at.asc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_pending_count(self, user_id: UUID) -> int:
        """
        Get count of pending actions for a user.

        Args:
            user_id: The user ID

        Returns:
            Number of pending actions
        """
        query = (
            select(func.count())
            .select_from(PendingAction)
            .where(
                and_(
                    PendingAction.user_id == user_id,
                    PendingAction.status == "pending",
                )
            )
        )
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def get_critical_pending(self, user_id: UUID) -> List[PendingAction]:
        """
        Get critical and high severity pending actions.

        Args:
            user_id: The user ID

        Returns:
            List of critical/high severity pending actions
        """
        query = (
            select(PendingAction)
            .where(
                and_(
                    PendingAction.user_id == user_id,
                    PendingAction.status == "pending",
                    PendingAction.severity.in_(["critical", "high"]),
                )
            )
            .order_by(PendingAction.created_at.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_stats(self, user_id: UUID) -> dict:
        """
        Get approval statistics for a user.

        Returns:
            Dictionary with counts by status
        """
        query = (
            select(
                PendingAction.status,
                func.count().label("count")
            )
            .where(PendingAction.user_id == user_id)
            .group_by(PendingAction.status)
        )
        result = await self.session.execute(query)
        rows = result.all()

        stats = {
            "pending": 0,
            "approved": 0,
            "rejected": 0,
            "expired": 0,
            "completed": 0,
            "failed": 0,
        }
        for row in rows:
            if row.status in stats:
                stats[row.status] = row.count

        stats["total"] = sum(stats.values())
        return stats

    async def update_status(
        self,
        action_id: UUID,
        new_status: str,
        decided_by: UUID | None = None,
        decision_method: str | None = None,
        rejection_reason: str | None = None,
    ) -> bool:
        """
        Update the status of a pending action.

        Args:
            action_id: The action ID
            new_status: New status value
            decided_by: User ID who made the decision (optional)
            decision_method: How the decision was made (optional)
            rejection_reason: Reason for rejection (optional)

        Returns:
            True if updated, False if not found
        """
        values = {
            "status": new_status,
            "decided_at": datetime.utcnow(),
        }
        if decided_by:
            values["decided_by"] = decided_by
        if decision_method:
            values["decision_method"] = decision_method
        if rejection_reason:
            values["rejection_reason"] = rejection_reason

        stmt = (
            update(PendingAction)
            .where(PendingAction.id == action_id)
            .values(**values)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0


class ApprovalPolicyRepository(BaseRepository[ActionApprovalConfig]):
    """Repository for ActionApprovalConfig operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(ActionApprovalConfig, session)

    async def get_by_action_type(
        self,
        user_id: UUID,
        action_type: str,
    ) -> Optional[ActionApprovalConfig]:
        """
        Get policy for a specific action type.

        First looks for exact match, then falls back to wildcard (*).

        Args:
            user_id: The user ID
            action_type: The action type (e.g., "block_ip")

        Returns:
            Matching policy or None
        """
        # First try exact match
        query = (
            select(ActionApprovalConfig)
            .where(
                and_(
                    ActionApprovalConfig.user_id == user_id,
                    ActionApprovalConfig.action_type == action_type,
                    ActionApprovalConfig.is_active == True,
                )
            )
            .order_by(ActionApprovalConfig.priority.asc())
            .limit(1)
        )
        result = await self.session.execute(query)
        policy = result.scalar_one_or_none()

        if policy:
            return policy

        # Fall back to wildcard
        query = (
            select(ActionApprovalConfig)
            .where(
                and_(
                    ActionApprovalConfig.user_id == user_id,
                    ActionApprovalConfig.action_type == "*",
                    ActionApprovalConfig.is_active == True,
                )
            )
            .order_by(ActionApprovalConfig.priority.asc())
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_all_for_user(
        self,
        user_id: UUID,
        include_inactive: bool = False,
    ) -> List[ActionApprovalConfig]:
        """
        Get all approval configs for a user.

        Args:
            user_id: The user ID
            include_inactive: Whether to include inactive policies

        Returns:
            List of policies ordered by priority
        """
        conditions = [ActionApprovalConfig.user_id == user_id]

        if not include_inactive:
            conditions.append(ActionApprovalConfig.is_active == True)

        query = (
            select(ActionApprovalConfig)
            .where(and_(*conditions))
            .order_by(ActionApprovalConfig.priority.asc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create_default_policies(self, user_id: UUID) -> List[ActionApprovalConfig]:
        """
        Create default approval policies for a new user.

        Args:
            user_id: The user ID

        Returns:
            List of created policies
        """
        default_policies = [
            ActionApprovalConfig(
                user_id=user_id,
                name="Block IP Policy",
                description="Require approval for IP blocking actions",
                action_type="block_ip",
                requirement="always",
                timeout_seconds=300,
                timeout_action="reject",
                severity_timeouts={
                    "critical": 60,
                    "high": 180,
                    "medium": 300,
                    "low": 600,
                },
                notify_websocket=True,
                priority=100,
            ),
            ActionApprovalConfig(
                user_id=user_id,
                name="Host Isolation Policy",
                description="Require approval for host isolation",
                action_type="isolate_host",
                requirement="always",
                timeout_seconds=300,
                timeout_action="reject",
                severity_timeouts={
                    "critical": 60,
                    "high": 180,
                    "medium": 300,
                    "low": 600,
                },
                notify_websocket=True,
                priority=100,
            ),
            ActionApprovalConfig(
                user_id=user_id,
                name="Default Policy",
                description="Default policy for all other actions",
                action_type="*",
                requirement="conditional",
                conditions={
                    "severity_threshold": "high",
                    "confidence_below": 0.9,
                },
                timeout_seconds=300,
                timeout_action="reject",
                severity_timeouts={
                    "critical": 60,
                    "high": 180,
                    "medium": 300,
                    "low": 600,
                },
                notify_websocket=True,
                priority=1000,  # Lower priority (fallback)
            ),
        ]

        for policy in default_policies:
            self.session.add(policy)

        await self.session.commit()

        # Refresh to get IDs
        for policy in default_policies:
            await self.session.refresh(policy)

        return default_policies
