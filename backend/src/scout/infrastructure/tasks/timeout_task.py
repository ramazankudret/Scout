"""
Background Task for Processing Approval Timeouts.

Runs periodically to handle expired pending actions.
"""

import asyncio
from typing import Callable, Awaitable

from scout.core.logging import get_logger

logger = get_logger(__name__)

# Configuration
TIMEOUT_CHECK_INTERVAL = 10  # Check every 10 seconds

# Global state
_running = False
_task: asyncio.Task | None = None


async def timeout_processing_task(
    get_db_session: Callable[[], Awaitable],
) -> None:
    """
    Background task that processes expired approval requests.

    Runs continuously, checking for expired actions at regular intervals.

    Args:
        get_db_session: Async context manager for database sessions
    """
    global _running
    _running = True

    logger.info("timeout_task_started", interval_seconds=TIMEOUT_CHECK_INTERVAL)

    while _running:
        try:
            # Import here to avoid circular imports
            from scout.infrastructure.repositories.approval_repositories import (
                PendingActionRepository,
            )
            from scout.application.services.timeout_service import ApprovalTimeoutService
            from scout.infrastructure.websocket import websocket_manager

            async with get_db_session() as db:
                repo = PendingActionRepository(db)
                service = ApprovalTimeoutService(
                    pending_action_repo=repo,
                    websocket_manager=websocket_manager,
                )

                processed = await service.process_expired_actions()

                if processed > 0:
                    logger.debug("timeout_check_complete", processed=processed)

        except Exception as e:
            logger.exception("timeout_task_error", error=str(e))

        await asyncio.sleep(TIMEOUT_CHECK_INTERVAL)

    logger.info("timeout_task_stopped")


def stop_timeout_task() -> None:
    """Stop the timeout processing task."""
    global _running, _task
    _running = False
    if _task:
        _task.cancel()
        _task = None


def start_timeout_task(
    get_db_session: Callable[[], Awaitable],
) -> asyncio.Task:
    """
    Start the timeout processing task.

    Args:
        get_db_session: Async context manager for database sessions

    Returns:
        The asyncio Task object
    """
    global _task
    _task = asyncio.create_task(timeout_processing_task(get_db_session))
    return _task
