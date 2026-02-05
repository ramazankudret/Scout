"""
Unit Tests for Domain Entities.
"""

from uuid import uuid4

import pytest

from scout.domain.entities import (
    Asset,
    AssetStatus,
    AssetType,
    Threat,
    ThreatSeverity,
    ThreatStatus,
    ThreatType,
)


class TestThreatEntity:
    """Tests for Threat entity."""

    def test_create_threat(self) -> None:
        """Test creating a threat with required fields."""
        threat = Threat(
            title="Port Scan Detected",
            threat_type=ThreatType.PORT_SCAN,
        )

        assert threat.title == "Port Scan Detected"
        assert threat.threat_type == ThreatType.PORT_SCAN
        assert threat.severity == ThreatSeverity.MEDIUM  # default
        assert threat.status == ThreatStatus.DETECTED  # default
        assert threat.id is not None

    def test_threat_confirm(self) -> None:
        """Test confirming a threat."""
        threat = Threat(
            title="Test Threat",
            threat_type=ThreatType.MALWARE,
        )

        threat.confirm(confidence=0.95)

        assert threat.status == ThreatStatus.CONFIRMED
        assert threat.confidence_score == 0.95

    def test_threat_mitigate(self) -> None:
        """Test mitigating a threat."""
        threat = Threat(
            title="Test Threat",
            threat_type=ThreatType.BRUTE_FORCE,
            source_ip="192.168.1.100",
        )

        threat.mitigate("Blocked source IP in firewall")

        assert threat.status == ThreatStatus.MITIGATED
        assert "Blocked source IP" in threat.actions_taken[0]
        assert threat.mitigated_at is not None

    def test_threat_false_positive(self) -> None:
        """Test marking threat as false positive."""
        threat = Threat(
            title="Possible Attack",
            threat_type=ThreatType.ANOMALY,
        )

        threat.mark_false_positive("Normal backup process")

        assert threat.status == ThreatStatus.FALSE_POSITIVE

    def test_threat_is_actionable(self) -> None:
        """Test checking if threat is actionable."""
        threat = Threat(
            title="Active Threat",
            threat_type=ThreatType.DDOS,
        )

        assert threat.is_actionable() is True

        threat.mitigate("Rate limiting applied")
        assert threat.is_actionable() is False

    def test_threat_is_critical(self) -> None:
        """Test checking if threat is critical."""
        threat = Threat(
            title="Critical Threat",
            threat_type=ThreatType.RANSOMWARE,
            severity=ThreatSeverity.CRITICAL,
        )

        assert threat.is_critical() is True

        threat.severity = ThreatSeverity.LOW
        assert threat.is_critical() is False

    def test_threat_equality_by_id(self) -> None:
        """Test that threats are equal if they have the same ID."""
        threat_id = uuid4()

        threat1 = Threat(id=threat_id, title="Threat 1", threat_type=ThreatType.MALWARE)
        threat2 = Threat(id=threat_id, title="Threat 2", threat_type=ThreatType.DDOS)

        assert threat1 == threat2  # Same ID = equal


class TestAssetEntity:
    """Tests for Asset entity."""

    def test_create_asset(self) -> None:
        """Test creating an asset."""
        asset = Asset(
            name="Web Server",
            hostname="web-01",
            ip_address="10.0.0.5",
            asset_type=AssetType.SERVER,
        )

        assert asset.name == "Web Server"
        assert asset.ip_address == "10.0.0.5"
        assert asset.asset_type == AssetType.SERVER

    def test_asset_discover_service(self) -> None:
        """Test discovering a service on an asset."""
        asset = Asset(name="Test Server")

        asset.discover_service(port=80, service_name="HTTP")
        asset.discover_service(port=443, service_name="HTTPS")

        assert 80 in asset.open_ports
        assert 443 in asset.open_ports
        assert "HTTP" in asset.services
        assert "HTTPS" in asset.services

    def test_asset_mark_as_attacked(self) -> None:
        """Test marking asset as under attack."""
        asset = Asset(name="Target Server")

        asset.mark_as_attacked()

        assert asset.status == AssetStatus.UNDER_ATTACK

    def test_asset_is_critical(self) -> None:
        """Test checking if asset is critical."""
        asset = Asset(name="DB Server", criticality=5)
        assert asset.is_critical_asset() is True

        asset.criticality = 2
        assert asset.is_critical_asset() is False
