"""
Domain Interfaces (Ports).

These abstract classes define the "ports" in Hexagonal Architecture.
Infrastructure layer provides concrete "adapters" that implement these.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from uuid import UUID

from scout.domain.entities.base import Entity

# Generic type for entities
T = TypeVar("T", bound=Entity)


class Repository(ABC, Generic[T]):
    """
    Base repository interface for all entities.

    Repositories abstract data persistence. Domain layer uses this interface,
    infrastructure layer provides the implementation (PostgreSQL, MongoDB, etc.).
    """

    @abstractmethod
    async def get_by_id(self, entity_id: UUID) -> T | None:
        """Get an entity by its ID."""
        ...

    @abstractmethod
    async def save(self, entity: T) -> T:
        """Save (create or update) an entity."""
        ...

    @abstractmethod
    async def delete(self, entity_id: UUID) -> bool:
        """Delete an entity by its ID."""
        ...

    @abstractmethod
    async def list_all(self, limit: int = 100, offset: int = 0) -> list[T]:
        """List all entities with pagination."""
        ...


class IThreatRepository(Repository["Threat"], ABC):
    """
    Repository interface for Threat entities.

    Extends base Repository with threat-specific queries.
    """

    @abstractmethod
    async def find_by_status(self, status: str) -> list["Threat"]:
        """Find threats by status."""
        ...

    @abstractmethod
    async def find_by_source_ip(self, source_ip: str) -> list["Threat"]:
        """Find threats by source IP address."""
        ...

    @abstractmethod
    async def find_active_threats(self) -> list["Threat"]:
        """Find all active (non-mitigated) threats."""
        ...

    @abstractmethod
    async def count_by_severity(self) -> dict[str, int]:
        """Count threats grouped by severity."""
        ...


class IAssetRepository(Repository["Asset"], ABC):
    """
    Repository interface for Asset entities.

    Extends base Repository with asset-specific queries.
    """

    @abstractmethod
    async def find_by_ip(self, ip_address: str) -> "Asset | None":
        """Find an asset by IP address."""
        ...

    @abstractmethod
    async def find_by_status(self, status: str) -> list["Asset"]:
        """Find assets by status."""
        ...

    @abstractmethod
    async def find_critical_assets(self) -> list["Asset"]:
        """Find all assets with criticality >= 4."""
        ...


class ILLMService(ABC):
    """
    Interface for LLM (Large Language Model) service.

    Abstracts the AI/ML backend for threat analysis.
    """

    @abstractmethod
    async def analyze_threat(
        self, threat_data: dict, context: str | None = None
    ) -> dict:
        """
        Analyze a potential threat using LLM.

        Returns analysis including severity suggestion, recommendations, etc.
        """
        ...

    @abstractmethod
    async def summarize_activity(
        self, events: list[dict], timeframe: str
    ) -> str:
        """
        Generate a human-readable summary of security events.
        """
        ...

    @abstractmethod
    async def generate_response_plan(
        self, threat_type: str, severity: str
    ) -> list[str]:
        """
        Generate a list of recommended response actions.
        """
        ...


class INetworkService(ABC):
    """
    Interface for network operations.

    Abstracts network scanning, packet capture, etc.
    """

    @abstractmethod
    async def start_capture(self, interface: str) -> None:
        """Start capturing network traffic on an interface."""
        ...

    @abstractmethod
    async def stop_capture(self) -> None:
        """Stop the current capture session."""
        ...

    @abstractmethod
    async def get_captured_packets(self, limit: int = 100) -> list[dict]:
        """Get captured packets."""
        ...

    @abstractmethod
    async def scan_port(self, target_ip: str, port: int) -> bool:
        """Check if a specific port is open on target."""
        ...


class IEventPublisher(ABC):
    """
    Interface for publishing domain events.

    Enables loose coupling between modules through events.
    """

    @abstractmethod
    async def publish(self, event: "DomainEvent") -> None:
        """Publish a domain event."""
        ...



class ISupervisorRepository(ABC):
    """
    Repository interface for Supervisor State and Events.
    """
    
    @abstractmethod
    async def get_state(self, agent_name: str) -> "SupervisorState | None":
        """Get current state of an agent."""
        ...
        
    @abstractmethod
    async def update_state(self, agent_name: str, **kwargs) -> "SupervisorState":
        """Update agent state."""
        ...
        
    @abstractmethod
    async def log_execution(self, execution_data: dict) -> "AgentExecutionHistory":
        """Log a new execution entry."""
        ...
        
    @abstractmethod
    async def log_event(self, event_data: dict) -> "SupervisorEvent":
        """Log a supervisor event."""
        ...
        
    @abstractmethod
    async def get_all_states(self) -> list["SupervisorState"]:
        """Get states of all agents."""
        ...


class ILearningRepository(Repository["LearnedLesson"], ABC):
    """
    Repository interface for Learned Lessons.
    """
    
    @abstractmethod
    async def find_similar(
        self, 
        embedding: list[float], 
        limit: int = 5, 
        threshold: float = 0.8
    ) -> list["LearnedLesson"]:
        """
        Find semantically similar lessons using vector search.
        Requires pgvector extension.
        """
        ...
        
    @abstractmethod
    async def find_by_category(self, category: str) -> list["LearnedLesson"]:
        """Find lessons by category."""
        ...
        
    @abstractmethod
    async def find_by_action_type(self, action_type: str) -> list["LearnedLesson"]:
        """Get lessons relevant to a specific action type."""
        ...


# Import at the end to avoid circular imports
from scout.domain.entities.threat import Threat  # noqa: E402
from scout.domain.entities.asset import Asset  # noqa: E402
from scout.domain.events.base import DomainEvent  # noqa: E402
# Type hints only
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from scout.infrastructure.database.models import (
        LearnedLesson, SupervisorState, AgentExecutionHistory, SupervisorEvent
    )
