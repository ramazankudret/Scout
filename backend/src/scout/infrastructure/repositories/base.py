"""
Base Repository - Generic CRUD operations
"""
from typing import TypeVar, Generic, Type, Optional, List, Any
from uuid import UUID

from sqlalchemy import select, func, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from scout.infrastructure.database.models import Base

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    """
    Generic repository for common database operations.
    
    Usage:
        class UserRepository(BaseRepository[User]):
            pass
        
        repo = UserRepository(User, db)
        user = await repo.get(user_id)
    """
    
    def __init__(self, model: Type[T], session: AsyncSession):
        self.model = model
        self.session = session
    
    async def get(self, id: UUID) -> Optional[T]:
        """Get a single record by ID"""
        return await self.session.get(self.model, id)
    
    async def get_or_raise(self, id: UUID) -> T:
        """Get a single record by ID, raise if not found"""
        result = await self.get(id)
        if result is None:
            raise ValueError(f"{self.model.__name__} with id {id} not found")
        return result
    
    async def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100,
        order_by: Optional[str] = None
    ) -> List[T]:
        """Get all records with pagination"""
        query = select(self.model).offset(skip).limit(limit)
        if order_by:
            query = query.order_by(order_by)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_by_user(
        self, 
        user_id: UUID, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[T]:
        """Get all records for a specific user"""
        query = (
            select(self.model)
            .where(self.model.user_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def create(self, **kwargs) -> T:
        """Create a new record"""
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance
    
    async def update(self, id: UUID, **kwargs) -> Optional[T]:
        """Update a record by ID"""
        instance = await self.get(id)
        if instance is None:
            return None
        for key, value in kwargs.items():
            setattr(instance, key, value)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance
    
    async def delete(self, id: UUID) -> bool:
        """Delete a record by ID"""
        instance = await self.get(id)
        if instance is None:
            return False
        await self.session.delete(instance)
        await self.session.flush()
        return True
    
    async def count(self) -> int:
        """Count all records"""
        query = select(func.count()).select_from(self.model)
        result = await self.session.execute(query)
        return result.scalar() or 0
    
    async def count_by_user(self, user_id: UUID) -> int:
        """Count records for a specific user"""
        query = (
            select(func.count())
            .select_from(self.model)
            .where(self.model.user_id == user_id)
        )
        result = await self.session.execute(query)
        return result.scalar() or 0
    
    async def exists(self, id: UUID) -> bool:
        """Check if a record exists"""
        query = select(func.count()).select_from(self.model).where(self.model.id == id)
        result = await self.session.execute(query)
        return (result.scalar() or 0) > 0
