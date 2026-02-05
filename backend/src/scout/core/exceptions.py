"""
Scout Core Exceptions
Merkezi hata tanımlamaları - Tüm modüller bu hataları kullanır
"""

from typing import Optional, Dict, Any


class ScoutError(Exception):
    """Base exception for all Scout errors"""
    def __init__(self, message: str, code: str = "SCOUT_ERROR", details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": self.code,
            "message": self.message,
            "details": self.details
        }


# === Agent Errors ===
class AgentError(ScoutError):
    """Base error for agent-related issues"""
    def __init__(self, message: str, agent_name: str, **kwargs):
        super().__init__(message, code="AGENT_ERROR", details={"agent": agent_name, **kwargs})


class AgentTimeoutError(AgentError):
    """Agent took too long to respond"""
    def __init__(self, agent_name: str, timeout_seconds: int):
        super().__init__(f"Agent {agent_name} timed out after {timeout_seconds}s", agent_name, timeout=timeout_seconds)
        self.code = "AGENT_TIMEOUT"


class AgentExecutionError(AgentError):
    """Agent failed during execution"""
    def __init__(self, agent_name: str, reason: str):
        super().__init__(f"Agent {agent_name} failed: {reason}", agent_name, reason=reason)
        self.code = "AGENT_EXECUTION_ERROR"


# === LLM Errors ===
class LLMError(ScoutError):
    """Base error for LLM-related issues"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, code="LLM_ERROR", details=kwargs)


class LLMRateLimitError(LLMError):
    """LLM API rate limit exceeded"""
    def __init__(self, retry_after: Optional[int] = None):
        super().__init__("LLM rate limit exceeded", retry_after=retry_after)
        self.code = "LLM_RATE_LIMIT"


class PromptInjectionDetected(LLMError):
    """Potential prompt injection attack detected"""
    def __init__(self, input_text: str):
        super().__init__("Prompt injection attempt detected", input_preview=input_text[:100])
        self.code = "PROMPT_INJECTION"


# === Network/Scan Errors ===
class NetworkError(ScoutError):
    """Base error for network operations"""
    def __init__(self, message: str, target: str = "", **kwargs):
        super().__init__(message, code="NETWORK_ERROR", details={"target": target, **kwargs})


class ScanError(NetworkError):
    """Error during security scan"""
    def __init__(self, target: str, reason: str):
        super().__init__(f"Scan failed for {target}: {reason}", target, reason=reason)
        self.code = "SCAN_ERROR"


class TargetUnreachable(NetworkError):
    """Target host is unreachable"""
    def __init__(self, target: str):
        super().__init__(f"Target {target} is unreachable", target)
        self.code = "TARGET_UNREACHABLE"


# === Licensing Errors ===
class LicenseError(ScoutError):
    """Base error for licensing issues"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, code="LICENSE_ERROR", details=kwargs)


class FeatureNotAvailable(LicenseError):
    """Feature not available in current subscription tier"""
    def __init__(self, feature: str, required_tier: str, current_tier: str):
        super().__init__(
            f"Feature '{feature}' requires {required_tier} tier (current: {current_tier})",
            feature=feature,
            required_tier=required_tier,
            current_tier=current_tier
        )
        self.code = "FEATURE_NOT_AVAILABLE"


class QuotaExceeded(LicenseError):
    """Usage quota exceeded for current tier"""
    def __init__(self, resource: str, limit: int, used: int):
        super().__init__(
            f"Quota exceeded for {resource}: {used}/{limit}",
            resource=resource,
            limit=limit,
            used=used
        )
        self.code = "QUOTA_EXCEEDED"


# === Validation Errors ===
class ValidationError(ScoutError):
    """Input validation failed"""
    def __init__(self, field: str, reason: str):
        super().__init__(f"Validation failed for '{field}': {reason}", code="VALIDATION_ERROR", details={"field": field, "reason": reason})


# === Security Errors ===
class SecurityError(ScoutError):
    """Security-related error"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, code="SECURITY_ERROR", details=kwargs)


class UnauthorizedAccess(SecurityError):
    """Unauthorized access attempt"""
    def __init__(self, resource: str, user_id: Optional[str] = None):
        super().__init__(f"Unauthorized access to {resource}", resource=resource, user_id=user_id)
        self.code = "UNAUTHORIZED"
