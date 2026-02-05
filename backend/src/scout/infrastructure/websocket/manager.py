"""
WebSocket Connection Manager.

Manages WebSocket connections for real-time notifications in the HITL system.
"""

from datetime import datetime
from typing import Any
from uuid import UUID
import json

from fastapi import WebSocket

from scout.core.logging import get_logger

logger = get_logger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections for real-time communication.

    Features:
    - User-scoped connections (multiple connections per user allowed)
    - Automatic cleanup of dead connections
    - Message queuing for temporarily disconnected users
    - Broadcast to specific user or all users
    """

    def __init__(self, max_queue_size: int = 100):
        # user_id -> list of WebSocket connections
        self._connections: dict[UUID, list[WebSocket]] = {}

        # user_id -> list of queued messages (for temporary disconnects)
        self._message_queue: dict[UUID, list[dict[str, Any]]] = {}

        self._max_queue_size = max_queue_size

    async def connect(self, websocket: WebSocket, user_id: UUID) -> None:
        """
        Accept a new WebSocket connection.

        Args:
            websocket: The WebSocket connection
            user_id: The user ID for this connection
        """
        await websocket.accept()

        if user_id not in self._connections:
            self._connections[user_id] = []

        self._connections[user_id].append(websocket)

        logger.info(
            "websocket_connected",
            user_id=str(user_id),
            connection_count=len(self._connections[user_id]),
        )

        # Send any queued messages
        await self._flush_queue(user_id, websocket)

    def disconnect(self, websocket: WebSocket, user_id: UUID) -> None:
        """
        Remove a WebSocket connection.

        Args:
            websocket: The WebSocket connection to remove
            user_id: The user ID for this connection
        """
        if user_id in self._connections:
            try:
                self._connections[user_id].remove(websocket)
                if not self._connections[user_id]:
                    del self._connections[user_id]
            except ValueError:
                pass  # Already removed

        logger.info("websocket_disconnected", user_id=str(user_id))

    async def broadcast_to_user(
        self,
        user_id: UUID,
        message: dict[str, Any],
    ) -> int:
        """
        Send a message to all connections for a specific user.

        If user is not connected, message is queued for later delivery.

        Args:
            user_id: The user ID to send to
            message: The message dictionary

        Returns:
            Number of connections message was sent to
        """
        sent_count = 0
        message_json = json.dumps(message, default=str)

        if user_id not in self._connections:
            # User not connected, queue the message
            self._queue_message(user_id, message)
            return 0

        dead_connections = []

        for websocket in self._connections[user_id]:
            try:
                await websocket.send_text(message_json)
                sent_count += 1
            except Exception as e:
                logger.warning(
                    "websocket_send_failed",
                    user_id=str(user_id),
                    error=str(e),
                )
                dead_connections.append(websocket)

        # Clean up dead connections
        for ws in dead_connections:
            self.disconnect(ws, user_id)

        return sent_count

    async def broadcast_all(self, message: dict[str, Any]) -> int:
        """
        Broadcast message to all connected users.

        Args:
            message: The message dictionary

        Returns:
            Total number of connections message was sent to
        """
        sent_count = 0
        for user_id in list(self._connections.keys()):
            sent_count += await self.broadcast_to_user(user_id, message)
        return sent_count

    async def send_to_connection(
        self,
        websocket: WebSocket,
        message: dict[str, Any],
    ) -> bool:
        """
        Send a message to a specific connection.

        Args:
            websocket: The WebSocket connection
            message: The message dictionary

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            message_json = json.dumps(message, default=str)
            await websocket.send_text(message_json)
            return True
        except Exception as e:
            logger.warning("websocket_send_failed", error=str(e))
            return False

    def _queue_message(self, user_id: UUID, message: dict[str, Any]) -> None:
        """
        Queue a message for a disconnected user.

        Args:
            user_id: The user ID
            message: The message to queue
        """
        if user_id not in self._message_queue:
            self._message_queue[user_id] = []

        # Limit queue size
        if len(self._message_queue[user_id]) < self._max_queue_size:
            message["queued_at"] = datetime.utcnow().isoformat()
            self._message_queue[user_id].append(message)
        else:
            logger.warning(
                "message_queue_full",
                user_id=str(user_id),
                queue_size=len(self._message_queue[user_id]),
            )

    async def _flush_queue(self, user_id: UUID, websocket: WebSocket) -> None:
        """
        Send all queued messages to a newly connected user.

        Args:
            user_id: The user ID
            websocket: The WebSocket connection to send to
        """
        if user_id not in self._message_queue:
            return

        messages = self._message_queue.pop(user_id, [])

        for message in messages:
            try:
                message_json = json.dumps(message, default=str)
                await websocket.send_text(message_json)
            except Exception as e:
                logger.warning(
                    "queue_flush_failed",
                    user_id=str(user_id),
                    error=str(e),
                )

        if messages:
            logger.info(
                "queue_flushed",
                user_id=str(user_id),
                message_count=len(messages),
            )

    def get_connected_users(self) -> list[UUID]:
        """
        Get list of currently connected user IDs.

        Returns:
            List of user UUIDs
        """
        return list(self._connections.keys())

    def is_user_connected(self, user_id: UUID) -> bool:
        """
        Check if a user has any active connections.

        Args:
            user_id: The user ID to check

        Returns:
            True if user has at least one active connection
        """
        return (
            user_id in self._connections
            and len(self._connections[user_id]) > 0
        )

    def get_connection_count(self, user_id: UUID | None = None) -> int:
        """
        Get number of active connections.

        Args:
            user_id: Optional user ID to filter by

        Returns:
            Number of connections
        """
        if user_id:
            return len(self._connections.get(user_id, []))

        return sum(len(conns) for conns in self._connections.values())

    def get_stats(self) -> dict[str, Any]:
        """
        Get connection statistics.

        Returns:
            Dictionary with stats
        """
        return {
            "total_users": len(self._connections),
            "total_connections": self.get_connection_count(),
            "queued_users": len(self._message_queue),
            "queued_messages": sum(
                len(msgs) for msgs in self._message_queue.values()
            ),
        }


# Global singleton instance
websocket_manager = ConnectionManager()
