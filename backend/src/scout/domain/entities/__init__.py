"""Domain Entities Module."""

from scout.domain.entities.asset import Asset, AssetStatus, AssetType
from scout.domain.entities.base import AggregateRoot, Entity, ValueObject
from scout.domain.entities.threat import (
    Threat,
    ThreatSeverity,
    ThreatStatus,
    ThreatType,
)
from scout.domain.entities.pending_action import (
    ActionSeverity,
    PendingAction,
    PendingActionStatus,
    TimeoutAction,
)
from scout.domain.entities.approval_policy import (
    ActionApprovalPolicy,
    ApprovalRequirement,
)

__all__ = [
    # Base
    "Entity",
    "AggregateRoot",
    "ValueObject",
    # Threat
    "Threat",
    "ThreatType",
    "ThreatSeverity",
    "ThreatStatus",
    # Asset
    "Asset",
    "AssetType",
    "AssetStatus",
    # HITL - Pending Actions
    "PendingAction",
    "PendingActionStatus",
    "ActionSeverity",
    "TimeoutAction",
    # HITL - Approval Policy
    "ActionApprovalPolicy",
    "ApprovalRequirement",
]
