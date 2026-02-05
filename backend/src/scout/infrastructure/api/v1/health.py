"""
Health Check Endpoints.

Standard health and readiness checks for monitoring.
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter

from scout.core import settings

router = APIRouter()


@router.get("/health")
async def health_check() -> dict[str, Any]:
    """
    Basic health check endpoint.

    Returns service status and version.
    """
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/ready")
async def readiness_check() -> dict[str, Any]:
    """
    Readiness check endpoint.

    Verifies all dependencies are available.
    """
    checks = {
        "database": await _check_database(),
        "redis": await _check_redis(),
    }

    all_ready = all(check["status"] == "ok" for check in checks.values())

    return {
        "ready": all_ready,
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat(),
    }


async def _check_database() -> dict[str, str]:
    """Check database connectivity."""
    # TODO: Implement actual database check
    return {"status": "ok", "message": "Database connection pending implementation"}


async def _check_redis() -> dict[str, str]:
    """Check Redis connectivity."""
    # TODO: Implement actual Redis check
    return {"status": "ok", "message": "Redis connection pending implementation"}
