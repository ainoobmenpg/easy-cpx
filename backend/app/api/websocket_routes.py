# WebSocket API Routes - Real-time game updates
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from sqlalchemy.orm import Session
from typing import Optional, Dict, Set
from app.database import get_db
from app.services.notification_service import get_notification_service, NotificationType
from app.services.auth_service import AuthService, extract_token
from app.services.rbac_service import RBACService
from app.models import Game, User
import json
import logging

logger = logging.getLogger("websocket")
router = APIRouter()


async def get_websocket_db():
    """Dependency for WebSocket database session"""
    db = next(get_db())
    try:
        yield db
    finally:
        db.close()


class ConnectionManager:
    """Manages WebSocket connections for games with role-based rooms"""

    def __init__(self):
        # game_id -> set of WebSockets
        self.active_connections: dict[int, set[WebSocket]] = {}
        # game_id -> role -> set of WebSockets (for role-based chat)
        self.room_connections: dict[int, dict[str, set[WebSocket]]] = {}
        # websocket -> metadata (user, game_id, roles)
        self.ws_metadata: dict[WebSocket, dict] = {}

    async def connect(self, websocket: WebSocket, game_id: int, user=None, game_role=None):
        """Accept and track a new WebSocket connection"""
        await websocket.accept()
        if game_id not in self.active_connections:
            self.active_connections[game_id] = set()
        self.active_connections[game_id].add(websocket)

        # Store metadata
        self.ws_metadata[websocket] = {
            "user_id": user.id if user else None,
            "username": user.username if user else "anonymous",
            "game_id": game_id,
            "game_role": game_role
        }

        # Initialize room connections
        if game_id not in self.room_connections:
            self.room_connections[game_id] = {
                "all": set(),
                "blue": set(),
                "red": set(),
                "white": set(),
                "observer": set()
            }

        # Add to "all" room
        self.room_connections[game_id]["all"].add(websocket)

        # Add to role-specific room
        if game_role:
            self.room_connections[game_id][game_role].add(websocket)

        logger.info(f"WebSocket connected to game {game_id} as {game_role or 'anonymous'}")

    def disconnect(self, websocket: WebSocket, game_id: int):
        """Remove a WebSocket connection"""
        if game_id in self.active_connections:
            self.active_connections[game_id].discard(websocket)
            if not self.active_connections[game_id]:
                del self.active_connections[game_id]
            logger.info(f"WebSocket disconnected from game {game_id}")

        # Remove from rooms
        if game_id in self.room_connections:
            for room in self.room_connections[game_id]:
                self.room_connections[game_id][room].discard(websocket)

        # Remove metadata
        if websocket in self.ws_metadata:
            del self.ws_metadata[websocket]

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific WebSocket"""
        await websocket.send_text(json.dumps(message))

    async def broadcast(self, message: dict, game_id: int):
        """Broadcast a message to all connections for a game"""
        if game_id not in self.active_connections:
            return

        disconnected = []
        for connection in self.active_connections[game_id]:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending to WebSocket: {e}")
                disconnected.append(connection)

        # Clean up dead connections
        for conn in disconnected:
            self.disconnect(conn, game_id)

    async def broadcast_to_room(self, message: dict, game_id: int, channel: str):
        """Broadcast a message to a specific role-based room"""
        if game_id not in self.room_connections:
            return

        target_rooms = ["all"]  # Always include "all" room
        if channel != "all":
            target_rooms.append(channel)

        disconnected = []
        for room in target_rooms:
            if room in self.room_connections[game_id]:
                for connection in self.room_connections[game_id][room]:
                    try:
                        await connection.send_text(json.dumps(message))
                    except Exception as e:
                        logger.error(f"Error sending to WebSocket: {e}")
                        if connection not in disconnected:
                            disconnected.append(connection)

        # Clean up dead connections
        for conn in disconnected:
            self.disconnect(conn, game_id)


# Global connection manager
manager = ConnectionManager()


@router.websocket("/ws/games/{game_id}")
async def websocket_game_endpoint(
    websocket: WebSocket,
    game_id: int,
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """WebSocket endpoint for real-time game updates"""

    # Optional authentication check
    user = None
    game_role = None
    if token:
        auth_service = AuthService(db)
        payload = auth_service.decode_token(token)
        if payload and payload.get("type") == "access":
            user_id = int(payload.get("sub"))
            user = auth_service.get_user_by_id(user_id)
            # Get game-specific role
            rbac = RBACService(db)
            game_role = rbac.get_user_game_role(user_id, game_id)
            # Fall back to system role if no game-specific role
            if not game_role and user:
                game_role = user.role.value

    # Verify game exists
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        await websocket.close(code=4004, reason="Game not found")
        return

    # Connect with role info
    await manager.connect(websocket, game_id, user=user, game_role=game_role)

    # Send connection confirmation
    await manager.send_personal_message({
        "type": "connected",
        "game_id": game_id,
        "user": user.username if user else "anonymous",
        "turn": game.current_turn
    }, websocket)

    try:
        # Handle incoming messages
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)

                # Handle ping/pong
                if message.get("type") == "ping":
                    await manager.send_personal_message({
                        "type": "pong",
                        "timestamp": message.get("timestamp")
                    }, websocket)

                # Handle subscription changes (future: room-based)
                elif message.get("type") == "subscribe":
                    # Already subscribed to game_id
                    pass

                else:
                    logger.warning(f"Unknown WebSocket message type: {message.get('type')}")

            except json.JSONDecodeError:
                logger.error("Invalid JSON received")

    except WebSocketDisconnect:
        manager.disconnect(websocket, game_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, game_id)


# Helper function to broadcast game updates (called from other services)
async def broadcast_game_update(game_id: int, update_type: str, data: dict, turn: Optional[int] = None):
    """Broadcast a game update to all connected clients"""
    message = {
        "type": update_type,
        "game_id": game_id,
        "data": data,
        "turn": turn
    }
    await manager.broadcast(message, game_id)
