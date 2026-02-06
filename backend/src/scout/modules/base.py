"""
Scout Module (Plugin) System.

This is the extensible module system that allows adding new
security capabilities without modifying core code.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from scout.core.logging import get_logger

logger = get_logger(__name__)


class ModuleMode(str, Enum):
    """Operating mode for modules."""

    PASSIVE = "passive"  # Only observe, never act
    ACTIVE = "active"  # Can take actions
    SIMULATION = "simulation"  # Simulate actions without executing


class ModuleStatus(str, Enum):
    """Module lifecycle status."""

    IDLE = "idle"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class ExecutionContext(BaseModel):
    """
    Context passed to modules during execution.

    Contains shared resources and configuration.
    """

    mode: ModuleMode = ModuleMode.PASSIVE
    config: dict[str, Any] = Field(default_factory=dict)
    start_time: datetime = Field(default_factory=datetime.utcnow)

    # Injected dependencies (set by ModuleRegistry)
    # These are Any to avoid circular imports, but will be typed interfaces
    threat_repo: Any = None
    asset_repo: Any = None
    traffic_repo: Any = None  # Added for Stealth module
    scan_result_repo: Any = None  # For persisting scan results (Hunter, etc.)
    llm_service: Any = None
    event_publisher: Any = None

    # ─────────────────────────────────────────────────────────────────────────
    # HITL (Human-in-the-Loop) Fields
    # ─────────────────────────────────────────────────────────────────────────
    approval_service: Any = None  # ActionApprovalService for requesting approvals
    user_id: UUID | None = None   # User context for approval requests
    require_approval: bool = True  # Whether to require approval for destructive actions


class ModuleResult(BaseModel):
    """
    Result returned from module execution.

    Standardized format for all module outputs.
    """

    success: bool = True
    message: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
    execution_time_ms: float | None = None


class BaseModule(ABC):
    """
    Abstract base class for all Scout modules.

    To create a new module:
    1. Inherit from BaseModule
    2. Set name, description, version
    3. Implement execute() method
    4. Register with ModuleRegistry
    """

    # Module metadata (override in subclass)
    name: str = "base_module"
    description: str = "Base module"
    version: str = "0.1.0"
    supported_modes: list[ModuleMode] = [ModuleMode.PASSIVE, ModuleMode.ACTIVE]

    def __init__(self) -> None:
        self.status = ModuleStatus.IDLE
        self._logger = get_logger(f"module.{self.name}")
        
        # Dashboard metrics
        self.started_at: datetime | None = None
        self.tasks_completed: int = 0
        self.last_action_time: datetime | None = None
        self.current_task: str | None = None

    @abstractmethod
    async def execute(self, context: ExecutionContext) -> ModuleResult:
        """
        Main execution method. Override this in subclasses.
        """
        ...

    async def start(self, context: ExecutionContext) -> None:
        """Called when module starts."""
        self.status = ModuleStatus.STARTING
        self.started_at = datetime.utcnow()
        self._logger.info("module_starting", mode=context.mode)
        self.status = ModuleStatus.RUNNING

    async def stop(self) -> None:
        """Called when module stops."""
        self.status = ModuleStatus.STOPPING
        self._logger.info("module_stopping")
        self.status = ModuleStatus.STOPPED

    def supports_mode(self, mode: ModuleMode) -> bool:
        """Check if module supports a given operating mode."""
        return mode in self.supported_modes

    def get_info(self) -> dict[str, Any]:
        """Get module information."""
        uptime_str = "0m"
        if self.started_at:
            delta = datetime.utcnow() - self.started_at
            hours, remainder = divmod(int(delta.total_seconds()), 3600)
            minutes, _ = divmod(remainder, 60)
            if hours > 0:
                uptime_str = f"{hours}h {minutes}m"
            else:
                uptime_str = f"{minutes}m"
        
        last_action_str = "Never"
        if self.last_action_time:
            delta = datetime.utcnow() - self.last_action_time
            if delta.total_seconds() < 60:
                last_action_str = "Just now"
            elif delta.total_seconds() < 3600:
                last_action_str = f"{int(delta.total_seconds() // 60)}m ago"
            else:
                last_action_str = f"{int(delta.total_seconds() // 3600)}h ago"

        return {
            "id": self.name,
            "name": self.name.replace("_", " ").title(),
            "description": self.description,
            "version": self.version,
            "status": self.status.value,
            "supported_modes": [m.value for m in self.supported_modes],
            # Metrics
            "currentTask": self.current_task,
            "tasksCompleted": self.tasks_completed,
            "lastAction": last_action_str,
            "uptime": uptime_str,
        }
