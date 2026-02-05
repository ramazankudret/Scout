"""
Domain Events Base Classes.

Events enable loose coupling between modules. When something
important happens (threat detected, IP blocked), an event is published.
Other modules can subscribe and react.
"""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class DomainEvent(BaseModel):
    """
    Base class for all domain events.

    Events are immutable records of something that happened.
    They carry data about the occurrence.
    """

    model_config = ConfigDict(frozen=True)

    event_id: UUID = Field(default_factory=uuid4)
    event_type: str
    occurred_at: datetime = Field(default_factory=datetime.utcnow)
    aggregate_id: UUID | None = None
    aggregate_type: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "event_id": str(self.event_id),
            "event_type": self.event_type,
            "occurred_at": self.occurred_at.isoformat(),
            "aggregate_id": str(self.aggregate_id) if self.aggregate_id else None,
            "aggregate_type": self.aggregate_type,
            "payload": self.payload,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Threat Events
# ─────────────────────────────────────────────────────────────────────────────


class ThreatDetectedEvent(DomainEvent):
    """Event raised when a new threat is detected."""

    event_type: str = "threat.detected"
    threat_type: str
    severity: str
    source_ip: str | None = None


class ThreatMitigatedEvent(DomainEvent):
    """Event raised when a threat is mitigated."""

    event_type: str = "threat.mitigated"
    action_taken: str
    mitigated_by: str | None = None


class ThreatEscalatedEvent(DomainEvent):
    """Event raised when a threat is escalated to higher severity."""

    event_type: str = "threat.escalated"
    previous_severity: str
    new_severity: str
    reason: str | None = None


# ─────────────────────────────────────────────────────────────────────────────
# Asset Events
# ─────────────────────────────────────────────────────────────────────────────


class AssetDiscoveredEvent(DomainEvent):
    """Event raised when a new asset is discovered on the network."""

    event_type: str = "asset.discovered"
    ip_address: str
    asset_type: str | None = None


class AssetUnderAttackEvent(DomainEvent):
    """Event raised when an asset is detected to be under attack."""

    event_type: str = "asset.under_attack"
    asset_name: str
    threat_id: UUID | None = None


# ─────────────────────────────────────────────────────────────────────────────
# Module Events
# ─────────────────────────────────────────────────────────────────────────────


class ModuleStartedEvent(DomainEvent):
    """Event raised when a security module starts."""

    event_type: str = "module.started"
    module_name: str
    mode: str | None = None


class ModuleStoppedEvent(DomainEvent):
    """Event raised when a security module stops."""

    event_type: str = "module.stopped"
    module_name: str
    reason: str | None = None


class ActionExecutedEvent(DomainEvent):
    """Event raised when Scout takes an action (e.g., blocks an IP)."""

    event_type: str = "action.executed"
    action_type: str
    target: str
    success: bool = True
    details: str | None = None
