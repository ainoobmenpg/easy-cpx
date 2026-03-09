# WebSocket Notification Service - Real-time notifications for game events
from typing import Dict, List, Callable, Any, Optional
from datetime import datetime
import json
from dataclasses import dataclass, field
from enum import Enum


class NotificationType(str, Enum):
    """Types of notifications that can be sent"""
    TURN_ADVANCE = "turn_advance"
    ORDER_RECEIVED = "order_received"
    SITREP_READY = "sitrep_ready"
    GAME_UPDATE = "game_update"
    CHAT_MESSAGE = "chat_message"
    PLAYER_READY = "player_ready"
    GAME_START = "game_start"
    GAME_END = "game_end"


@dataclass
class WebSocketMessage:
    """WebSocket message structure"""
    type: NotificationType
    game_id: int
    turn: Optional[int] = None
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_json(self) -> str:
        return json.dumps({
            "type": self.type.value,
            "game_id": self.game_id,
            "turn": self.turn,
            "data": self.data,
            "timestamp": self.timestamp
        })


class NotificationService:
    """Service for managing WebSocket notifications"""

    def __init__(self):
        # game_id -> set of connected WebSocket connections
        self._game_connections: Dict[int, set] = {}
        # connection -> game_id mapping
        self._connection_to_game: Dict[Any, int] = {}

    def subscribe(self, game_id: int, websocket: Any) -> None:
        """Subscribe a WebSocket connection to game updates"""
        if game_id not in self._game_connections:
            self._game_connections[game_id] = set()

        self._game_connections[game_id].add(websocket)
        self._connection_to_game[websocket] = game_id

    def unsubscribe(self, websocket: Any) -> None:
        """Unsubscribe a WebSocket connection"""
        game_id = self._connection_to_game.pop(websocket, None)
        if game_id and game_id in self._game_connections:
            self._game_connections[game_id].discard(websocket)
            if not self._game_connections[game_id]:
                del self._game_connections[game_id]

    def get_subscribers(self, game_id: int) -> set:
        """Get all subscribers for a game"""
        return self._game_connections.get(game_id, set())

    def broadcast_to_game(
        self,
        game_id: int,
        message_type: NotificationType,
        data: Dict[str, Any],
        turn: Optional[int] = None
    ) -> int:
        """Broadcast a message to all subscribers of a game"""
        message = WebSocketMessage(
            type=message_type,
            game_id=game_id,
            turn=turn,
            data=data
        )

        count = 0
        disconnected = []

        for ws in self.get_subscribers(game_id):
            try:
                # Check if websocket has send_text method
                if hasattr(ws, 'send_text'):
                    import asyncio
                    asyncio.get_event_loop().run_until_complete(ws.send_text(message.to_json()))
                    count += 1
                elif hasattr(ws, 'send'):
                    ws.send(message.to_json())
                    count += 1
            except Exception:
                # Connection is dead, mark for removal
                disconnected.append(ws)

        # Clean up dead connections
        for ws in disconnected:
            self.unsubscribe(ws)

        return count

    def notify_turn_advance(self, game_id: int, turn: int, next_time: str) -> int:
        """Notify that the turn has advanced"""
        return self.broadcast_to_game(
            game_id,
            NotificationType.TURN_ADVANCE,
            {"next_time": next_time, "turn": turn},
            turn
        )

    def notify_order_received(self, game_id: int, turn: int, unit_id: int) -> int:
        """Notify that an order was received"""
        return self.broadcast_to_game(
            game_id,
            NotificationType.ORDER_RECEIVED,
            {"unit_id": unit_id},
            turn
        )

    def notify_sitrep_ready(self, game_id: int, turn: int) -> int:
        """Notify that SITREP is ready"""
        return self.broadcast_to_game(
            game_id,
            NotificationType.SITREP_READY,
            {},
            turn
        )

    def notify_game_update(self, game_id: int, update_type: str, data: Dict[str, Any]) -> int:
        """Notify of a general game update"""
        return self.broadcast_to_game(
            game_id,
            NotificationType.GAME_UPDATE,
            {"update_type": update_type, **data}
        )

    def notify_player_ready(self, game_id: int, username: str, is_ready: bool) -> int:
        """Notify that a player changed ready status"""
        return self.broadcast_to_game(
            game_id,
            NotificationType.PLAYER_READY,
            {"username": username, "is_ready": is_ready}
        )

    def get_connection_count(self, game_id: int) -> int:
        """Get the number of connected clients for a game"""
        return len(self.get_subscribers(game_id))


# Global notification service instance
_notification_service: Optional[NotificationService] = None


def get_notification_service() -> NotificationService:
    """Get the global notification service instance"""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service


# Integration helpers for existing services

def notify_turn_commit_complete(
    game_id: int,
    turn: int,
    next_time: str,
    player_count: int = 0
) -> None:
    """Notify all players that turn commit is complete"""
    service = get_notification_service()
    if player_count > 0 or service.get_connection_count(game_id) > 0:
        service.notify_turn_advance(game_id, turn, next_time)


def notify_sitrep_available(game_id: int, turn: int) -> None:
    """Notify all players that SITREP is available"""
    service = get_notification_service()
    service.notify_sitrep_ready(game_id, turn)
