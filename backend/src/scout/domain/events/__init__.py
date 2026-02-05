"""Domain Events Module."""

from scout.domain.events.base import (
    ActionExecutedEvent,
    AssetDiscoveredEvent,
    AssetUnderAttackEvent,
    DomainEvent,
    ModuleStartedEvent,
    ModuleStoppedEvent,
    ThreatDetectedEvent,
    ThreatEscalatedEvent,
    ThreatMitigatedEvent,
)
from scout.domain.events.approval_events import (
    ActionApprovedEvent,
    ActionCompletedEvent,
    ActionExecutingEvent,
    ActionExpiredEvent,
    ActionFailedEvent,
    ActionPendingApprovalEvent,
    ActionRejectedEvent,
)

__all__ = [
    "DomainEvent",
    # Threat Events
    "ThreatDetectedEvent",
    "ThreatMitigatedEvent",
    "ThreatEscalatedEvent",
    # Asset Events
    "AssetDiscoveredEvent",
    "AssetUnderAttackEvent",
    # Module Events
    "ModuleStartedEvent",
    "ModuleStoppedEvent",
    "ActionExecutedEvent",
    # HITL Approval Events
    "ActionPendingApprovalEvent",
    "ActionApprovedEvent",
    "ActionRejectedEvent",
    "ActionExpiredEvent",
    "ActionExecutingEvent",
    "ActionCompletedEvent",
    "ActionFailedEvent",
]
