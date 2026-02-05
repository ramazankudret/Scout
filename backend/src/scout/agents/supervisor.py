"""
Supervisor Agent - Agent Monitoring & Self-Healing.

Monitors the health of other agents and performs automatic recovery
when agents fail or become unresponsive.
Supports persistent state storage via SupervisorRepository.
"""

import asyncio
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict, List
from dataclasses import dataclass, field

from scout.core.logger import get_logger
from scout.core.model_router import get_reasoning_model, TaskCategory, get_model_for_task
from scout.infrastructure.database.session import get_db_context
from scout.infrastructure.repositories.supervisor_repository import SupervisorRepository

logger = get_logger("supervisor_agent")


class AgentStatus(str, Enum):
    """Status of an agent."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    RECOVERING = "recovering"
    STOPPED = "stopped"


@dataclass
class AgentHealthRecord:
    """Health record for a single agent."""
    agent_name: str
    status: AgentStatus = AgentStatus.STOPPED
    last_heartbeat: Optional[datetime] = None
    last_error: Optional[str] = None
    consecutive_failures: int = 0
    total_executions: int = 0
    successful_executions: int = 0
    restart_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_executions == 0:
            return 100.0
        return (self.successful_executions / self.total_executions) * 100
    
    @property
    def is_healthy(self) -> bool:
        """Check if agent is healthy."""
        if self.status != AgentStatus.HEALTHY:
            return False
        if self.last_heartbeat is None:
            return False
        # Consider unhealthy if no heartbeat in last 60 seconds
        return datetime.utcnow() - self.last_heartbeat < timedelta(seconds=60)


class SupervisorAgent:
    """
    Supervisor Agent monitors and manages other agents.
    
    Responsibilities:
    - Track agent health status (In-Memory + DB Persistence)
    - Detect agent failures
    - Automatically restart failed agents
    - Escalate critical issues to humans (HITL)
    - Analyze failure patterns with LLM
    """
    
    def __init__(
        self,
        max_restart_attempts: int = 3,
        health_check_interval: int = 30,
        failure_threshold: int = 3,
    ):
        self.max_restart_attempts = max_restart_attempts
        self.health_check_interval = health_check_interval
        self.failure_threshold = failure_threshold
        
        self._agents: Dict[str, AgentHealthRecord] = {}
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None
        
        logger.info(
            "supervisor_initialized",
            max_restart_attempts=max_restart_attempts,
            health_check_interval=health_check_interval,
        )
    
    async def _persist_state(self, agent_name: str, record: AgentHealthRecord) -> None:
        """Helper to persist current agent state to DB."""
        try:
            async with get_db_context() as session:
                repo = SupervisorRepository(session)
                await repo.update_state(
                    agent_name=agent_name,
                    status=record.status.value,
                    last_heartbeat=record.last_heartbeat,
                    last_error=record.last_error,
                    consecutive_failures=record.consecutive_failures,
                    total_executions=record.total_executions,
                    success_rate=record.success_rate,
                    restart_count=record.restart_count
                )
        except Exception as e:
            logger.error("persist_state_failed", agent=agent_name, error=str(e))

    async def _log_execution_history(self, agent_name: str, success: bool, error: Optional[str] = None):
        """Helper to log execution history to DB."""
        try:
            async with get_db_context() as session:
                repo = SupervisorRepository(session)
                await repo.log_execution({
                    "agent_name": agent_name,
                    "start_time": datetime.utcnow(), # Approximate
                    "end_time": datetime.utcnow(),
                    "status": "SUCCESS" if success else "FAILED",
                    "error_details": error
                })
        except Exception as e:
            logger.error("log_history_failed", agent=agent_name, error=str(e))

    async def register_agent(self, agent_name: str) -> None:
        """Register an agent for monitoring."""
        if agent_name not in self._agents:
            self._agents[agent_name] = AgentHealthRecord(agent_name=agent_name)
            logger.info("agent_registered", agent_name=agent_name)
            await self._persist_state(agent_name, self._agents[agent_name])
    
    async def unregister_agent(self, agent_name: str) -> None:
        """Unregister an agent from monitoring."""
        if agent_name in self._agents:
            del self._agents[agent_name]
            logger.info("agent_unregistered", agent_name=agent_name)
            # Potentially mark as Inactive in DB, currently we keep history
    
    async def record_heartbeat(self, agent_name: str) -> None:
        """Record a heartbeat from an agent."""
        if agent_name in self._agents:
            record = self._agents[agent_name]
            record.last_heartbeat = datetime.utcnow()
            record.status = AgentStatus.HEALTHY
            record.consecutive_failures = 0
            
            # Persist periodically or on change? For now, persist on heartbeat to keep DB live
            # To optimize: throttle DB updates
            await self._persist_state(agent_name, record)
    
    async def record_execution(
        self, 
        agent_name: str, 
        success: bool, 
        error: Optional[str] = None
    ) -> None:
        """Record an agent execution result."""
        if agent_name not in self._agents:
            await self.register_agent(agent_name)
        
        record = self._agents[agent_name]
        record.total_executions += 1
        record.last_heartbeat = datetime.utcnow()
        
        if success:
            record.successful_executions += 1
            record.consecutive_failures = 0
            record.status = AgentStatus.HEALTHY
        else:
            record.consecutive_failures += 1
            record.last_error = error
            
            if record.consecutive_failures >= self.failure_threshold:
                record.status = AgentStatus.FAILED
                logger.warning(
                    "agent_failure_threshold_reached",
                    agent_name=agent_name,
                    consecutive_failures=record.consecutive_failures,
                    last_error=error,
                )
            else:
                record.status = AgentStatus.DEGRADED
        
        # Persist state and history
        await self._persist_state(agent_name, record)
        await self._log_execution_history(agent_name, success, error)
    
    def get_agent_status(self, agent_name: str) -> Optional[AgentHealthRecord]:
        """Get the health record for an agent (From Cache)."""
        return self._agents.get(agent_name)
    
    def get_all_statuses(self) -> Dict[str, AgentHealthRecord]:
        """Get health records for all agents."""
        return self._agents.copy()
    
    async def restart_agent(self, agent_name: str) -> bool:
        """
        Attempt to restart a failed agent.
        """
        record = self._agents.get(agent_name)
        if not record:
            logger.error("restart_failed_agent_not_found", agent_name=agent_name)
            return False
        
        if record.restart_count >= self.max_restart_attempts:
            logger.error(
                "max_restart_attempts_exceeded",
                agent_name=agent_name,
                restart_count=record.restart_count,
            )
            await self._escalate_to_human(agent_name, record)
            return False
        
        record.status = AgentStatus.RECOVERING
        record.restart_count += 1
        
        logger.info(
            "agent_restart_initiated",
            agent_name=agent_name,
            attempt=record.restart_count,
        )
        await self._persist_state(agent_name, record)
        
        # TODO: Implement actual agent restart logic (Container restart / Process restart)
        # For simulation:
        
        record.consecutive_failures = 0
        record.status = AgentStatus.HEALTHY
        record.last_heartbeat = datetime.utcnow()
        
        logger.info("agent_restart_successful", agent_name=agent_name)
        
        # Log event
        async with get_db_context() as session:
            repo = SupervisorRepository(session)
            await repo.log_event({
                "event_type": "AUTO_RESTART",
                "target_agent": agent_name,
                "outcome": "SUCCESS",
                "is_automated": True
            })
            await repo.update_state(agent_name, status="healthy", restart_count=record.restart_count)
            
        return True
    
    async def _escalate_to_human(
        self, 
        agent_name: str, 
        record: AgentHealthRecord
    ) -> None:
        """
        Escalate a critical agent failure to human operators via HITL.
        """
        logger.critical(
            "escalating_to_human",
            agent_name=agent_name,
            restart_count=record.restart_count,
            last_error=record.last_error,
            success_rate=record.success_rate,
        )
        
        # Analyze failure with LLM
        analysis = await self._analyze_failure(agent_name, record)
        
        async with get_db_context() as session:
            repo = SupervisorRepository(session)
            await repo.log_event({
                "event_type": "ESCALATION",
                "target_agent": agent_name,
                "trigger_reason": f"Max restarts ({self.max_restart_attempts}) exceeded. Error: {record.last_error}",
                "action_taken": "Sent to HITL",
                "outcome": "PENDING",
                "is_automated": True
            })
        
        logger.info(
            "failure_analysis_complete",
            agent_name=agent_name,
            analysis_preview=analysis[:200] if analysis else None,
        )
    
    async def _analyze_failure(
        self, 
        agent_name: str, 
        record: AgentHealthRecord
    ) -> str:
        """
        Use LLM to analyze the failure pattern and suggest remediation.
        """
        try:
            llm = get_reasoning_model()
            
            prompt = f"""Analyze this agent failure and suggest remediation:

