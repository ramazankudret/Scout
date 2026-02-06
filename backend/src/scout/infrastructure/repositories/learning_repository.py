"""
Learning Repository Implementation.

Implements ILearningRepository interface for Learning Engine data persistence.
Supports vector search for embedding-based lesson retrieval.
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from scout.domain.interfaces.repositories import ILearningRepository
from scout.infrastructure.database.models import LearnedLesson, VECTOR_AVAILABLE
from scout.infrastructure.repositories.base import BaseRepository


class LearningRepository(BaseRepository[LearnedLesson], ILearningRepository):
    """
    Repository for managing Learned Lessons (Knowledge Base).
    """
    
    def __init__(self, session: AsyncSession):
        super().__init__(model=LearnedLesson, session=session)
    
    async def get_by_id(self, entity_id: UUID) -> Optional[LearnedLesson]:
        """Get a lesson by ID (Repository interface)."""
        return await self.get(entity_id)
    
    async def list_all(self, limit: int = 100, offset: int = 0) -> List[LearnedLesson]:
        """List lessons with pagination (Repository interface)."""
        return await self.get_all(skip=offset, limit=limit)
    
    async def save(self, entity: LearnedLesson) -> LearnedLesson:
        """Save (create or update) a lesson (Repository interface)."""
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity
    
    async def delete(self, entity_id: UUID) -> bool:
        """Delete a lesson by ID (Repository interface)."""
        return await super().delete(entity_id)
        
    async def find_similar(
        self, 
        embedding: List[float], 
        limit: int = 5, 
        threshold: float = 0.8
    ) -> List[LearnedLesson]:
        """
        Find semantically similar lessons using vector search.
        Requires pgvector extension.
        """
        if not VECTOR_AVAILABLE:
            # Fallback for non-vector environments or if dependency missing
            return []
            
        # Using L2 distance (Euclidean) for similarity
        # Ideally, we'd filter by threshold, but let's start with nearest N
        query = (
            select(LearnedLesson)
            .order_by(LearnedLesson.vector_embedding.l2_distance(embedding))
            .limit(limit)
        )
        
        result = await self.session.execute(query)
        lessons = result.scalars().all()
        
        # TODO: Implement threshold filtering if distance metric allows
        return list(lessons)
        
    async def find_by_category(self, category: str) -> List[LearnedLesson]:
        """Find lessons by category."""
        query = (
            select(LearnedLesson)
            .where(LearnedLesson.category == category)
            .order_by(LearnedLesson.occurrence_count.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
        
    async def find_by_action_type(self, action_type: str) -> List[LearnedLesson]:
        """Get lessons relevant to a specific action type."""
        query = (
            select(LearnedLesson)
            .where(LearnedLesson.action_type == action_type)
            .order_by(LearnedLesson.confidence_score.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
