"""
WebSocket API Endpoint.

Handles WebSocket connections for real-time notifications in the HITL system.
"""

from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException
from jose import JWTError, jwt

from scout.core.config import settings
from scout.core.logging import get_logger
from scout.infrastructure.websocket import websocket_manager

logger = get_logger(__name__)

router = APIRouter()


async def authenticate_websocket(token: str) -> UUID:
    """
    Authenticate a WebSocket connection using JWT token.

    Args:
        token: JWT token

    Returns:
        User ID from the token

    Raises:
        HTTPException: If authentication fails
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("No user ID in token")
        return UUID(user_id)
    except JWTError as e:
        detail = "Token expired" if "expired" in str(e).lower() else f"Invalid token: {e}"
        raise HTTPException(status_code=4001, detail=detail)
    except Exception as e:
        raise HTTPException(status_code=4003, detail=f"Authentication failed: {e}")


@router.websocket("/ws/notifications")
async def notifications_websocket(
    websocket: WebSocket,
    token: str = Query(..., description="JWT token for authentication"),
):
    """
    WebSocket endpoint for real-time notifications.

    Connect with: ws://localhost:8000/api/v1/ws/notifications?token=<jwt>

    Message types sent to client:
    - connected: Connection established
    - action_pending_approval: New action requires approval
    - action_approved: Action was approved
    - action_rejected: Action was rejected
    - action_expired: Action expired with auto-action
    - ping: Heartbeat (client should respond with pong)

    Message types received from client:
    - pong: Heartbeat response
    - ack: Acknowledge receipt of a message
    """
    # Authenticate user from token
    try:
        user_id = await authenticate_websocket(token)
    except HTTPException as e:
        await websocket.close(code=4001, reason=str(e.detail))
        return
    except Exception as e:
        await websocket.close(code=4003, reason=f"Authentication failed: {e}")
        return

    # Accept connection
    await websocket_manager.connect(websocket, user_id)

    try:
        # Send connection confirmation
        await websocket_manager.send_to_connection(
            websocket,
            {
                "type": "connected",
                "user_id": str(user_id),
                "message": "WebSocket connection established",
            }
        )

        # Listen for messages
        while True:
            try:
                data = await websocket.receive_json()

                # Handle different message types
                msg_type = data.get("type")

                if msg_type == "pong":
                    # Heartbeat response - do nothing
                    logger.debug("pong_received", user_id=str(user_id))

                elif msg_type == "ack":
                    # Acknowledge message receipt
                    message_id = data.get("message_id")
                    logger.debug(
                        "message_acknowledged",
                        user_id=str(user_id),
                        message_id=message_id,
                    )

                elif msg_type == "ping":
                    # Client ping - respond with pong
                    await websocket_manager.send_to_connection(
                        websocket,
                        {"type": "pong"}
                    )

                else:
                    logger.warning(
                        "unknown_ws_message_type",
                        user_id=str(user_id),
                        msg_type=msg_type,
                    )

            except Exception as e:
                logger.debug(
                    "ws_receive_error",
                    user_id=str(user_id),
                    error=str(e),
                )
                break

    except WebSocketDisconnect:
        logger.info("websocket_client_disconnected", user_id=str(user_id))
    except Exception as e:
        logger.error("websocket_error", user_id=str(user_id), error=str(e))
    finally:
        websocket_manager.disconnect(websocket, user_id)


@router.get("/ws/stats")
async def get_websocket_stats():
    """Get WebSocket connection statistics."""
    return websocket_manager.get_stats()
