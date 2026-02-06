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
from scout.infrastructure.database import get_db
from scout.infrastructure.api.v1.auth import get_current_user_optional
from scout.infrastructure.database import User
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

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
    db: AsyncSession = Depends(get_db),
    current_user: Annotated[User | None, Depends(get_current_user_optional)] = None,
) -> ExecuteModuleResponse:
    """
    Execute a specific module.

    The module will run with the specified mode and configuration.
    """
    try:
        from uuid import UUID
        from scout.infrastructure.repositories import AssetRepository, ScanResultRepository, TrafficRepository

        DEMO_USER_ID = UUID("00000000-0000-0000-0000-000000000001")
        user_id = current_user.id if current_user else DEMO_USER_ID
        context = ExecutionContext(
            mode=request.mode,
            config=request.config,
            asset_repo=AssetRepository(db),
            traffic_repo=TrafficRepository(db),
            scan_result_repo=ScanResultRepository(db),
            user_id=user_id,
        )
        result = await module_registry.execute(module_name, context)

        return ExecuteModuleResponse(
            module_name=module_name,
            result=result,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Module '{module_name}' not found")
    except Exception as e:
        return ExecuteModuleResponse(
            module_name=module_name,
            result=ModuleResult(
                success=False,
                message="Module execution failed",
                data={"error": str(e)},
                errors=[str(e)],
            ),
        )


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
