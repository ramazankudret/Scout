"""
Domain Entities Base Classes.

Contains base entity and aggregate root classes following DDD patterns.
"""

from abc import ABC
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class Entity(BaseModel, ABC):
    """
    Base class for all domain entities.

    Entities have identity (id) that persists across changes.
    Two entities with the same id are considered equal.
    """

    model_config = ConfigDict(
        frozen=False,  # Entities can be mutated
        use_enum_values=True,
        validate_assignment=True,
    )

    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Entity):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    def update_timestamp(self) -> None:
        """Update the updated_at timestamp."""
        object.__setattr__(self, "updated_at", datetime.utcnow())


class AggregateRoot(Entity, ABC):
    """
    Base class for aggregate roots.

    Aggregate roots are the entry points to clusters of domain objects.
    They ensure consistency boundaries and can emit domain events.
    """

    _domain_events: list[Any] = []

    def add_domain_event(self, event: Any) -> None:
        """Add a domain event to be dispatched after persistence."""
        self._domain_events.append(event)

    def clear_domain_events(self) -> list[Any]:
        """Clear and return all pending domain events."""
        events = self._domain_events.copy()
        self._domain_events = []
        return events


class ValueObject(BaseModel, ABC):
    """
    Base class for value objects.

    Value objects are compared by their attributes, not identity.
    They should be immutable (frozen=True).
    """

    model_config = ConfigDict(
        frozen=True,  # Value objects are immutable
        use_enum_values=True,
    )
