"""
Learning Engine - Failure Analysis & Knowledge Base.

Analyzes agent failures, extracts lessons, and stores them in the knowledge base.
Supports persistence and vector search (future).
"""

import asyncio
from typing import Optional, List, Dict
from datetime import datetime
from uuid import uuid4, UUID

from scout.core.logger import get_logger
from scout.core.model_router import get_reasoning_model
from scout.infrastructure.database.session import get_db_context
from scout.infrastructure.repositories.learning_repository import LearningRepository
from scout.infrastructure.database.models import LearnedLesson
# Removed circular import
# from scout.agents.learning_engine import LessonCategory, LessonSeverity 

# Re-defining Enums here to avoid circular dependency issues if file is completely replaced
from enum import Enum

class LessonCategory(str, Enum):
    CONFIGURATION = "configuration"
    NETWORK = "network"
    PERMISSION = "permission"
    RESOURCE = "resource"
    LOGIC = "logic"
    EXTERNAL = "external"
    UNKNOWN = "unknown"

class LessonSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

logger = get_logger("learning_engine")


class LearningEngine:
    """
    Learning Engine that extracts lessons from failures.
    
    Workflow:
    1. Agent reports a failed action
    2. LLM analyzes the failure
    3. Lesson is extracted and stored (In-Memory + DB)
    4. Future actions check lessons before execution
    """
    
    def __init__(self):
        self._lessons: Dict[str, LearnedLesson] = {} # Cache: ID -> Lesson
        self._lesson_index: Dict[str, List[str]] = {}  # Category -> IDs
        
        logger.info("learning_engine_initialized")
        
    async def start(self):
        """Load lessons from database on startup."""
        try:
            async with get_db_context() as session:
                repo = LearningRepository(session)
                lessons = await repo.get_all()
                
                for lesson in lessons:
                    self._cache_lesson(lesson)
                    
            logger.info("learning_engine_started", loaded_lessons=len(self._lessons))
        except Exception as e:
            logger.error("learning_engine_load_failed", error=str(e))

    def _cache_lesson(self, lesson: LearnedLesson):
        """Update internal cache."""
        lesson_id = str(lesson.id)
        self._lessons[lesson_id] = lesson
        
        if lesson.category not in self._lesson_index:
            self._lesson_index[lesson.category] = []
        if lesson_id not in self._lesson_index[lesson.category]:
            self._lesson_index[lesson.category].append(lesson_id)

    async def _persist_lesson(self, lesson_data: dict) -> LearnedLesson:
        """Save lesson to database."""
        async with get_db_context() as session:
            repo = LearningRepository(session)
            lesson = await repo.create(**lesson_data)
            return lesson

    async def analyze_failure(
        self,
        agent_name: str,
        action_type: str,
        target: str,
        error_message: str,
        error_type: str = "",
        context: Optional[dict] = None
    ) -> LearnedLesson:
        """
        Analyze a failure using LLM and store the lesson.
        """
        logger.info("analyzing_failure", agent=agent_name, action=action_type)
        
        # 1. LLM Analysis
        try:
            llm = get_reasoning_model()
            prompt = self._create_analysis_prompt(
                agent_name, action_type, target, error_message, error_type, context
            )
            
            response = await llm.ainvoke(prompt)
            analysis_text = response.content
            
            # 2. Extract structured data (simplify for now, ideally use JsonOutputParser)
            # For this implementation, we'll parse a simple structure or use defaults
            # TODO: Improve parsing logic
            lesson_data = self._parse_llm_response(analysis_text)
            
        except Exception as e:
            logger.error("llm_analysis_failed", error=str(e))
            # Fallback
            lesson_data = {
                "root_cause": "Automatic analysis failed",
                "prevention_strategy": "Manual review required",
                "category": LessonCategory.UNKNOWN,
                "severity": LessonSeverity.MEDIUM,
                "recommended_checks": []
            }

        # 3. Create Lesson Object
        # Note: We create a DB model instance directly
        new_lesson_data = {
            "agent_name": agent_name,
            "action_type": action_type,
            "target": target,
            "error_message": error_message,
            "root_cause": lesson_data.get("root_cause"),
            "category": lesson_data.get("category", LessonCategory.UNKNOWN),
            "severity": lesson_data.get("severity", LessonSeverity.MEDIUM),
            "prevention_strategy": lesson_data.get("prevention_strategy"),
            "recommended_checks": lesson_data.get("recommended_checks", []),
            "occurrence_count": 1,
            "effectiveness_rate": 0.0,
            # "vector_embedding": ... # TODO: Add embedding
        }
        
        # 4. Save to DB and Cache
        saved_lesson = await self._persist_lesson(new_lesson_data)
        self._cache_lesson(saved_lesson)
        
        return saved_lesson

    def _create_analysis_prompt(self, agent_name, action_type, target, error_message, error_type, context):
        return f"""Analyze this failure and extract a lesson:
        
Agent: {agent_name}
Action: {action_type}
Target: {target}
Error: {error_message} ({error_type})
Context: {context}

Provide a structured analysis including:
1. Root Cause
2. Category (CONFIG, NETWORK, PERMISSION, RESOURCE, LOGIC, EXTERNAL)
3. Severity (LOW, MEDIUM, HIGH, CRITICAL)
4. Prevention Strategy
5. Recommended Checks (List of strings)

Format your response clearly.
"""

    def _parse_llm_response(self, text: str) -> dict:
        """Simple fuzzy parser for LLM response."""
        # This is a placeholder. In production, use LangChain OutputParsers.
        data = {}
        text = text.lower()
        
        if "network" in text: data["category"] = LessonCategory.NETWORK
        elif "permission" in text or "denied" in text: data["category"] = LessonCategory.PERMISSION
        elif "config" in text: data["category"] = LessonCategory.CONFIGURATION
        else: data["category"] = LessonCategory.UNKNOWN
        
        if "critical" in text: data["severity"] = LessonSeverity.CRITICAL
        elif "high" in text: data["severity"] = LessonSeverity.HIGH
        else: data["severity"] = LessonSeverity.MEDIUM
        
        data["root_cause"] = text.split('\n')[0][:200] # Take first line as summary
        data["prevention_strategy"] = "Extracted from analysis: " + text[:100] + "..."
        data["recommended_checks"] = ["Check connectivity", "Verify permissions"]
        
        return data

    def get_all_lessons(self) -> List[LearnedLesson]:
        """Get all lessons (from cache)."""
        return list(self._lessons.values())
        
    def get_lessons_by_category(self, category: LessonCategory) -> List[LearnedLesson]:
        """Get lessons by category (from cache)."""
        if category not in self._lesson_index:
            return []
            
        return [
            self._lessons[lesson_id] 
            for lesson_id in self._lesson_index.get(category, [])  # Use .get() to avoid KeyError if key not in dict but loop logic is flawed
             if lesson_id in self._lessons # Double check existence
        ]
        
    def get_lessons_for_action(self, action_type: str) -> List[LearnedLesson]:
        """Get lessons relevant to an action type."""
        # Simple scan for now, could index by action_type too
        return [
            l for l in self._lessons.values() 
            if l.action_type == action_type
        ]

    def get_prevention_checks(self, action_type: str) -> List[str]:
        """Get unified list of checks for an action."""
        lessons = self.get_lessons_for_action(action_type)
        checks = set()
        for l in lessons:
            if l.recommended_checks:
                # Handle if recommended_checks is list or json
                if isinstance(l.recommended_checks, list):
                    checks.update(l.recommended_checks)
        return list(checks)

    def get_summary(self) -> dict:
        """Get engine statistics."""
        return {
            "total_lessons": len(self._lessons),
            "total_occurrences": sum(l.occurrence_count for l in self._lessons.values()),
            "by_category": {
                cat: len(ids) for cat, ids in self._lesson_index.items()
            },
            "by_severity": {} # TODO: Calculate
        }


# Global instance
learning_engine = LearningEngine()
