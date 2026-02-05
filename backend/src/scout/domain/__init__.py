"""Domain Layer Module."""

from scout.domain.entities import (
    AggregateRoot,
    Asset,
    AssetStatus,
    AssetType,
    Entity,
    Threat,
    ThreatSeverity,
    ThreatStatus,
    ThreatType,
    ValueObject,
)
from scout.domain.events import (
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
from scout.domain.interfaces import (
    IAssetRepository,
    IEventPublisher,
    ILLMService,
    INetworkService,
    IThreatRepository,
    Repository,
)

__all__ = [
    # Base
    "Entity",
    "AggregateRoot",
    "ValueObject",
    # Entities
    "Threat",
    "ThreatType",
    "ThreatSeverity",
    "ThreatStatus",
    "Asset",
    "AssetType",
    "AssetStatus",
    # Events
    "DomainEvent",
    "ThreatDetectedEvent",
    "ThreatMitigatedEvent",
    "ThreatEscalatedEvent",
    "AssetDiscoveredEvent",
    "AssetUnderAttackEvent",
    "ModuleStartedEvent",
    "ModuleStoppedEvent",
    "ActionExecutedEvent",
    # Interfaces
    "Repository",
    "IThreatRepository",
    "IAssetRepository",
    "ILLMService",
    "INetworkService",
    "IEventPublisher",
]
