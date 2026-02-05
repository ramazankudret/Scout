"""
Approval-related Domain Events.

Events for the Human-in-the-Loop approval workflow.
"""

from datetime import datetime
from uuid import UUID

from scout.domain.events.base import DomainEvent


class ActionPendingApprovalEvent(DomainEvent):
    """Event raised when an action requires human approval."""

    event_type: str = "action.pending_approval"
    pending_action_id: UUID
    action_type: str  # e.g., "block_ip", "isolate_host", "kill_process"
    module_name: str
    severity: str  # "critical", "high", "medium", "low"
    target: str  # The target of the action (IP, hostname, etc.)
    target_type: str  # "ip", "host", "process", "user", "file"
    reason: str  # Why this action is being requested
    confidence_score: float = 0.5
    auto_action: str = "reject"  # "approve" or "reject" - what happens on timeout
    expires_at: datetime | None = None


class ActionApprovedEvent(DomainEvent):
    """Event raised when a pending action is approved."""

    event_type: str = "action.approved"
    pending_action_id: UUID
    action_type: str
    target: str
    approved_by: UUID | None = None  # User ID, None if auto-approved
    approval_method: str = "manual"  # "manual", "auto_timeout", "policy"


class ActionRejectedEvent(DomainEvent):
    """Event raised when a pending action is rejected."""

    event_type: str = "action.rejected"
    pending_action_id: UUID
    action_type: str
    target: str
    rejected_by: UUID | None = None  # User ID, None if auto-rejected
    rejection_reason: str | None = None
    rejection_method: str = "manual"  # "manual", "auto_timeout", "policy"


class ActionExpiredEvent(DomainEvent):
    """Event raised when a pending action expires without decision."""

    event_type: str = "action.expired"
    pending_action_id: UUID
    action_type: str
    target: str
    auto_action_taken: str  # What action was taken due to expiry ("approve" or "reject")


class ActionExecutingEvent(DomainEvent):
    """Event raised when an approved action starts executing."""

    event_type: str = "action.executing"
    pending_action_id: UUID
    action_type: str
    target: str


class ActionCompletedEvent(DomainEvent):
    """Event raised when an action completes successfully."""

    event_type: str = "action.completed"
    pending_action_id: UUID
    action_type: str
    target: str
    execution_time_ms: float | None = None


class ActionFailedEvent(DomainEvent):
    """Event raised when an action fails during execution."""

    event_type: str = "action.failed"
    pending_action_id: UUID
    action_type: str
    target: str
    error_message: str
