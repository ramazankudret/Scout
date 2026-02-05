"""Scout Modules Package."""

from scout.modules.base import (
    BaseModule,
    ExecutionContext,
    ModuleMode,
    ModuleResult,
    ModuleStatus,
)
from scout.modules.defense import DefenseModule
from scout.modules.hunter import HunterModule
from scout.modules.registry import ModuleRegistry, module_registry
from scout.modules.stealth import StealthModule

__all__ = [
    # Base
    "BaseModule",
    "ExecutionContext",
    "ModuleMode",
    "ModuleResult",
    "ModuleStatus",
    # Registry
    "ModuleRegistry",
    "module_registry",
    # Modules
    "StealthModule",
    "DefenseModule",
    "HunterModule",
]


def register_default_modules() -> None:
    """Register all default modules with the global registry."""
    module_registry.register(StealthModule())
    module_registry.register(DefenseModule())
    module_registry.register(HunterModule())
