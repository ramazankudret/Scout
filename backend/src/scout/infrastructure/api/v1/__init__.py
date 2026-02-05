"""
API v1 Router.

Aggregates all v1 API endpoints.
"""

from fastapi import APIRouter

from scout.infrastructure.api.v1.health import router as health_router
from scout.infrastructure.api.v1.modules import router as modules_router
from scout.infrastructure.api.v1.threats import router as threats_router
from scout.infrastructure.api.v1.logs import router as logs_router
from scout.infrastructure.api.v1.assets import router as assets_router
from scout.infrastructure.api.v1.incidents import router as incidents_router
from scout.infrastructure.api.v1.auth import router as auth_router
from scout.infrastructure.api.v1.llm import router as llm_router
from scout.infrastructure.api.v1.approvals import router as approvals_router
from scout.infrastructure.api.v1.websocket import router as websocket_router
from scout.infrastructure.api.v1.models import router as models_router
from scout.infrastructure.api.v1.supervisor import router as supervisor_router

router = APIRouter()

# Include sub-routers
router.include_router(health_router, tags=["Health"])
router.include_router(modules_router, prefix="/modules", tags=["Modules"])
router.include_router(threats_router, prefix="/threats", tags=["Threats"])
router.include_router(logs_router, prefix="/logs", tags=["Logs"])
router.include_router(assets_router, tags=["Assets"])
router.include_router(incidents_router, tags=["Incidents"])
router.include_router(auth_router, tags=["Auth"])
router.include_router(llm_router, prefix="/llm", tags=["LLM"])
router.include_router(approvals_router, prefix="/approvals", tags=["Approvals"])
router.include_router(websocket_router, tags=["WebSocket"])
router.include_router(models_router, tags=["Models"])
router.include_router(supervisor_router, tags=["Supervisor"])