Agent: {agent_name}
Status: {record.status.value}
Consecutive Failures: {record.consecutive_failures}
Total Executions: {record.total_executions}
Success Rate: {record.success_rate:.1f}%
Restart Attempts: {record.restart_count}
Last Error: {record.last_error or 'Unknown'}

Please analyze:
1. What is the likely root cause?
2. Is this a transient or systemic issue?
3. What remediation steps should be taken?
4. Should this be escalated to human operators?
"""
            
            response = await llm.ainvoke(prompt)
            return response.content
            
        except Exception as e:
            logger.error("failure_analysis_error", error=str(e))
            return f"Analysis failed: {str(e)}"
    
    async def _health_check_loop(self) -> None:
        """Background loop for periodic health checks."""
        while self._running:
            await asyncio.sleep(self.health_check_interval)
            
            for agent_name, record in self._agents.items():
                if record.last_heartbeat:
                    time_since_heartbeat = datetime.utcnow() - record.last_heartbeat
                    
                    if time_since_heartbeat > timedelta(seconds=60):
                        if record.status == AgentStatus.HEALTHY:
                            record.status = AgentStatus.DEGRADED
                            await self._persist_state(agent_name, record)
                    
                    if time_since_heartbeat > timedelta(seconds=120):
                        if record.status != AgentStatus.FAILED:
                            record.status = AgentStatus.FAILED
                            await self._persist_state(agent_name, record)
                            await self.restart_agent(agent_name)
    
    async def start(self) -> None:
        """Start the supervisor monitoring loop and load state."""
        if self._running:
            return
        
        # Load state from DB
        try:
            async with get_db_context() as session:
                repo = SupervisorRepository(session)
                states = await repo.get_all_states()
                for state in states:
                    self._agents[state.agent_name] = AgentHealthRecord(
                        agent_name=state.agent_name,
                        status=AgentStatus(state.status) if state.status else AgentStatus.STOPPED,
                        last_heartbeat=state.last_heartbeat.replace(tzinfo=None) if state.last_heartbeat else None,
                        last_error=state.last_error,
                        consecutive_failures=state.consecutive_failures or 0,
                        total_executions=state.total_executions or 0,
                        restart_count=state.restart_count or 0
                    )
                logger.info("supervisor_state_loaded", count=len(states))
        except Exception as e:
            logger.warning("supervisor_state_load_failed", error=str(e))
        
        self._running = True
        self._monitor_task = asyncio.create_task(self._health_check_loop())
        logger.info("supervisor_started")
    
    async def stop(self) -> None:
        """Stop the supervisor monitoring loop."""
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("supervisor_stopped")
    
    def get_summary(self) -> dict:
        """Get a summary of all agent statuses."""
        summary = {
            "total_agents": len(self._agents),
            "healthy": 0,
            "degraded": 0,
            "failed": 0,
            "recovering": 0,
            "stopped": 0,
        }
        
        for record in self._agents.values():
            status_key = record.status.value
            if status_key in summary:
                summary[status_key] += 1
        
        return summary


# Global supervisor instance
supervisor = SupervisorAgent()
