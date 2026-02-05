"""
HITL Approval Database Models.

Database models for the Human-in-the-Loop approval system.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4

from sqlalchemy import (
    String, Text, Integer, Boolean, Numeric,
    ForeignKey, DateTime, Index, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from scout.infrastructure.database.models import Base, TimestampMixin


# ============================================
# PENDING_ACTION MODEL
# ============================================
class PendingAction(Base, TimestampMixin):
    """
    Database model for pending actions awaiting human approval.

    This is the core of the HITL system - it stores action requests
    that need human approval before execution.
    """
    __tablename__ = "pending_actions"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Action Identification
    # ─────────────────────────────────────────────────────────────────────────
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # e.g., "block_ip", "unblock_ip", "isolate_host", "terminate_process"

    module_name: Mapped[str] = mapped_column(String(50), nullable=False)
    # e.g., "defense", "hunter", "stealth"

    severity: Mapped[str] = mapped_column(String(20), default="medium")
    # "critical", "high", "medium", "low"

    # ─────────────────────────────────────────────────────────────────────────
    # Target Information
    # ─────────────────────────────────────────────────────────────────────────
    target: Mapped[str] = mapped_column(String(500), nullable=False)
    # The actual target: IP address, hostname, process ID, etc.

    target_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # "ip", "host", "process", "user", "file"

    target_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    # Additional context: {"port": 22, "protocol": "TCP", "country": "CN"}

    # ─────────────────────────────────────────────────────────────────────────
    # Request Context
    # ─────────────────────────────────────────────────────────────────────────
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    # Why this action is being requested

    threat_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("incidents.id", ondelete="SET NULL")
    )
    incident_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("incidents.id", ondelete="SET NULL")
    )

    confidence_score: Mapped[float] = mapped_column(
        Numeric(3, 2), default=0.50
    )
    # 0.00 to 1.00

    # ─────────────────────────────────────────────────────────────────────────
    # Action Parameters
    # ─────────────────────────────────────────────────────────────────────────
    action_params: Mapped[dict] = mapped_column(JSONB, default=dict)
    # Parameters passed to the module when executing
    # e.g., {"duration": 3600, "reason": "Brute force detected"}

    # ─────────────────────────────────────────────────────────────────────────
    # Status
    # ─────────────────────────────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(String(20), default="pending")
    # "pending", "approved", "rejected", "expired", "executing", "completed", "failed"

    # ─────────────────────────────────────────────────────────────────────────
    # Timeout Configuration
    # ─────────────────────────────────────────────────────────────────────────
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=300)
    # Default 5 minutes

    auto_action: Mapped[str] = mapped_column(String(20), default="reject")
    # "approve" or "reject" - what happens on timeout

    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Decision Tracking
    # ─────────────────────────────────────────────────────────────────────────
    decided_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    decided_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL")
    )
    decision_method: Mapped[Optional[str]] = mapped_column(String(30))
    # "manual", "auto_timeout", "policy"

    rejection_reason: Mapped[Optional[str]] = mapped_column(Text)

    # ─────────────────────────────────────────────────────────────────────────
    # Execution Tracking
    # ─────────────────────────────────────────────────────────────────────────
    executed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    execution_result: Mapped[dict] = mapped_column(JSONB, default=dict)
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    __table_args__ = (
        Index("idx_pending_actions_user_status", "user_id", "status"),
        Index(
            "idx_pending_actions_expires",
            "expires_at",
            postgresql_where=(status == "pending")
        ),
        Index("idx_pending_actions_severity", "severity"),
        CheckConstraint(
            "status IN ('pending', 'approved', 'rejected', 'expired', 'executing', 'completed', 'failed')",
            name="chk_pending_action_status"
        ),
        CheckConstraint(
            "severity IN ('critical', 'high', 'medium', 'low')",
            name="chk_pending_action_severity"
        ),
        CheckConstraint(
            "auto_action IN ('approve', 'reject')",
            name="chk_pending_action_auto_action"
        ),
    )


# ============================================
# ACTION_APPROVAL_CONFIG MODEL
# ============================================
class ActionApprovalConfig(Base, TimestampMixin):
    """
    Database model for user-configurable approval policies.

    Users can customize which actions require approval,
    timeout durations, and what happens on timeout.
    """
    __tablename__ = "action_approval_configs"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Policy Identification
    # ─────────────────────────────────────────────────────────────────────────
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Action type this policy applies to (* for all)
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # e.g., "block_ip", "isolate_host", "*"

    # ─────────────────────────────────────────────────────────────────────────
    # Approval Requirement
    # ─────────────────────────────────────────────────────────────────────────
    requirement: Mapped[str] = mapped_column(String(20), default="always")
    # "always", "never", "conditional"

    conditions: Mapped[dict] = mapped_column(JSONB, default=dict)
    # JSON conditions for "conditional" requirement
    # e.g., {"severity_threshold": "high", "confidence_below": 0.9}

    # ─────────────────────────────────────────────────────────────────────────
    # Timeout Configuration
    # ─────────────────────────────────────────────────────────────────────────
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=300)
    timeout_action: Mapped[str] = mapped_column(String(20), default="reject")
    # "approve" or "reject"

    severity_timeouts: Mapped[dict] = mapped_column(JSONB, default=dict)
    # Per-severity timeout overrides
    # e.g., {"critical": 60, "high": 180, "medium": 300, "low": 600}

    # ─────────────────────────────────────────────────────────────────────────
    # Notification Preferences
    # ─────────────────────────────────────────────────────────────────────────
    notify_websocket: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_email: Mapped[bool] = mapped_column(Boolean, default=False)
    notify_slack: Mapped[bool] = mapped_column(Boolean, default=False)

    # ─────────────────────────────────────────────────────────────────────────
    # Policy Metadata
    # ─────────────────────────────────────────────────────────────────────────
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=100)
    # Lower = higher priority (for overlapping policies)

    __table_args__ = (
        Index("idx_approval_config_user_action", "user_id", "action_type"),
        Index(
            "idx_approval_config_active",
            "user_id",
            "is_active",
            postgresql_where=(is_active == True)
        ),
        CheckConstraint(
            "requirement IN ('always', 'never', 'conditional')",
            name="chk_approval_config_requirement"
        ),
        CheckConstraint(
            "timeout_action IN ('approve', 'reject')",
            name="chk_approval_config_timeout_action"
        ),
    )
