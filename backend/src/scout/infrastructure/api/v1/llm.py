"""
LLM API Endpoints.

Provides endpoints for testing and using the local LLM (Ollama).
"""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from scout.core.logging import get_logger
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
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Simple chat interface with the LLM.

    Use this for general security-related questions.
    """
    try:
        service = get_llm_service()
        response = await service.chat(
            message=request.message,
            system_prompt=request.system_prompt,
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

    Provide raw logs and a query describing what to look for.
    """
    try:
        service = get_llm_service()
        result = await service.analyze_logs(
            logs=request.logs,
            query=request.query,
        )
        result["model"] = service.model
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
