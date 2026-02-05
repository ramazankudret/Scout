"""
Approval Timeout Service.

Handles automatic approval/rejection of expired pending actions.
This service runs periodically in the background.
"""

from datetime import datetime
from typing import Any, Protocol
from uuid import UUID

from scout.core.logging import get_logger
from scout.domain.events.approval_events import (
    ActionApprovedEvent,
    ActionExpiredEvent,
    ActionRejectedEvent,
)
from scout.infrastructure.database.models_approval import PendingAction

logger = get_logger(__name__)


class IEventPublisher(Protocol):
    """Protocol for event publishing."""
    async def publish(self, event: Any) -> None: ...


class IWebSocketManager(Protocol):
    """Protocol for WebSocket manager."""
    async def broadcast_to_user(self, user_id: UUID, message: dict) -> int: ...


class IActionExecutor(Protocol):
    """Protocol for action execution."""
    async def execute(self, action: PendingAction) -> dict[str, Any]: ...


class ApprovalTimeoutService:
    """
    Background service for processing approval timeouts.

    Runs periodically to:
    1. Find expired pending actions
    2. Apply auto-action (approve/reject)
    3. Execute auto-approved actions
    4. Notify users
    """

    def __init__(
        self,
        pending_action_repo: Any,  # PendingActionRepository
        event_publisher: IEventPublisher | None = None,
        action_executor: IActionExecutor | None = None,
        websocket_manager: IWebSocketManager | None = None,
    ):
        self.pending_action_repo = pending_action_repo
        self.event_publisher = event_publisher
        self.action_executor = action_executor
        self.websocket_manager = websocket_manager

    async def process_expired_actions(self) -> int:
        """
        Process all expired pending actions.

        This is the main method called by the background task.

        Returns:
            Number of actions processed
        """
        # Get all expired actions
        expired_actions = await self.pending_action_repo.get_expired()
        processed = 0

        for action in expired_actions:
            try:
                await self._process_expired_action(action)
                processed += 1
            except Exception as e:
                logger.exception(
                    "timeout_processing_failed",
                    pending_action_id=str(action.id),
                    error=str(e),
                )

        if processed > 0:
            logger.info("timeout_processing_complete", processed_count=processed)

        return processed

    async def _process_expired_action(self, action: PendingAction) -> None:
        """Process a single expired action."""
        auto_action = action.auto_action

        # Mark as expired first
        action.status = "expired"
        action.decided_at = datetime.utcnow()
        action.decision_method = "auto_timeout"

        if auto_action == "approve":
            # Auto-approve: execute the action
            await self._handle_auto_approve(action)
        else:
            # Auto-reject: just update status
            await self._handle_auto_reject(action)

        # Publish expired event
        if self.event_publisher:
            event = ActionExpiredEvent(
                pending_action_id=action.id,
                action_type=action.action_type,
                target=action.target,
                auto_action_taken=auto_action,
                aggregate_id=action.id,
                aggregate_type="PendingAction",
            )
            await self.event_publisher.publish(event)

        # Notify user via WebSocket
        if self.websocket_manager:
            await self.websocket_manager.broadcast_to_user(
                action.user_id,
                {
                    "type": "action_expired",
                    "pending_action_id": str(action.id),
                    "action_type": action.action_type,
                    "target": action.target,
                    "auto_action": auto_action,
                }
            )

    async def _handle_auto_approve(self, action: PendingAction) -> None:
        """Handle auto-approval of an expired action."""
        # Update status to approved
        action.status = "approved"
        await self.pending_action_repo.update(action)

        # Publish approved event
        if self.event_publisher:
            event = ActionApprovedEvent(
                pending_action_id=action.id,
                action_type=action.action_type,
                target=action.target,
                approved_by=None,  # Auto-approved
                approval_method="auto_timeout",
                aggregate_id=action.id,
                aggregate_type="PendingAction",
            )
            await self.event_publisher.publish(event)

        # Execute the action if executor is available
        if self.action_executor:
            try:
                result = await self.action_executor.execute(action)
                action.status = "completed"
                action.execution_result = result
                action.executed_at = datetime.utcnow()
            except Exception as e:
                action.status = "failed"
                action.error_message = str(e)
                logger.error(
                    "auto_approved_execution_failed",
                    pending_action_id=str(action.id),
                    error=str(e),
                )

            await self.pending_action_repo.update(action)

        logger.info(
            "action_auto_approved",
            pending_action_id=str(action.id),
            action_type=action.action_type,
            target=action.target,
        )

    async def _handle_auto_reject(self, action: PendingAction) -> None:
        """Handle auto-rejection of an expired action."""
        # Update status to rejected
        action.status = "rejected"
        action.rejection_reason = "Approval timeout - auto-rejected"
        await self.pending_action_repo.update(action)

        # Publish rejected event
        if self.event_publisher:
            event = ActionRejectedEvent(
                pending_action_id=action.id,
                action_type=action.action_type,
                target=action.target,
                rejected_by=None,  # Auto-rejected
                rejection_reason="Approval timeout",
                rejection_method="auto_timeout",
                aggregate_id=action.id,
                aggregate_type="PendingAction",
            )
            await self.event_publisher.publish(event)

        logger.info(
            "action_auto_rejected",
            pending_action_id=str(action.id),
            action_type=action.action_type,
            target=action.target,
        )
