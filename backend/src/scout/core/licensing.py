"""
Scout Licensing System
Abonelik seviyeleri ve özellik erişim kontrolü
"""

from enum import Enum
from typing import Dict, List, Optional, Set
from functools import wraps
from scout.core.exceptions import FeatureNotAvailable, QuotaExceeded
from scout.core.logger import get_logger

logger = get_logger(__name__)


class SubscriptionTier(str, Enum):
    """Available subscription tiers"""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"
    ULTIMATE = "ultimate"


# Feature definitions per tier
TIER_FEATURES: Dict[SubscriptionTier, Set[str]] = {
    SubscriptionTier.FREE: {
        "basic_scan",
        "dashboard_view",
        "hunter_agent",
    },
    SubscriptionTier.PRO: {
        "basic_scan",
        "dashboard_view",
        "hunter_agent",
        "stealth_agent",
        "defense_agent",
        "llm_guard",
        "api_access",
        "export_reports",
    },
    SubscriptionTier.ENTERPRISE: {
        "basic_scan",
        "dashboard_view",
        "hunter_agent",
        "stealth_agent",
        "defense_agent",
        "llm_guard",
        "api_access",
        "export_reports",
        "ai_pentest",
        "endpoint_security",
        "custom_integrations",
        "priority_support",
    },
    SubscriptionTier.ULTIMATE: {
        "*"  # All features
    }
}

# Quota limits per tier
TIER_QUOTAS: Dict[SubscriptionTier, Dict[str, int]] = {
    SubscriptionTier.FREE: {
        "daily_scans": 10,
        "max_targets": 5,
        "max_agents": 1,
        "api_calls_per_hour": 100,
    },
    SubscriptionTier.PRO: {
        "daily_scans": 100,
        "max_targets": 50,
        "max_agents": 3,
        "api_calls_per_hour": 1000,
    },
    SubscriptionTier.ENTERPRISE: {
        "daily_scans": 1000,
        "max_targets": 500,
        "max_agents": 10,
        "api_calls_per_hour": 10000,
    },
    SubscriptionTier.ULTIMATE: {
        "daily_scans": -1,  # Unlimited
        "max_targets": -1,
        "max_agents": -1,
        "api_calls_per_hour": -1,
    }
}


class LicenseManager:
    """
    Manages license validation and feature access.
    In production, this would connect to a license server.
    """
    
    def __init__(self):
        # Default to FREE tier for development
        self._current_tier = SubscriptionTier.FREE
        self._usage: Dict[str, int] = {}
    
    @property
    def current_tier(self) -> SubscriptionTier:
        return self._current_tier
    
    def set_tier(self, tier: SubscriptionTier):
        """Set the current subscription tier"""
        self._current_tier = tier
        logger.info("Subscription tier changed", tier=tier.value)
    
    def has_feature(self, feature: str) -> bool:
        """Check if current tier has access to a feature"""
        tier_features = TIER_FEATURES.get(self._current_tier, set())
        return "*" in tier_features or feature in tier_features
    
    def check_feature(self, feature: str) -> None:
        """Raise exception if feature not available"""
        if not self.has_feature(feature):
            # Find minimum required tier
            required_tier = "ULTIMATE"
            for tier in SubscriptionTier:
                if feature in TIER_FEATURES.get(tier, set()):
                    required_tier = tier.value
                    break
            
            raise FeatureNotAvailable(
                feature=feature,
                required_tier=required_tier,
                current_tier=self._current_tier.value
            )
    
    def get_quota(self, resource: str) -> int:
        """Get quota limit for a resource"""
        return TIER_QUOTAS.get(self._current_tier, {}).get(resource, 0)
    
    def check_quota(self, resource: str, current_usage: int) -> None:
        """Check if quota is exceeded"""
        limit = self.get_quota(resource)
        if limit != -1 and current_usage >= limit:
            raise QuotaExceeded(resource=resource, limit=limit, used=current_usage)
    
    def get_tier_info(self) -> Dict:
        """Get current tier information for UI display"""
        return {
            "tier": self._current_tier.value,
            "features": list(TIER_FEATURES.get(self._current_tier, set())),
            "quotas": TIER_QUOTAS.get(self._current_tier, {})
        }


# Global license manager instance
license_manager = LicenseManager()


def require_feature(feature: str):
    """
    Decorator to require a specific feature for a function.
    
    Usage:
        @require_feature("ai_pentest")
        async def run_ai_pentest():
            ...
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            license_manager.check_feature(feature)
            return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            license_manager.check_feature(feature)
            return func(*args, **kwargs)
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def require_tier(min_tier: SubscriptionTier):
    """
    Decorator to require a minimum subscription tier.
    
    Usage:
        @require_tier(SubscriptionTier.PRO)
        def premium_function():
            ...
    """
    tier_order = [SubscriptionTier.FREE, SubscriptionTier.PRO, SubscriptionTier.ENTERPRISE, SubscriptionTier.ULTIMATE]
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_idx = tier_order.index(license_manager.current_tier)
            required_idx = tier_order.index(min_tier)
            
            if current_idx < required_idx:
                raise FeatureNotAvailable(
                    feature=func.__name__,
                    required_tier=min_tier.value,
                    current_tier=license_manager.current_tier.value
                )
            
            return func(*args, **kwargs)
        return wrapper
    return decorator
