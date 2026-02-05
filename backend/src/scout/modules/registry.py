"""
Module Registry.

Central registry for discovering, loading, and managing modules.
"""

from typing import Any

from scout.core.logging import get_logger
from scout.modules.base import BaseModule, ExecutionContext, ModuleMode, ModuleResult

logger = get_logger(__name__)


class ModuleRegistry:
    """
    Singleton registry for all Scout modules.

    Usage:
        registry = ModuleRegistry()
        registry.register(MyModule())
        result = await registry.execute("my_module", context)
    """

    _instance: "ModuleRegistry | None" = None
    _modules: dict[str, BaseModule]

    def __new__(cls) -> "ModuleRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._modules = {}
        return cls._instance

    def register(self, module: BaseModule) -> None:
        """
        Register a module.

        Args:
            module: Module instance to register

        Raises:
            ValueError: If module with same name already registered
        """
        if module.name in self._modules:
            logger.warning(
                "module_already_registered",
                module_name=module.name,
                action="replacing",
            )
        self._modules[module.name] = module
        logger.info("module_registered", module_name=module.name, version=module.version)

    def unregister(self, module_name: str) -> bool:
        """
        Unregister a module.

        Returns:
            True if module was removed, False if not found
        """
        if module_name in self._modules:
            del self._modules[module_name]
            logger.info("module_unregistered", module_name=module_name)
            return True
        return False

    def get(self, module_name: str) -> BaseModule:
        """
        Get a module by name.

        Raises:
            KeyError: If module not found
        """
        if module_name not in self._modules:
            raise KeyError(f"Module '{module_name}' not found")
        return self._modules[module_name]

    def get_all(self) -> list[BaseModule]:
        """Get all registered modules."""
        return list(self._modules.values())

    def list_modules(self) -> list[dict[str, Any]]:
        """Get information about all registered modules."""
        return [module.get_info() for module in self._modules.values()]

    async def execute(
        self, module_name: str, context: ExecutionContext
    ) -> ModuleResult:
        """
        Execute a module by name.

        Args:
            module_name: Name of the module to execute
            context: Execution context

        Returns:
            ModuleResult from the module

        Raises:
            KeyError: If module not found
        """
        module = self.get(module_name)

        if not module.supports_mode(context.mode):
            return ModuleResult(
                success=False,
                message=f"Module '{module_name}' does not support mode '{context.mode}'",
            )

        logger.info("module_executing", module_name=module_name, mode=context.mode)

        try:
            await module.start(context)
            result = await module.execute(context)
            await module.stop()
            return result
        except Exception as e:
            logger.exception("module_execution_failed", module_name=module_name)
            await module.stop()
            return ModuleResult(
                success=False,
                message=f"Module execution failed: {str(e)}",
                errors=[str(e)],
            )

    async def execute_all(
        self, context: ExecutionContext, mode_filter: ModuleMode | None = None
    ) -> dict[str, ModuleResult]:
        """
        Execute all registered modules (optionally filtered by mode).

        Returns:
            Dictionary mapping module names to their results
        """
        results: dict[str, ModuleResult] = {}

        for module in self._modules.values():
            if mode_filter and not module.supports_mode(mode_filter):
                continue
            results[module.name] = await self.execute(module.name, context)

        return results

    def clear(self) -> None:
        """Clear all registered modules (useful for testing)."""
        self._modules.clear()


# Global registry instance
module_registry = ModuleRegistry()
