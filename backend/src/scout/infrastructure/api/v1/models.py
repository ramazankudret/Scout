"""
Model Management API Endpoints.

Provides endpoints for:
- Listing available models
- Checking model status
- Testing model inference
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from scout.core.model_router import (
    model_router,
    ModelType,
    TaskCategory,
    get_fast_model,
    get_reasoning_model,
    get_default_model,
)
from scout.core.config import settings
from scout.core.logger import get_logger

router = APIRouter(prefix="/models", tags=["Models"])
logger = get_logger("models_api")


class ModelStatus(BaseModel):
    """Model availability status."""
    name: str
    type: str
    available: bool


class ModelsStatusResponse(BaseModel):
    """Response for model status check."""
    models: list[ModelStatus]
    configured: dict[str, str]


class ModelTestRequest(BaseModel):
    """Request for testing a model."""
    model_type: str = "default"  # fast, reasoning, default
    prompt: str = "Hello, respond with 'OK' if you're working."
    max_tokens: int = 100


class ModelTestResponse(BaseModel):
    """Response from model test."""
    model_type: str
    model_name: str
    response: str
    success: bool
    error: str | None = None


@router.get("/status", response_model=ModelsStatusResponse)
async def get_models_status():
    """
    Get the status of all configured models.
    
    Returns which models are available in Ollama.
    """
    availability = await model_router.check_models_available()
    
    models = [
        ModelStatus(
            name=model_router.get_model_name(model_type),
            type=model_type.value,
            available=is_available
        )
        for model_type, is_available in availability.items()
    ]
    
    configured = {
        "default": settings.ollama_model,
        "reasoning": settings.ollama_reasoning_model,
        "fast": settings.ollama_fast_model,
    }
    
    return ModelsStatusResponse(models=models, configured=configured)


@router.post("/test", response_model=ModelTestResponse)
async def test_model(request: ModelTestRequest):
    """
    Test a model with a simple prompt.
    
    Useful for verifying model availability and performance.
    """
    try:
        model_type = ModelType(request.model_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model_type. Must be one of: fast, reasoning, default"
        )
    
    model_name = model_router.get_model_name(model_type)
    
    try:
        llm = model_router.get_model(model_type=model_type)
        response = await llm.ainvoke(request.prompt)
        
        return ModelTestResponse(
            model_type=model_type.value,
            model_name=model_name,
            response=response.content,
            success=True
        )
        
    except Exception as e:
        logger.error("model_test_failed", model=model_name, error=str(e))
        return ModelTestResponse(
            model_type=model_type.value,
            model_name=model_name,
            response="",
            success=False,
            error=str(e)
        )


@router.get("/task-mapping")
async def get_task_model_mapping():
    """
    Get the task category to model type mapping.
    
    Shows which model is used for each type of task.
    """
    from scout.core.model_router import TASK_MODEL_MAP
    
    mapping = {
        task.value: {
            "model_type": model_type.value,
            "model_name": model_router.get_model_name(model_type)
        }
        for task, model_type in TASK_MODEL_MAP.items()
    }
    
    return {"mapping": mapping}
