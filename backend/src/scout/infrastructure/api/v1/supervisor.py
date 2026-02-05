"""
Supervisor API Endpoints.

Provides endpoints for:
- Viewing agent health status
- Restarting failed agents
- Getting supervisor summary
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from scout.agents.supervisor import supervisor, AgentStatus
from scout.agents.learning_engine import learning_engine, LessonCategory
from scout.core.logger import get_logger

router = APIRouter(prefix="/supervisor", tags=["Supervisor"])
logger = get_logger("supervisor_api")


# ==================== Response Models ====================

class AgentHealthResponse(BaseModel):
    """Agent health status response."""
    agent_name: str
    status: str
    last_heartbeat: str | None
    last_error: str | None
    consecutive_failures: int
    total_executions: int
    success_rate: float
    restart_count: int


class SupervisorSummaryResponse(BaseModel):
    """Supervisor summary response."""
    total_agents: int
    healthy: int
    degraded: int
    failed: int
    recovering: int
    stopped: int


class LessonResponse(BaseModel):
    """Learned lesson response."""
    id: str
    agent_name: str
    action_type: str
    root_cause: str
    category: str
    severity: str
    prevention_strategy: str
    recommended_checks: list[str]
    occurrence_count: int
    effectiveness_rate: float


class LearningEngineSummaryResponse(BaseModel):
    """Learning engine summary response."""
    total_lessons: int
    total_occurrences: int
    by_category: dict[str, int]
    by_severity: dict[str, int]


class AnalyzeFailureRequest(BaseModel):
    """Request to analyze a failure."""
    agent_name: str
    action_type: str
    target: str
    error_message: str
    error_type: str = ""
    context: dict | None = None


# ==================== Supervisor Endpoints ====================

@router.get("/status", response_model=list[AgentHealthResponse])
async def get_all_agent_statuses():
    """
    Get health status for all registered agents.
    """
    statuses = supervisor.get_all_statuses()
    
    return [
        AgentHealthResponse(
            agent_name=record.agent_name,
            status=record.status.value,
            last_heartbeat=record.last_heartbeat.isoformat() if record.last_heartbeat else None,
            last_error=record.last_error,
            consecutive_failures=record.consecutive_failures,
            total_executions=record.total_executions,
            success_rate=record.success_rate,
            restart_count=record.restart_count,
        )
        for record in statuses.values()
    ]


@router.get("/status/{agent_name}", response_model=AgentHealthResponse)
async def get_agent_status(agent_name: str):
    """
    Get health status for a specific agent.
    """
    record = supervisor.get_agent_status(agent_name)
    
    if not record:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
    
    return AgentHealthResponse(
        agent_name=record.agent_name,
        status=record.status.value,
        last_heartbeat=record.last_heartbeat.isoformat() if record.last_heartbeat else None,
        last_error=record.last_error,
        consecutive_failures=record.consecutive_failures,
        total_executions=record.total_executions,
        success_rate=record.success_rate,
        restart_count=record.restart_count,
    )


@router.post("/restart/{agent_name}")
async def restart_agent(agent_name: str):
    """
    Attempt to restart a failed agent.
    """
    record = supervisor.get_agent_status(agent_name)
    
    if not record:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
    
    success = await supervisor.restart_agent(agent_name)
    
    return {
        "agent_name": agent_name,
        "restart_initiated": success,
        "message": "Restart successful" if success else "Restart failed - max attempts exceeded",
    }


@router.get("/summary", response_model=SupervisorSummaryResponse)
async def get_supervisor_summary():
    """
    Get a summary of all agent statuses.
    """
    summary = supervisor.get_summary()
    return SupervisorSummaryResponse(**summary)


@router.post("/register/{agent_name}")
async def register_agent(agent_name: str):
    """
    Register an agent for monitoring.
    """
    await supervisor.register_agent(agent_name)
    return {"message": f"Agent '{agent_name}' registered successfully"}


# ==================== Learning Engine Endpoints ====================

@router.get("/lessons", response_model=list[LessonResponse])
async def get_all_lessons():
    """
    Get all learned lessons.
    """
    lessons = learning_engine.get_all_lessons()
    
    return [
        LessonResponse(
            id=lesson.id,
            agent_name=lesson.agent_name,
            action_type=lesson.action_type,
            root_cause=lesson.root_cause,
            category=lesson.category.value,
            severity=lesson.severity.value,
            prevention_strategy=lesson.prevention_strategy,
            recommended_checks=lesson.recommended_checks,
            occurrence_count=lesson.occurrence_count,
            effectiveness_rate=lesson.effectiveness_rate,
        )
        for lesson in lessons
    ]


@router.get("/lessons/category/{category}", response_model=list[LessonResponse])
async def get_lessons_by_category(category: str):
    """
    Get lessons by category.
    """
    try:
        cat = LessonCategory(category.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category. Must be one of: {[c.value for c in LessonCategory]}"
        )
    
    lessons = learning_engine.get_lessons_by_category(cat)
    
    return [
        LessonResponse(
            id=lesson.id,
            agent_name=lesson.agent_name,
            action_type=lesson.action_type,
            root_cause=lesson.root_cause,
            category=lesson.category.value,
            severity=lesson.severity.value,
            prevention_strategy=lesson.prevention_strategy,
            recommended_checks=lesson.recommended_checks,
            occurrence_count=lesson.occurrence_count,
            effectiveness_rate=lesson.effectiveness_rate,
        )
        for lesson in lessons
    ]


@router.get("/lessons/action/{action_type}")
async def get_lessons_for_action(action_type: str):
    """
    Get lessons and recommended checks for a specific action type.
    
    Useful before executing an action to check for known issues.
    """
    lessons = learning_engine.get_lessons_for_action(action_type)
    checks = learning_engine.get_prevention_checks(action_type)
    
    return {
        "action_type": action_type,
        "lessons_count": len(lessons),
        "recommended_checks": checks,
        "lessons": [
            {
                "id": lesson.id,
                "root_cause": lesson.root_cause,
                "prevention_strategy": lesson.prevention_strategy,
                "occurrence_count": lesson.occurrence_count,
            }
            for lesson in lessons
        ]
    }


@router.post("/lessons/analyze", response_model=LessonResponse)
async def analyze_failure(request: AnalyzeFailureRequest):
    """
    Analyze a failure and extract a lesson.
    
    Uses LLM to understand the root cause and prevention strategy.
    """
    lesson = await learning_engine.analyze_failure(
        agent_name=request.agent_name,
        action_type=request.action_type,
        target=request.target,
        error_message=request.error_message,
        error_type=request.error_type,
        context=request.context,
    )
    
    return LessonResponse(
        id=lesson.id,
        agent_name=lesson.agent_name,
        action_type=lesson.action_type,
        root_cause=lesson.root_cause,
        category=lesson.category.value,
        severity=lesson.severity.value,
        prevention_strategy=lesson.prevention_strategy,
        recommended_checks=lesson.recommended_checks,
        occurrence_count=lesson.occurrence_count,
        effectiveness_rate=lesson.effectiveness_rate,
    )


@router.get("/learning/summary", response_model=LearningEngineSummaryResponse)
async def get_learning_summary():
    """
    Get a summary of the learning engine state.
    """
    summary = learning_engine.get_summary()
    return LearningEngineSummaryResponse(**summary)
