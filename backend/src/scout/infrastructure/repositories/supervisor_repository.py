"""
Supervisor Repository Implementation.

Implements ISupervisorRepository interface for data persistence.
Handles SupervisorState, AgentExecutionHistory, SupervisorEvent, and AgentMetric.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import uuid4

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from scout.domain.interfaces.repositories import ISupervisorRepository
from scout.infrastructure.database.models import (
    SupervisorState,
    AgentExecutionHistory,
    SupervisorEvent,
    AgentMetric
)


class SupervisorRepository(ISupervisorRepository):
    """
    Repository for managing Supervisor data.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        
    async def get_state(self, agent_name: str) -> Optional[SupervisorState]:
        """Get current state of an agent."""
        return await self.session.get(SupervisorState, agent_name)
        
    async def update_state(self, agent_name: str, **kwargs) -> SupervisorState:
        """
        Update agent state. Creates if not exists.
        """
        state = await self.get_state(agent_name)
        
        if not state:
            state = SupervisorState(agent_name=agent_name, **kwargs)
            self.session.add(state)
        else:
            for key, value in kwargs.items():
                if hasattr(state, key):
                    setattr(state, key, value)
            # Always update timestamp
            # (handled by onupdate in model mixin, but good to be explicit for manual updates)
            pass
            
        await self.session.flush()
        await self.session.refresh(state)
        return state
        
    async def log_execution(self, execution_data: Dict[str, Any]) -> AgentExecutionHistory:
        """Log a new execution entry."""
        entry = AgentExecutionHistory(**execution_data)
        if not entry.id:
            entry.id = uuid4()
            
        self.session.add(entry)
        await self.session.flush()
        await self.session.refresh(entry)
        return entry
        
    async def log_event(self, event_data: Dict[str, Any]) -> SupervisorEvent:
        """Log a supervisor event."""
        event = SupervisorEvent(**event_data)
        if not event.id:
            event.id = uuid4()
            
        self.session.add(event)
        await self.session.flush()
        await self.session.refresh(event)
        return event
        
    async def get_all_states(self) -> List[SupervisorState]:
        """Get states of all agents."""
        query = select(SupervisorState)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    # --- Extended Methods ---

    async def get_execution_history(
        self, 
        agent_name: str, 
        limit: int = 10, 
        offset: int = 0
    ) -> List[AgentExecutionHistory]:
        """Get execution history for an agent."""
        query = (
            select(AgentExecutionHistory)
            .where(AgentExecutionHistory.agent_name == agent_name)
            .order_by(desc(AgentExecutionHistory.start_time))
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def log_metric(self, metric_data: Dict[str, Any]) -> AgentMetric:
        """Log a performance metric."""
        metric = AgentMetric(**metric_data)
        self.session.add(metric)
        await self.session.flush()
        return metric

    async def get_recent_events(
        self,
        limit: int = 20,
        event_types: Optional[List[str]] = None,
    ) -> List[SupervisorEvent]:
        """Get recent supervisor events (ESCALATION, AUTO_RESTART, etc.)."""
        query = (
            select(SupervisorEvent)
            .order_by(desc(SupervisorEvent.timestamp))
            .limit(limit)
        )
        if event_types:
            query = query.where(SupervisorEvent.event_type.in_(event_types))
        result = await self.session.execute(query)
        return list(result.scalars().all())
