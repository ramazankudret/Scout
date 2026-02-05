"""
Scout LLM Model Router.

Dynamically routes tasks to the most appropriate LLM model based on:
- Task complexity
- Latency requirements
- Model capabilities
"""

from enum import Enum
from typing import Optional
from langchain_ollama import ChatOllama
from scout.core.config import settings
from scout.core.logger import get_logger

logger = get_logger("model_router")


class ModelType(str, Enum):
    """Available model types for different task categories."""
    
    FAST = "fast"           # Quick responses, agent routing, simple decisions
    REASONING = "reasoning" # Deep analysis, threat investigation, complex logic
    DEFAULT = "default"     # General purpose, balanced performance


class TaskCategory(str, Enum):
    """Task categories that map to model types."""
    
    # Fast model tasks
    AGENT_ROUTING = "agent_routing"
    SIMPLE_CLASSIFICATION = "simple_classification"
    QUICK_RESPONSE = "quick_response"
    LOG_PARSING = "log_parsing"
    
    # Reasoning model tasks
    THREAT_ANALYSIS = "threat_analysis"
    INCIDENT_INVESTIGATION = "incident_investigation"
    ATTACK_CHAIN_REASONING = "attack_chain_reasoning"
    REPORT_GENERATION = "report_generation"
    VULNERABILITY_ASSESSMENT = "vulnerability_assessment"
    
    # Default model tasks
    GENERAL = "general"
    CHAT = "chat"
    SUMMARIZATION = "summarization"


# Task category to model type mapping
TASK_MODEL_MAP: dict[TaskCategory, ModelType] = {
    # Fast
    TaskCategory.AGENT_ROUTING: ModelType.FAST,
    TaskCategory.SIMPLE_CLASSIFICATION: ModelType.FAST,
    TaskCategory.QUICK_RESPONSE: ModelType.FAST,
    TaskCategory.LOG_PARSING: ModelType.FAST,
    
    # Reasoning
    TaskCategory.THREAT_ANALYSIS: ModelType.REASONING,
    TaskCategory.INCIDENT_INVESTIGATION: ModelType.REASONING,
    TaskCategory.ATTACK_CHAIN_REASONING: ModelType.REASONING,
    TaskCategory.REPORT_GENERATION: ModelType.REASONING,
    TaskCategory.VULNERABILITY_ASSESSMENT: ModelType.REASONING,
    
    # Default
    TaskCategory.GENERAL: ModelType.DEFAULT,
    TaskCategory.CHAT: ModelType.DEFAULT,
    TaskCategory.SUMMARIZATION: ModelType.DEFAULT,
}


class ModelRouter:
    """
    Routes LLM requests to the appropriate model based on task type.
    
    Usage:
        router = ModelRouter()
        llm = router.get_model(TaskCategory.THREAT_ANALYSIS)
        response = await llm.ainvoke("Analyze this threat...")
    """
    
    def __init__(self):
        self._models: dict[ModelType, ChatOllama] = {}
        self._model_configs = {
            ModelType.FAST: {
                "model": settings.ollama_fast_model,
                "temperature": 0.1,  # More deterministic
                "num_predict": 256,  # Shorter responses
            },
            ModelType.REASONING: {
                "model": settings.ollama_reasoning_model,
                "temperature": 0.3,
                "num_predict": 2048,  # Longer chain-of-thought
            },
            ModelType.DEFAULT: {
                "model": settings.ollama_model,
                "temperature": 0.7,
                "num_predict": 1024,
            },
        }
        
    def get_model(
        self, 
        task: TaskCategory | None = None,
        model_type: ModelType | None = None,
        temperature: Optional[float] = None,
    ) -> ChatOllama:
        """
        Get the appropriate LLM model for a task.
        
        Args:
            task: The task category (will be mapped to model type)
            model_type: Direct model type override
            temperature: Optional temperature override
            
        Returns:
            Configured ChatOllama instance
        """
        # Determine model type
        if model_type is None:
            model_type = TASK_MODEL_MAP.get(task, ModelType.DEFAULT) if task else ModelType.DEFAULT
            
        # Get or create model instance
        if model_type not in self._models:
            config = self._model_configs[model_type].copy()
            
            if temperature is not None:
                config["temperature"] = temperature
                
            self._models[model_type] = ChatOllama(
                base_url=settings.ollama_base_url,
                **config
            )
            
            logger.info(
                "model_initialized",
                model_type=model_type.value,
                model_name=config["model"],
            )
            
        return self._models[model_type]
    
    def get_model_name(self, model_type: ModelType) -> str:
        """Get the model name for a given type."""
        return self._model_configs[model_type]["model"]
    
    async def check_models_available(self) -> dict[ModelType, bool]:
        """Check which models are available in Ollama."""
        import httpx
        
        results = {}
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{settings.ollama_base_url}/api/tags",
                    timeout=5.0
                )
                if response.status_code == 200:
                    data = response.json()
                    available_models = {m["name"] for m in data.get("models", [])}
                    
                    for model_type in ModelType:
                        model_name = self._model_configs[model_type]["model"]
                        # Check both exact match and base name
                        is_available = (
                            model_name in available_models or
                            any(model_name.split(":")[0] in m for m in available_models)
                        )
                        results[model_type] = is_available
                        
            except Exception as e:
                logger.error("model_check_failed", error=str(e))
                results = {mt: False for mt in ModelType}
                
        return results


# Global router instance
model_router = ModelRouter()


# Convenience functions
def get_fast_model() -> ChatOllama:
    """Get the fast model for quick operations."""
    return model_router.get_model(model_type=ModelType.FAST)


def get_reasoning_model() -> ChatOllama:
    """Get the reasoning model for deep analysis."""
    return model_router.get_model(model_type=ModelType.REASONING)


def get_default_model() -> ChatOllama:
    """Get the default balanced model."""
    return model_router.get_model(model_type=ModelType.DEFAULT)


def get_model_for_task(task: TaskCategory) -> ChatOllama:
    """Get the appropriate model for a specific task."""
    return model_router.get_model(task=task)
