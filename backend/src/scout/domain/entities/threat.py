"""
Threat Entity.

Represents a detected security threat in the system.
"""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import Field

from scout.domain.entities.base import AggregateRoot


class ThreatSeverity(str, Enum):
    """Threat severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ThreatStatus(str, Enum):
    """Threat lifecycle status."""

    DETECTED = "detected"
    ANALYZING = "analyzing"
    CONFIRMED = "confirmed"
    MITIGATED = "mitigated"
    FALSE_POSITIVE = "false_positive"
    IGNORED = "ignored"


class ThreatType(str, Enum):
    """Types of threats."""

    PORT_SCAN = "port_scan"
    BRUTE_FORCE = "brute_force"
    DDOS = "ddos"
    MALWARE = "malware"
    RANSOMWARE = "ransomware"
    DATA_EXFILTRATION = "data_exfiltration"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    LATERAL_MOVEMENT = "lateral_movement"
    ANOMALY = "anomaly"
    UNKNOWN = "unknown"


class Threat(AggregateRoot):
    """
    Represents a security threat detected by Scout.

    This is an Aggregate Root that encapsulates:
    - Threat identification and classification
    - Source and target information
    - Actions taken in response
    """

    # Classification
    threat_type: ThreatType
    severity: ThreatSeverity = ThreatSeverity.MEDIUM
    status: ThreatStatus = ThreatStatus.DETECTED
    confidence_score: float = Field(ge=0.0, le=1.0, default=0.5)

    # Identification
    title: str
    description: str | None = None

    # Source & Target
    source_ip: str | None = None
    source_port: int | None = None
    target_ip: str | None = None
    target_port: int | None = None

    # Context
    detected_by_module: str | None = None
    raw_data: dict[str, Any] = Field(default_factory=dict)
    indicators: list[str] = Field(default_factory=list)

    # Timeline
    first_seen: datetime = Field(default_factory=datetime.utcnow)
    last_seen: datetime = Field(default_factory=datetime.utcnow)

    # Response
    actions_taken: list[str] = Field(default_factory=list)
    mitigated_at: datetime | None = None

    # --- Domain Methods ---

    def confirm(self, confidence: float | None = None) -> None:
        """Mark the threat as confirmed."""
        self.status = ThreatStatus.CONFIRMED
        if confidence:
            self.confidence_score = confidence
        self.update_timestamp()

    def mitigate(self, action: str) -> None:
        """Mark the threat as mitigated with the action taken."""
        self.status = ThreatStatus.MITIGATED
        self.actions_taken.append(action)
        self.mitigated_at = datetime.utcnow()
        self.update_timestamp()

    def mark_false_positive(self, reason: str | None = None) -> None:
        """Mark the threat as a false positive."""
        self.status = ThreatStatus.FALSE_POSITIVE
        if reason:
            self.description = f"{self.description or ''}\nFalse positive: {reason}"
        self.update_timestamp()

    def update_severity(self, severity: ThreatSeverity) -> None:
        """Update threat severity based on new information."""
        self.severity = severity
        self.update_timestamp()

    def record_sighting(self) -> None:
        """Record a new sighting of this threat."""
        self.last_seen = datetime.utcnow()
        self.update_timestamp()

    def is_actionable(self) -> bool:
        """Check if the threat requires action."""
        return self.status in {ThreatStatus.DETECTED, ThreatStatus.CONFIRMED}

    def is_critical(self) -> bool:
        """Check if the threat is critical severity."""
        return self.severity == ThreatSeverity.CRITICAL
