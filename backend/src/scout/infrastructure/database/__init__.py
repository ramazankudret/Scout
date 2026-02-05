"""
Scout Database Infrastructure Module
"""
from scout.infrastructure.database.session import (
    engine,
    async_session_factory,
    get_db,
    get_db_context,
    init_db,
    close_db,
)
from scout.infrastructure.database.models import (
    Base,
    User,
    Subscription,
    Asset,
    Incident,
    ScanResult,
    Vulnerability,
    AgentRun,
    AgentMemory,
    LearnedLesson,
    DefenseRule,
    Notification,
    AuditLog,
    LlmLog,
    ApiKey,
    Session,
    SupervisorState,
    AgentExecutionHistory,
    SupervisorEvent,
    AgentMetric,
)

__all__ = [
    # Session management
    "engine",
    "async_session_factory",
    "get_db",
    "get_db_context",
    "init_db",
    "close_db",
    # Models
    "Base",
    "User",
    "Subscription",
    "Asset",
    "Incident",
    "ScanResult",
    "Vulnerability",
    "AgentRun",
    "AgentMemory",
    "LearnedLesson",
    "DefenseRule",
    "Notification",
    "AuditLog",
    "LlmLog",
    "ApiKey",
    "Session",
    "SupervisorState",
    "AgentExecutionHistory",
    "SupervisorEvent",
    "AgentMetric",
]
