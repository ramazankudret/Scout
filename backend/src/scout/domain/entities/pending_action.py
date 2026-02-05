"""
Pending Action Entity.

Represents an action awaiting human approval in the HITL workflow.
"""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import Field

from scout.domain.entities.base import AggregateRoot


class PendingActionStatus(str, Enum):
    """Status of a pending action in the approval workflow."""

    PENDING = "pending"        # Waiting for human decision
    APPROVED = "approved"      # Human approved the action
    REJECTED = "rejected"      # Human rejected the action
    EXPIRED = "expired"        # Timeout reached, auto-action applied
    EXECUTING = "executing"    # Approved action is being executed
    COMPLETED = "completed"    # Action executed successfully
    FAILED = "failed"          # Action execution failed


class ActionSeverity(str, Enum):
    """Severity level for actions - determines notification urgency."""

    CRITICAL = "critical"  # Immediate WebSocket push, short timeout
    HIGH = "high"          # WebSocket push, medium timeout
    MEDIUM = "medium"      # Polling + optional push
    LOW = "low"            # Polling only


class TimeoutAction(str, Enum):
    """Action to take when approval times out."""

    APPROVE = "approve"  # Auto-approve on timeout (use with caution)
    REJECT = "reject"    # Auto-reject on timeout (safer default)


