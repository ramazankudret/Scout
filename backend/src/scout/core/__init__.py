"""
Scout Core Module Exports
"""

from scout.core.config import settings
from scout.core.exceptions import (
    ScoutError,
    AgentError,
    AgentTimeoutError,
    AgentExecutionError,
    LLMError,
    LLMRateLimitError,
    PromptInjectionDetected,
    NetworkError,
    ScanError,
    TargetUnreachable,
    LicenseError,
    FeatureNotAvailable,
    QuotaExceeded,
    ValidationError,
    SecurityError,
    UnauthorizedAccess,
)
from scout.core.logger import setup_logging, get_logger, LoggerFactory
from scout.core.error_handler import safe_execute, error_collector
from scout.core.licensing import (
    SubscriptionTier,
    license_manager,
    require_feature,
    require_tier,
)
from scout.core.state import AgentState
from scout.core.model_router import (
    ModelRouter,
    ModelType,
    TaskCategory,
    model_router,
    get_fast_model,
    get_reasoning_model,
    get_default_model,
    get_model_for_task,
)

__all__ = [
    # Config
    "settings",
    # Exceptions
    "ScoutError",
    "AgentError",
    "AgentTimeoutError",
    "AgentExecutionError",
    "LLMError",
    "LLMRateLimitError",
    "PromptInjectionDetected",
    "NetworkError",
    "ScanError",
    "TargetUnreachable",
    "LicenseError",
    "FeatureNotAvailable",
    "QuotaExceeded",
    "ValidationError",
    "SecurityError",
    "UnauthorizedAccess",
    # Logging
    "setup_logging",
    "get_logger",
    "LoggerFactory",
    # Error Handling
    "safe_execute",
    "error_collector",
    # Licensing
    "SubscriptionTier",
    "license_manager",
    "require_feature",
    "require_tier",
    # State
    "AgentState",
    # Model Router
    "ModelRouter",
    "ModelType",
    "TaskCategory",
    "model_router",
    "get_fast_model",
    "get_reasoning_model",
    "get_default_model",
    "get_model_for_task",
]
