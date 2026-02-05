"""
Action Approval Service.

Orchestrates the Human-in-the-Loop approval workflow.
This is the core service for the HITL system.
"""

from datetime import datetime, timedelta
from typing import Any, Protocol
from uuid import UUID

from scout.core.logging import get_logger
from scout.domain.entities.pending_action import (
    ActionSeverity,
    PendingAction as PendingActionEntity,
    PendingActionStatus,
    TimeoutAction,
)
from scout.domain.entities.approval_policy import (
    ActionApprovalPolicy,
    ApprovalRequirement,
    DEFAULT_SEVERITY_TIMEOUTS,
)
from scout.domain.events.approval_events import (
    ActionApprovedEvent,
    ActionPendingApprovalEvent,
    ActionRejectedEvent,
)
from scout.infrastructure.database.models_approval import (
    PendingAction,
    ActionApprovalConfig,
)

logger = get_logger(__name__)


class IEventPublisher(Protocol):
    """Protocol for event publishing."""
    async def publish(self, event: Any) -> None: ...


class IWebSocketManager(Protocol):
    """Protocol for WebSocket manager."""
    async def broadcast_to_user(self, user_id: UUID, message: dict) -> int: ...


class ActionApprovalService:
    """
    Service for managing action approval workflow.

    Responsibilities:
    - Check if actions require approval based on user policies
    - Create pending action records
    - Process approvals/rejections
    - Notify users via WebSocket and notifications
    """

    def __init__(
        self,
        pending_action_repo: Any,  # PendingActionRepository
        policy_repo: Any,  # ApprovalPolicyRepository
        notification_repo: Any | None = None,  # NotificationRepository
        event_publisher: IEventPublisher | None = None,
        websocket_manager: IWebSocketManager | None = None,
    ):
        self.pending_action_repo = pending_action_repo
        self.policy_repo = policy_repo
        self.notification_repo = notification_repo
        self.event_publisher = event_publisher
        self.websocket_manager = websocket_manager

    async def request_approval(
        self,
        user_id: UUID,
        action_type: str,
        module_name: str,
        target: str,
        target_type: str,
        reason: str,
        severity: ActionSeverity = ActionSeverity.MEDIUM,
        action_params: dict[str, Any] | None = None,
        target_metadata: dict[str, Any] | None = None,
        threat_id: UUID | None = None,
        incident_id: UUID | None = None,
        confidence_score: float = 0.5,
    ) -> PendingAction | None:
        """
        Request approval for an action.

        This is the main entry point for the HITL system.
        Call this before executing any potentially dangerous action.

        Args:
            user_id: The user who owns this action
            action_type: Type of action (e.g., "block_ip")
            module_name: Module requesting the action
            target: Target of the action (IP, hostname, etc.)
            target_type: Type of target ("ip", "host", etc.)
            reason: Why this action is being requested
            severity: Severity level of the action
            action_params: Parameters to pass when executing
            target_metadata: Additional target context
            threat_id: Related threat ID (optional)
            incident_id: Related incident ID (optional)
            confidence_score: AI confidence (0.0 - 1.0)

        Returns:
            PendingAction if approval is required, None if auto-approved
        """
        # Get applicable policy for this action type
        policy = await self._get_policy_for_action(user_id, action_type)

        # Build context for policy evaluation
        context = {
            "severity": severity.value if isinstance(severity, ActionSeverity) else severity,
            "confidence": confidence_score,
            "target": target,
            "target_type": target_type,
            "action_type": action_type,
        }

        # Check if approval is required based on policy
        requires_approval = self._evaluate_policy(policy, context)

        if not requires_approval:
            logger.info(
                "action_auto_approved",
                action_type=action_type,
                target=target,
                reason="policy_bypass",
                user_id=str(user_id),
            )
            return None  # No approval needed, execute immediately

        # Calculate expiration time
        timeout = self._get_timeout_for_severity(policy, severity)
        expires_at = datetime.utcnow() + timedelta(seconds=timeout)

        # Determine auto-action on timeout
        auto_action = policy.timeout_action if policy else "reject"

        # Create pending action record
        pending_action = PendingAction(
            user_id=user_id,
            action_type=action_type,
            module_name=module_name,
            severity=severity.value if isinstance(severity, ActionSeverity) else severity,
            target=target,
            target_type=target_type,
            target_metadata=target_metadata or {},
            reason=reason,
            action_params=action_params or {},
            threat_id=threat_id,
            incident_id=incident_id,
            confidence_score=confidence_score,
            status="pending",
            timeout_seconds=timeout,
            auto_action=auto_action if isinstance(auto_action, str) else auto_action.value,
            expires_at=expires_at,
        )

        # Save to database
        saved_action = await self.pending_action_repo.create(pending_action)

        # Publish event
        if self.event_publisher:
            event = ActionPendingApprovalEvent(
                pending_action_id=saved_action.id,
                action_type=action_type,
                module_name=module_name,
                severity=severity.value if isinstance(severity, ActionSeverity) else severity,
                target=target,
                target_type=target_type,
                reason=reason,
                confidence_score=confidence_score,
                auto_action=auto_action if isinstance(auto_action, str) else auto_action.value,
                expires_at=expires_at,
                aggregate_id=saved_action.id,
                aggregate_type="PendingAction",
            )
            await self.event_publisher.publish(event)

        # Send real-time notification
        await self._notify_pending_action(saved_action, policy)

        logger.info(
            "action_pending_approval",
            pending_action_id=str(saved_action.id),
            action_type=action_type,
            target=target,
            severity=severity.value if isinstance(severity, ActionSeverity) else severity,
            expires_at=expires_at.isoformat(),
            user_id=str(user_id),
        )

        return saved_action

    async def approve(
        self,
        pending_action_id: UUID,
        user_id: UUID,
    ) -> PendingAction:
        """
        Approve a pending action.

        Args:
            pending_action_id: The pending action ID
            user_id: The user approving the action

        Returns:
            Updated PendingAction

        Raises:
            ValueError: If action not found or not in pending status
        """
        action = await self.pending_action_repo.get(pending_action_id)

        if not action:
            raise ValueError(f"Pending action {pending_action_id} not found")

        if action.status != "pending":
            raise ValueError(
                f"Action {pending_action_id} is not pending (status: {action.status})"
            )

        # Update status
        action.status = "approved"
        action.decided_at = datetime.utcnow()
        action.decided_by = user_id
        action.decision_method = "manual"

        await self.pending_action_repo.update(action)

        # Publish event
        if self.event_publisher:
            event = ActionApprovedEvent(
                pending_action_id=action.id,
                action_type=action.action_type,
                target=action.target,
                approved_by=user_id,
                approval_method="manual",
                aggregate_id=action.id,
                aggregate_type="PendingAction",
            )
            await self.event_publisher.publish(event)

        # Notify via WebSocket
        if self.websocket_manager:
            await self.websocket_manager.broadcast_to_user(
                action.user_id,
                {
                    "type": "action_approved",
                    "pending_action_id": str(action.id),
                    "action_type": action.action_type,
                    "target": action.target,
                }
            )

        logger.info(
            "action_approved",
            pending_action_id=str(action.id),
            approved_by=str(user_id),
            action_type=action.action_type,
            target=action.target,
        )

        return action

    async def reject(
        self,
        pending_action_id: UUID,
        user_id: UUID,
        reason: str | None = None,
    ) -> PendingAction:
        """
        Reject a pending action.

        Args:
            pending_action_id: The pending action ID
            user_id: The user rejecting the action
            reason: Optional rejection reason

        Returns:
            Updated PendingAction

        Raises:
            ValueError: If action not found or not in pending status
        """
        action = await self.pending_action_repo.get(pending_action_id)

        if not action:
            raise ValueError(f"Pending action {pending_action_id} not found")

        if action.status != "pending":
            raise ValueError(
                f"Action {pending_action_id} is not pending (status: {action.status})"
            )

        # Update status
        action.status = "rejected"
        action.decided_at = datetime.utcnow()
        action.decided_by = user_id
        action.decision_method = "manual"
        action.rejection_reason = reason

        await self.pending_action_repo.update(action)

        # Publish event
        if self.event_publisher:
            event = ActionRejectedEvent(
                pending_action_id=action.id,
                action_type=action.action_type,
                target=action.target,
                rejected_by=user_id,
                rejection_reason=reason,
                rejection_method="manual",
                aggregate_id=action.id,
                aggregate_type="PendingAction",
            )
            await self.event_publisher.publish(event)

        # Notify via WebSocket
        if self.websocket_manager:
            await self.websocket_manager.broadcast_to_user(
                action.user_id,
                {
                    "type": "action_rejected",
                    "pending_action_id": str(action.id),
                    "action_type": action.action_type,
                    "target": action.target,
                    "reason": reason,
                }
            )

        logger.info(
            "action_rejected",
            pending_action_id=str(action.id),
            rejected_by=str(user_id),
            reason=reason,
            action_type=action.action_type,
            target=action.target,
        )

        return action

    async def get_pending_actions(
        self,
        user_id: UUID,
        status: str | None = None,
        severity: str | None = None,
        limit: int = 50,
    ) -> list[PendingAction]:
        """Get pending actions for a user."""
        return await self.pending_action_repo.get_by_user(
            user_id=user_id,
            status=status,
            severity=severity,
            limit=limit,
        )

    async def get_pending_count(self, user_id: UUID) -> int:
        """Get count of pending actions for a user."""
        return await self.pending_action_repo.get_pending_count(user_id)

    async def get_stats(self, user_id: UUID) -> dict:
        """Get approval statistics for a user."""
        return await self.pending_action_repo.get_stats(user_id)

    # ═══════════════════════════════════════════════════════════════════════════
    # Private Methods
    # ═══════════════════════════════════════════════════════════════════════════

    async def _get_policy_for_action(
        self,
        user_id: UUID,
        action_type: str,
    ) -> ActionApprovalConfig | None:
        """Get the applicable policy for an action type."""
        return await self.policy_repo.get_by_action_type(user_id, action_type)

    def _evaluate_policy(
        self,
        policy: ActionApprovalConfig | None,
        context: dict[str, Any],
    ) -> bool:
        """
        Evaluate whether approval is required based on policy and context.

        Returns True if approval is required.
        """
        # No policy = require approval (safe default)
        if not policy:
            return True

        requirement = policy.requirement

        if requirement == "always":
            return True
        if requirement == "never":
            return False

        # Conditional evaluation
        conditions = policy.conditions or {}

        # Severity threshold check
        if "severity_threshold" in conditions:
            severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
            threshold = severity_order.get(conditions["severity_threshold"], 0)
            actual = severity_order.get(context.get("severity", "low"), 1)
            if actual >= threshold:
                return True

        # Confidence threshold check
        if "confidence_below" in conditions:
            confidence = context.get("confidence", 1.0)
            if confidence < conditions["confidence_below"]:
                return True

        # Default: don't require approval if no conditions matched
        return False

    def _get_timeout_for_severity(
        self,
        policy: ActionApprovalConfig | None,
        severity: ActionSeverity | str,
    ) -> int:
        """Get timeout seconds for a given severity level."""
        severity_str = severity.value if isinstance(severity, ActionSeverity) else severity

        if policy and policy.severity_timeouts:
            return policy.severity_timeouts.get(severity_str, policy.timeout_seconds)

        # Fall back to defaults
        return DEFAULT_SEVERITY_TIMEOUTS.get(severity_str, 300)

    async def _notify_pending_action(
        self,
        action: PendingAction,
        policy: ActionApprovalConfig | None,
    ) -> None:
        """Send notifications for a pending action."""
        # Determine if WebSocket notification is needed
        notify_websocket = True
        if policy:
            notify_websocket = policy.notify_websocket

        # Also always notify for critical/high severity
        is_urgent = action.severity in ("critical", "high")

        if (notify_websocket or is_urgent) and self.websocket_manager:
            await self.websocket_manager.broadcast_to_user(
                action.user_id,
                {
                    "type": "action_pending_approval",
                    "pending_action": {
                        "id": str(action.id),
                        "action_type": action.action_type,
                        "module_name": action.module_name,
                        "target": action.target,
                        "severity": action.severity,
                        "reason": action.reason,
                        "expires_at": action.expires_at.isoformat() if action.expires_at else None,
                        "auto_action": action.auto_action,
                        "confidence_score": float(action.confidence_score),
                    }
                }
            )

        # Create notification record if repo is available
        if self.notification_repo:
            from scout.infrastructure.database.models import Notification

            notification = Notification(
                user_id=action.user_id,
                notification_type="action_approval",
                category="security",
                title=f"Action Requires Approval: {action.action_type}",
                message=f"Scout wants to {action.action_type} on {action.target}. Reason: {action.reason}",
                severity=action.severity,
                is_actionable=True,
                related_type="pending_action",
                related_id=action.id,
                actions=[
                    {"label": "Approve", "action": "approve", "style": "primary"},
                    {"label": "Reject", "action": "reject", "style": "danger"},
                ],
                expires_at=action.expires_at,
            )
            await self.notification_repo.create(notification)
