"""
Timeout Processor for Pending Actions.

This module handles the automatic processing of pending actions
that have exceeded their validity period. It respects the 'auto_action'
configuration (approve vs reject) defined in the request.
"""

import asyncio
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from scout.core.logging import get_logger
from scout.infrastructure.database.session import get_db

logger = get_logger(__name__)


class TimeoutProcessor:
    """
    Background task to process timed-out pending actions.
    """

    def __init__(self, interval_seconds: int = 60):
        self.interval = interval_seconds
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self):
        """Start the timeout processor background task."""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("timeout_processor_started", interval=self.interval)

    async def stop(self):
        """Stop the timeout processor."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("timeout_processor_stopped")

    async def _run_loop(self):
        """Main processing loop."""
        while self._running:
            try:
                await self.process_timeouts()
            except Exception as e:
                logger.error("timeout_processor_error", error=str(e))
                # Prevent tight loop on error
                await asyncio.sleep(5)
            
            await asyncio.sleep(self.interval)

    async def process_timeouts(self) -> int:
        """
        Find and process pending actions that have passed their expiration time.
        """
        try:
            # Delayed import to avoid circular dependencies during startup
            from scout.infrastructure.database.models_approval import PendingAction
        except ImportError:
            logger.warning("approval_models_not_found_skipping")
            return 0

        count = 0
        async for session in get_db():
            try:
                now = datetime.utcnow()
                
                # Find all expired pending actions
                # We fetch them first because we might need to apply different logic
                # based on 'auto_action' (approve vs reject)
                stmt = select(PendingAction).where(
                    PendingAction.status == "pending",
                    PendingAction.expires_at < now
                ).limit(100)  # Process in batches
                
                result = await session.execute(stmt)
                expired_actions = result.scalars().all()
                
                if not expired_actions:
                    return 0
                
                for action in expired_actions:
                    # Decide new status based on policy
                    original_status = action.status
                    
                    if action.auto_action == "approve":
                        action.status = "approved"
                        action.decision_method = "auto_timeout"
                        action.decided_at = now
                        # Ideally, this would trigger the actual execution logic here
                        # For now, we just mark it approved, and another worker pick it up
                        logger.info("action_auto_approved_on_timeout", action_id=str(action.id))
                    else:
                        action.status = "expired"  # or 'rejected'
                        action.decision_method = "auto_timeout"
                        action.decided_at = now
                        action.rejection_reason = "Action timed out and policy is to reject."
                        logger.info("action_expired_on_timeout", action_id=str(action.id))
                    
                    count += 1
                
                await session.commit()
                
                if count > 0:
                    logger.info("processed_timeouts", count=count)
                
                return count
                
            except Exception as e:
                await session.rollback()
                logger.error("error_processing_timeouts", error=str(e))
                raise e
        return 0
