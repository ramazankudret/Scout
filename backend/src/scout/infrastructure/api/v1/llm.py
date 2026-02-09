"""
LLM API Endpoints.

Provides endpoints for testing and using the local LLM (Ollama).
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from scout.application.services.llm_context_builder import build_llm_context
from scout.application.services.log_preprocessor import preprocess as preprocess_logs
from scout.core.config import get_settings
from scout.core.logging import get_logger
from scout.infrastructure.api.v1.auth import get_current_user_optional
from scout.infrastructure.database import get_db
from scout.infrastructure.database import User
from scout.infrastructure.llm import OllamaService

router = APIRouter()
logger = get_logger(__name__)

# Lazy initialization of LLM service
_llm_service: OllamaService | None = None


def get_llm_service() -> OllamaService:
    """Get or create the LLM service instance."""
    global _llm_service
    if _llm_service is None:
        _llm_service = OllamaService()
    return _llm_service


# === Request/Response Models ===


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""

    message: str = Field(..., min_length=1, max_length=4000)
    system_prompt: str | None = None
    model: str | None = None
    task_hint: str | None = None  # "general" | "analysis" for auto model selection


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""

    response: str
    model: str


class AnalyzeLogsRequest(BaseModel):
    """Request model for log analysis."""

    logs: str = Field(..., min_length=1, max_length=50000)
    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        examples=["Find suspicious login attempts", "Detect port scanning activity"],
    )


class AnalyzeThreatRequest(BaseModel):
    """Request model for threat analysis."""

    threat_data: dict[str, Any] = Field(
        ...,
        examples=[
            {
                "source_ip": "192.168.1.100",
                "destination_ip": "10.0.0.5",
                "port": 22,
                "protocol": "TCP",
                "event_type": "multiple_failed_logins",
                "count": 150,
                "timeframe": "5 minutes",
            }
        ],
    )
    context: str | None = None


class ResponsePlanRequest(BaseModel):
    """Request model for response plan generation."""

    threat_type: str = Field(..., examples=["brute_force", "port_scan", "malware"])
    severity: str = Field(..., examples=["critical", "high", "medium", "low"])


# === Endpoints ===


@router.get("/health")
async def llm_health_check() -> dict[str, Any]:
    """
    Check LLM service health and availability.

    Returns:
        Health status including available models
    """
    service = get_llm_service()
    return service.health_check()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_current_user_optional)] = None,
) -> ChatResponse:
    """
    Simple chat interface with the LLM.

    Use this for general security-related questions.
    If model is provided, that Ollama model is used; otherwise default or task_hint.
    When task_hint=analysis and user is logged in, recent traffic/scan/asset context is injected.
    """
    try:
        settings = get_settings()
        if request.model:
            service = OllamaService(model=request.model)
        elif request.task_hint == "analysis":
            service = OllamaService(model=settings.ollama_reasoning_model)
        else:
            service = get_llm_service()

        system_prompt = request.system_prompt
        if request.task_hint == "analysis" and current_user is not None:
            try:
                context = await build_llm_context(db, current_user.id)
                if context:
                    system_prompt = (system_prompt or "") + "\n\n" + context
            except Exception as e:
                logger.warning("llm_context_build_failed", error=str(e))

        response = await service.chat(
            message=request.message,
            system_prompt=system_prompt or None,
        )
        return ChatResponse(response=response, model=service.model)
    except Exception as e:
        logger.error("chat_endpoint_error", error=str(e))
        raise HTTPException(
            status_code=503,
            detail=f"LLM service error: {e}. Is Ollama running?",
        ) from e


@router.post("/analyze/logs")
async def analyze_logs(request: AnalyzeLogsRequest) -> dict[str, Any]:
    """
    Analyze log data for anomalies and security issues.

    Raw logs are preprocessed (priority filter + quota); under high load
    hybrid mode uses the fast model and stricter limits. Response includes
    analysis_meta (total_lines, lines_analyzed, hybrid_mode_used, etc.).
    """
    try:
        settings = get_settings()
        line_count = len([ln for ln in request.logs.strip().splitlines() if ln.strip()])
        hybrid = line_count >= settings.log_high_load_threshold_lines

        preprocessed = preprocess_logs(request.logs, request.query, hybrid=hybrid)

        if hybrid:
            service = OllamaService(model=settings.ollama_fast_model)
        else:
            service = get_llm_service()

        result = await service.analyze_logs(
            logs=preprocessed.content,
            query=request.query,
        )
        result["model"] = service.model
        result["analysis_meta"] = {
            "total_lines": preprocessed.total_lines,
            "lines_analyzed": preprocessed.lines_analyzed,
            "priority_lines_included": preprocessed.priority_lines_included,
            "rest_lines_dropped": preprocessed.rest_lines_dropped,
            "was_truncated": preprocessed.was_truncated,
            "hybrid_mode_used": preprocessed.hybrid_mode_used,
        }
        return result
    except Exception as e:
        logger.error("log_analysis_endpoint_error", error=str(e))
        raise HTTPException(
            status_code=503,
            detail=f"LLM service error: {e}. Is Ollama running?",
        ) from e


@router.post("/analyze/threat")
async def analyze_threat(request: AnalyzeThreatRequest) -> dict[str, Any]:
    """
    Analyze potential threat data using AI.

    Provide threat indicators and get severity assessment,
    IoC extraction, and recommendations.
    """
    try:
        service = get_llm_service()
        result = await service.analyze_threat(
            threat_data=request.threat_data,
            context=request.context,
        )
        result["model"] = service.model
        return result
    except Exception as e:
        logger.error("threat_analysis_endpoint_error", error=str(e))
        raise HTTPException(
            status_code=503,
            detail=f"LLM service error: {e}. Is Ollama running?",
        ) from e


@router.post("/response-plan")
async def generate_response_plan(request: ResponsePlanRequest) -> dict[str, Any]:
    """
    Generate an incident response plan for a specific threat.

    Provides step-by-step actions for incident responders.
    """
    try:
        service = get_llm_service()
        steps = await service.generate_response_plan(
            threat_type=request.threat_type,
            severity=request.severity,
        )
        return {
            "threat_type": request.threat_type,
            "severity": request.severity,
            "response_steps": steps,
            "model": service.model,
        }
    except Exception as e:
        logger.error("response_plan_endpoint_error", error=str(e))
        raise HTTPException(
            status_code=503,
            detail=f"LLM service error: {e}. Is Ollama running?",
        ) from e
