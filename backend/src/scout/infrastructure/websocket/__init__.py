"""WebSocket Infrastructure Module.

Provides real-time communication for the HITL approval system.
"""

from scout.infrastructure.websocket.manager import ConnectionManager, websocket_manager

__all__ = ["ConnectionManager", "websocket_manager"]
