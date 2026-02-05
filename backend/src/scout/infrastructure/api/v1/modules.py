"""
Modules API Endpoints.

Endpoints for managing and executing Scout modules.
"""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from scout.modules import (
    ExecutionContext,
    ModuleMode,
    ModuleResult,
    module_registry,
)

router = APIRouter()


class ExecuteModuleRequest(BaseModel):
    """Request body for module execution."""

    mode: ModuleMode = ModuleMode.PASSIVE
    config: dict[str, Any] = {}


class ExecuteModuleResponse(BaseModel):
    """Response from module execution."""

    module_name: str
    result: ModuleResult


@router.get("")
async def list_modules() -> dict[str, Any]:
    """
    List all registered modules.

    Returns module names, descriptions, and status.
    """
    modules = module_registry.list_modules()
    return {
        "count": len(modules),
        "modules": modules,
    }


@router.get("/{module_name}")
async def get_module(module_name: str) -> dict[str, Any]:
    """
    Get information about a specific module.
    """
    try:
        module = module_registry.get(module_name)
        return module.get_info()
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Module '{module_name}' not found")


@router.post("/{module_name}/execute")
async def execute_module(
    module_name: str,
    request: ExecuteModuleRequest,
) -> ExecuteModuleResponse:
    """
    Execute a specific module.

    The module will run with the specified mode and configuration.
    """
    try:
        context = ExecutionContext(
            mode=request.mode,
            config=request.config,
        )
        result = await module_registry.execute(module_name, context)

        return ExecuteModuleResponse(
            module_name=module_name,
            result=result,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Module '{module_name}' not found")


@router.post("/execute-all")
async def execute_all_modules(
    request: ExecuteModuleRequest,
) -> dict[str, ModuleResult]:
    """
    Execute all registered modules.

    Returns results from all modules.
    """
    context = ExecutionContext(
        mode=request.mode,
        config=request.config,
    )
    results = await module_registry.execute_all(context, mode_filter=request.mode)
    return results
