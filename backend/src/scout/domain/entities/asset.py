"""
Asset Entity.

Represents a network asset (server, device, service) being monitored by Scout.
"""

from enum import Enum

from pydantic import Field

from scout.domain.entities.base import AggregateRoot


class AssetType(str, Enum):
    """Types of network assets."""

    SERVER = "server"
    WORKSTATION = "workstation"
    NETWORK_DEVICE = "network_device"
    IOT_DEVICE = "iot_device"
    CLOUD_INSTANCE = "cloud_instance"
    CONTAINER = "container"
    SERVICE = "service"
    UNKNOWN = "unknown"


class AssetStatus(str, Enum):
    """Asset health status."""

    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"
    UNDER_ATTACK = "under_attack"
    UNKNOWN = "unknown"


class Asset(AggregateRoot):
    """
    Represents a network asset being protected by Scout.

    Assets are discovered or manually registered, and their
    security posture is continuously monitored.
    """

    # Identity
    name: str
    hostname: str | None = None
    ip_address: str | None = None
    mac_address: str | None = None

    # Classification
    asset_type: AssetType = AssetType.UNKNOWN
    status: AssetStatus = AssetStatus.UNKNOWN
    criticality: int = Field(ge=1, le=5, default=3)  # 1=low, 5=critical

    # Network Information
    open_ports: list[int] = Field(default_factory=list)
    services: list[str] = Field(default_factory=list)
    network_zone: str | None = None

    # Security Posture
    vulnerability_count: int = 0
    last_scanned_at: str | None = None
    compliance_score: float | None = None

    # Metadata
    os_type: str | None = None
    os_version: str | None = None
    tags: list[str] = Field(default_factory=list)
    notes: str | None = None

    # --- Domain Methods ---

    def mark_as_attacked(self) -> None:
        """Mark the asset as currently under attack."""
        self.status = AssetStatus.UNDER_ATTACK
        self.update_timestamp()

    def discover_service(self, port: int, service_name: str) -> None:
        """Record a discovered service on the asset."""
        if port not in self.open_ports:
            self.open_ports.append(port)
        if service_name not in self.services:
            self.services.append(service_name)
        self.update_timestamp()

    def update_status(self, status: AssetStatus) -> None:
        """Update the asset status."""
        self.status = status
        self.update_timestamp()

    def is_critical_asset(self) -> bool:
        """Check if this is a critical asset."""
        return self.criticality >= 4
