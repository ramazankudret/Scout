"""
Unit Tests for Module System.
"""

import pytest

from scout.core.exceptions import ModuleNotFoundError
from scout.modules import (
    BaseModule,
    ExecutionContext,
    ModuleMode,
    ModuleRegistry,
    ModuleResult,
)


class DummyModule(BaseModule):
    """A simple test module."""

    name = "dummy"
    description = "A dummy module for testing"
    version = "1.0.0"
    supported_modes = [ModuleMode.PASSIVE, ModuleMode.ACTIVE]

    async def execute(self, context: ExecutionContext) -> ModuleResult:
        return ModuleResult(
            success=True,
            message="Dummy execution complete",
            data={"mode": context.mode.value},
        )


class TestModuleRegistry:
    """Tests for ModuleRegistry."""

    @pytest.fixture
    def registry(self) -> ModuleRegistry:
        """Create a fresh registry for each test."""
        reg = ModuleRegistry()
        reg.clear()
        return reg

    def test_register_module(self, registry: ModuleRegistry) -> None:
        """Test registering a module."""
        module = DummyModule()
        registry.register(module)

        assert "dummy" in [m["name"] for m in registry.list_modules()]

    def test_get_module(self, registry: ModuleRegistry) -> None:
        """Test getting a registered module."""
        module = DummyModule()
        registry.register(module)

        retrieved = registry.get("dummy")
        assert retrieved.name == "dummy"

    def test_get_nonexistent_module(self, registry: ModuleRegistry) -> None:
        """Test getting a module that doesn't exist."""
        with pytest.raises(ModuleNotFoundError):
            registry.get("nonexistent")

    def test_unregister_module(self, registry: ModuleRegistry) -> None:
        """Test unregistering a module."""
        module = DummyModule()
        registry.register(module)

        result = registry.unregister("dummy")
        assert result is True

        with pytest.raises(ModuleNotFoundError):
            registry.get("dummy")

    def test_list_modules(self, registry: ModuleRegistry) -> None:
        """Test listing all modules."""
        registry.register(DummyModule())

        modules = registry.list_modules()
        assert len(modules) == 1
        assert modules[0]["name"] == "dummy"

    @pytest.mark.asyncio
    async def test_execute_module(self, registry: ModuleRegistry) -> None:
        """Test executing a module."""
        registry.register(DummyModule())

        context = ExecutionContext(mode=ModuleMode.PASSIVE)
        result = await registry.execute("dummy", context)

        assert result.success is True
        assert result.data["mode"] == "passive"

    @pytest.mark.asyncio
    async def test_execute_unsupported_mode(self, registry: ModuleRegistry) -> None:
        """Test executing a module with unsupported mode."""

        class LimitedModule(BaseModule):
            name = "limited"
            description = "Only passive"
            version = "1.0.0"
            supported_modes = [ModuleMode.PASSIVE]

            async def execute(self, context: ExecutionContext) -> ModuleResult:
                return ModuleResult(success=True)

        registry.register(LimitedModule())

        context = ExecutionContext(mode=ModuleMode.SIMULATION)
        result = await registry.execute("limited", context)

        assert result.success is False
        assert "does not support mode" in result.message


class TestBaseModule:
    """Tests for BaseModule."""

    def test_module_info(self) -> None:
        """Test getting module info."""
        module = DummyModule()
        info = module.get_info()

        assert info["name"] == "dummy"
        assert info["version"] == "1.0.0"
        assert "passive" in info["supported_modes"]

    def test_supports_mode(self) -> None:
        """Test checking mode support."""
        module = DummyModule()

        assert module.supports_mode(ModuleMode.PASSIVE) is True
        assert module.supports_mode(ModuleMode.ACTIVE) is True
        assert module.supports_mode(ModuleMode.SIMULATION) is False