class PendingAction(AggregateRoot):
    """
    Represents a defensive action awaiting human approval.

    Lifecycle:
    1. PENDING - Waiting for human decision
    2. APPROVED/REJECTED - Human made a decision
    3. EXPIRED - Timeout reached, auto-action applied
    4. EXECUTING - Approved action being executed
    5. COMPLETED/FAILED - Action execution result
    """

    # ─────────────────────────────────────────────────────────────────────────
    # Action Identification
    # ─────────────────────────────────────────────────────────────────────────
    action_type: str  # "block_ip", "unblock_ip", "isolate_host", "terminate_process"
    module_name: str  # Module requesting the action (e.g., "defense", "hunter")
    severity: ActionSeverity = ActionSeverity.MEDIUM

    # ─────────────────────────────────────────────────────────────────────────
    # Target Information
    # ─────────────────────────────────────────────────────────────────────────
    target: str  # Primary target (IP address, hostname, process ID, etc.)
    target_type: str  # "ip", "host", "process", "user", "file"
    target_metadata: dict[str, Any] = Field(default_factory=dict)
    # Example metadata: {"port": 22, "protocol": "TCP", "country": "CN"}

    # ─────────────────────────────────────────────────────────────────────────
    # Request Context
    # ─────────────────────────────────────────────────────────────────────────
    reason: str  # Why this action is being requested
    threat_id: UUID | None = None  # Related threat if applicable
    incident_id: UUID | None = None  # Related incident if applicable
    confidence_score: float = Field(ge=0.0, le=1.0, default=0.5)

    # Parameters for the action (passed to module when executing)
    action_params: dict[str, Any] = Field(default_factory=dict)
    # Example: {"duration": 3600, "reason": "Brute force detected"}

    # ─────────────────────────────────────────────────────────────────────────
    # Status Tracking
    # ─────────────────────────────────────────────────────────────────────────
    status: PendingActionStatus = PendingActionStatus.PENDING

    # ─────────────────────────────────────────────────────────────────────────
    # Timeout Configuration
    # ─────────────────────────────────────────────────────────────────────────
    timeout_seconds: int = 300  # 5 minutes default
    auto_action: TimeoutAction = TimeoutAction.REJECT
    expires_at: datetime | None = None

    # ─────────────────────────────────────────────────────────────────────────
    # Decision Tracking
    # ─────────────────────────────────────────────────────────────────────────
    decided_at: datetime | None = None
    decided_by: UUID | None = None  # User ID who made the decision
    decision_method: str | None = None  # "manual", "auto_timeout", "policy"
    rejection_reason: str | None = None

    # ─────────────────────────────────────────────────────────────────────────
    # Execution Tracking
    # ─────────────────────────────────────────────────────────────────────────
    executed_at: datetime | None = None
    execution_result: dict[str, Any] = Field(default_factory=dict)
    error_message: str | None = None

    # ─────────────────────────────────────────────────────────────────────────
    # User Context
    # ─────────────────────────────────────────────────────────────────────────
    user_id: UUID  # Owner of the action request

    # ═══════════════════════════════════════════════════════════════════════════
    # State Transition Methods
    # ═══════════════════════════════════════════════════════════════════════════

    def approve(self, user_id: UUID | None = None, method: str = "manual") -> None:
        """
        Approve the pending action.

        Args:
            user_id: ID of the user who approved (None for auto-approval)
            method: How the approval was made ("manual", "auto_timeout", "policy")
        """
        if not self.is_pending():
            raise ValueError(f"Cannot approve action in status: {self.status}")

        self.status = PendingActionStatus.APPROVED
        self.decided_at = datetime.utcnow()
        self.decided_by = user_id
        self.decision_method = method
        self.update_timestamp()

    def reject(
        self,
        user_id: UUID | None = None,
        reason: str | None = None,
        method: str = "manual",
    ) -> None:
        """
        Reject the pending action.

        Args:
            user_id: ID of the user who rejected (None for auto-rejection)
            reason: Optional reason for rejection
            method: How the rejection was made ("manual", "auto_timeout", "policy")
        """
        if not self.is_pending():
            raise ValueError(f"Cannot reject action in status: {self.status}")

        self.status = PendingActionStatus.REJECTED
        self.decided_at = datetime.utcnow()
        self.decided_by = user_id
        self.rejection_reason = reason
        self.decision_method = method
        self.update_timestamp()

    def expire(self) -> None:
        """Mark action as expired and record the auto-action."""
        if not self.is_pending():
            raise ValueError(f"Cannot expire action in status: {self.status}")

        self.status = PendingActionStatus.EXPIRED
        self.decided_at = datetime.utcnow()
        self.decision_method = "auto_timeout"
        self.update_timestamp()

    def mark_executing(self) -> None:
        """Mark action as currently executing."""
        if self.status not in (PendingActionStatus.APPROVED, PendingActionStatus.EXPIRED):
            raise ValueError(f"Cannot execute action in status: {self.status}")

        self.status = PendingActionStatus.EXECUTING
        self.executed_at = datetime.utcnow()
        self.update_timestamp()

    def mark_completed(self, result: dict[str, Any] | None = None) -> None:
        """Mark action as successfully completed."""
        if self.status != PendingActionStatus.EXECUTING:
            raise ValueError(f"Cannot complete action in status: {self.status}")

        self.status = PendingActionStatus.COMPLETED
        if result:
            self.execution_result = result
        self.update_timestamp()

    def mark_failed(self, error: str) -> None:
        """Mark action as failed."""
        if self.status != PendingActionStatus.EXECUTING:
            raise ValueError(f"Cannot fail action in status: {self.status}")

        self.status = PendingActionStatus.FAILED
        self.error_message = error
        self.update_timestamp()

    # ═══════════════════════════════════════════════════════════════════════════
    # Query Methods
    # ═══════════════════════════════════════════════════════════════════════════

    def is_pending(self) -> bool:
        """Check if action is still pending approval."""
        return self.status == PendingActionStatus.PENDING

    def is_decided(self) -> bool:
        """Check if a decision has been made (approved, rejected, or expired)."""
        return self.status in (
            PendingActionStatus.APPROVED,
            PendingActionStatus.REJECTED,
            PendingActionStatus.EXPIRED,
        )

    def is_terminal(self) -> bool:
        """Check if action is in a terminal state (completed, failed, or rejected)."""
        return self.status in (
            PendingActionStatus.COMPLETED,
            PendingActionStatus.FAILED,
            PendingActionStatus.REJECTED,
        )

    def is_expired(self) -> bool:
        """Check if action has expired based on expires_at timestamp."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    def should_auto_approve(self) -> bool:
        """Check if this action should be auto-approved on timeout."""
        return self.auto_action == TimeoutAction.APPROVE

    def requires_immediate_attention(self) -> bool:
        """Check if action requires immediate attention (WebSocket push)."""
        return self.severity in (ActionSeverity.CRITICAL, ActionSeverity.HIGH)

    def time_remaining_seconds(self) -> int | None:
        """Get seconds remaining until expiration."""
        if self.expires_at is None:
            return None
        remaining = (self.expires_at - datetime.utcnow()).total_seconds()
        return max(0, int(remaining))

    # ═══════════════════════════════════════════════════════════════════════════
    # Serialization
    # ═══════════════════════════════════════════════════════════════════════════

    def to_notification_dict(self) -> dict[str, Any]:
        """Convert to dictionary suitable for notification/WebSocket payload."""
        return {
            "id": str(self.id),
            "action_type": self.action_type,
            "module_name": self.module_name,
            "severity": self.severity.value,
            "target": self.target,
            "target_type": self.target_type,
            "reason": self.reason,
            "status": self.status.value,
            "confidence_score": self.confidence_score,
            "auto_action": self.auto_action.value,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "time_remaining": self.time_remaining_seconds(),
            "created_at": self.created_at.isoformat(),
        }
