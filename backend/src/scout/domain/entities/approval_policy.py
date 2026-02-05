"""
Action Approval Policy Entity.

Configurable rules for when actions require human approval.
Users can customize policies per action type.
"""

from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import Field

from scout.domain.entities.base import Entity


class ApprovalRequirement(str, Enum):
    """Whether approval is required for an action."""

    ALWAYS = "always"           # Always require approval
    NEVER = "never"             # Auto-approve (use with caution!)
    CONDITIONAL = "conditional"  # Based on conditions (severity, confidence, etc.)


class TimeoutAction(str, Enum):
    """Action to take on approval timeout."""

    APPROVE = "approve"  # Auto-approve on timeout
    REJECT = "reject"    # Auto-reject on timeout (safer)


# Default timeout values by severity (in seconds)
DEFAULT_SEVERITY_TIMEOUTS: dict[str, int] = {
    "critical": 60,    # 1 minute - urgent
    "high": 180,       # 3 minutes
    "medium": 300,     # 5 minutes
    "low": 600,        # 10 minutes
}


class ActionApprovalPolicy(Entity):
    """
    Configurable policy for action approval requirements.

    Users can customize:
    - Which actions require approval
    - What conditions trigger approval
    - Timeout durations per severity
    - What happens on timeout
    - Notification preferences
    """

    # ─────────────────────────────────────────────────────────────────────────
    # Policy Identification
    # ─────────────────────────────────────────────────────────────────────────
    user_id: UUID  # Owner of this policy
    name: str = "Default Policy"
    description: str | None = None

    # ─────────────────────────────────────────────────────────────────────────
    # Action Type Targeting
    # ─────────────────────────────────────────────────────────────────────────
    action_type: str  # "block_ip", "isolate_host", "*" for all actions

    # ─────────────────────────────────────────────────────────────────────────
    # Approval Requirement
    # ─────────────────────────────────────────────────────────────────────────
    requirement: ApprovalRequirement = ApprovalRequirement.ALWAYS

    # Conditions for conditional approval (evaluated when requirement=CONDITIONAL)
    conditions: dict[str, Any] = Field(default_factory=dict)
    # Example conditions:
    # {
    #     "severity_threshold": "high",     # Only require for high+ severity
    #     "confidence_below": 0.9,          # Require if confidence < 90%
    #     "target_in_list": ["10.0.0.0/8"], # Require for internal IPs
    #     "business_hours_only": true,      # Only require during 09:00-18:00
    # }

    # ─────────────────────────────────────────────────────────────────────────
    # Timeout Configuration
    # ─────────────────────────────────────────────────────────────────────────
    timeout_seconds: int = 300  # Default 5 minutes
    timeout_action: TimeoutAction = TimeoutAction.REJECT

    # Severity-specific timeouts (overrides default timeout_seconds)
    severity_timeouts: dict[str, int] = Field(
        default_factory=lambda: DEFAULT_SEVERITY_TIMEOUTS.copy()
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Notification Preferences
    # ─────────────────────────────────────────────────────────────────────────
    notify_websocket: bool = True   # Real-time push for urgent actions
    notify_email: bool = False      # Email notification
    notify_slack: bool = False      # Slack webhook (future)

    # ─────────────────────────────────────────────────────────────────────────
    # Policy Metadata
    # ─────────────────────────────────────────────────────────────────────────
    is_active: bool = True
    priority: int = 100  # Lower = higher priority (for overlapping policies)

    # ═══════════════════════════════════════════════════════════════════════════
    # Methods
    # ═══════════════════════════════════════════════════════════════════════════

    def get_timeout_for_severity(self, severity: str) -> int:
        """
        Get timeout seconds for a given severity level.

        Args:
            severity: Severity level ("critical", "high", "medium", "low")

        Returns:
            Timeout in seconds
        """
        return self.severity_timeouts.get(severity, self.timeout_seconds)

    def requires_approval(self, context: dict[str, Any]) -> bool:
        """
        Determine if approval is required based on policy and context.

        Args:
            context: Dictionary with action details:
                - severity: str
                - confidence: float (0.0 - 1.0)
                - target: str
                - target_type: str
                - action_type: str

        Returns:
            True if approval is required
        """
        if self.requirement == ApprovalRequirement.ALWAYS:
            return True

        if self.requirement == ApprovalRequirement.NEVER:
            return False

        # Conditional evaluation
        return self._evaluate_conditions(context)

    def _evaluate_conditions(self, context: dict[str, Any]) -> bool:
        """
        Evaluate conditional rules against the given context.

        Returns True if ANY condition triggers approval requirement.
        """
        # No conditions = require approval (safe default)
        if not self.conditions:
            return True

        # Severity threshold check
        if "severity_threshold" in self.conditions:
            severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
            threshold = severity_order.get(self.conditions["severity_threshold"], 0)
            actual = severity_order.get(context.get("severity", "low"), 1)
            if actual >= threshold:
                return True

        # Confidence threshold check
        if "confidence_below" in self.conditions:
            confidence = context.get("confidence", 1.0)
            if confidence < self.conditions["confidence_below"]:
                return True

        # Target in specific list (e.g., internal network ranges)
        if "target_in_list" in self.conditions:
            target = context.get("target", "")
            target_list = self.conditions["target_in_list"]
            if self._target_matches_list(target, target_list):
                return True

        # Business hours only
        if self.conditions.get("business_hours_only"):
            if self._is_business_hours():
                return True

        # Default: don't require approval if no conditions matched
        return False

    def _target_matches_list(self, target: str, target_list: list[str]) -> bool:
        """Check if target matches any item in the list."""
        import ipaddress

        for item in target_list:
            # Direct match
            if target == item:
                return True

            # CIDR network match (for IP targets)
            try:
                network = ipaddress.ip_network(item, strict=False)
                ip = ipaddress.ip_address(target)
                if ip in network:
                    return True
            except ValueError:
                # Not a valid IP/network, skip
                continue

        return False

    def _is_business_hours(self) -> bool:
        """Check if current time is within business hours (09:00-18:00 local)."""
        from datetime import datetime

        now = datetime.now()
        return 9 <= now.hour < 18 and now.weekday() < 5  # Mon-Fri, 9am-6pm

    def to_config_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "name": self.name,
            "description": self.description,
            "action_type": self.action_type,
            "requirement": self.requirement.value,
            "conditions": self.conditions,
            "timeout_seconds": self.timeout_seconds,
            "timeout_action": self.timeout_action.value,
            "severity_timeouts": self.severity_timeouts,
            "notify_websocket": self.notify_websocket,
            "notify_email": self.notify_email,
            "notify_slack": self.notify_slack,
            "is_active": self.is_active,
            "priority": self.priority,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
