# Chat API Routes - Role-based chat channels
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.database import get_db
from app.models import ChatMessage, Game, User
from app.services.chat_service import ChatService
from app.services.auth_service import AuthService, extract_token
from app.services.rbac_service import RBACService
from app.api.websocket_routes import manager
import logging

logger = logging.getLogger("chat_routes")
router = APIRouter()


# Request/Response Models
class ChatMessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)
    channel: str = Field(default="all")


class ChatMessageResponse(BaseModel):
    id: int
    game_id: int
    user_id: int
    username: str
    content: str
    channel: str
    created_at: str
    turn: Optional[int] = None
    read_by: dict = {}

    model_config = {"from_attributes": True}


class ChatMessageListResponse(BaseModel):
    messages: List[ChatMessageResponse]
    total: int


def get_current_user_required(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)) -> User:
    """Dependency that requires authentication"""
    token = extract_token(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")

    auth_service = AuthService(db)
    payload = auth_service.decode_token(token)

    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = int(payload.get("sub"))
    user = auth_service.get_user_by_id(user_id)

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


@router.post("/games/{game_id}/chat", response_model=ChatMessageResponse)
async def create_chat_message(
    game_id: int = Path(..., gt=0),
    message_data: ChatMessageCreate = ...,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_required)
):
    """Post a chat message to a game channel"""
    # Verify game exists
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    # Check access permission
    rbac = RBACService(db)
    if not rbac.can_access_game(user.id, game_id):
        raise HTTPException(status_code=403, detail="Access denied to this game")

    # Check write permission and channel access
    chat_service = ChatService(db)
    if not chat_service.can_write(user.id, game_id, message_data.channel):
        raise HTTPException(
            status_code=403,
            detail=f"Cannot write to {message_data.channel} channel"
        )

    # Create message
    message = chat_service.create_message(
        game_id=game_id,
        user_id=user.id,
        content=message_data.content,
        channel=message_data.channel,
        turn=game.current_turn
    )

    # Broadcast to WebSocket clients in the appropriate room
    ws_message = {
        "type": "chat_message",
        "data": {
            "id": message.id,
            "game_id": message.game_id,
            "user_id": message.user_id,
            "username": message.username,
            "content": message.content,
            "channel": message.channel,
            "created_at": message.created_at.isoformat() if message.created_at else "",
            "turn": message.turn
        }
    }
    await manager.broadcast_to_room(ws_message, game_id, message_data.channel)

    logger.info(f"Chat message created: {message.id} by user {user.id} in game {game_id}")

    return ChatMessageResponse(
        id=message.id,
        game_id=message.game_id,
        user_id=message.user_id,
        username=message.username,
        content=message.content,
        channel=message.channel,
        created_at=message.created_at.isoformat() if message.created_at else "",
        turn=message.turn,
        read_by=message.read_by or {}
    )


@router.get("/games/{game_id}/chat", response_model=ChatMessageListResponse)
async def get_chat_messages(
    game_id: int = Path(..., gt=0),
    since: Optional[str] = Query(None, description="ISO timestamp to get messages after"),
    limit: int = Query(100, le=500, ge=1),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_required)
):
    """Get chat messages for a game (filtered by user role)"""
    # Verify game exists
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    # Check access permission
    rbac = RBACService(db)
    if not rbac.can_access_game(user.id, game_id):
        raise HTTPException(status_code=403, detail="Access denied to this game")

    # Parse since timestamp
    since_dt = None
    if since:
        try:
            since_dt = datetime.fromisoformat(since.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid since timestamp")

    # Get messages
    chat_service = ChatService(db)
    messages = chat_service.get_messages(
        game_id=game_id,
        user_id=user.id,
        since=since_dt,
        limit=limit
    )

    return ChatMessageListResponse(
        messages=[
            ChatMessageResponse(
                id=m["id"],
                game_id=m["game_id"],
                user_id=m["user_id"],
                username=m["username"],
                content=m["content"],
                channel=m["channel"],
                created_at=m["created_at"] or "",
                turn=m["turn"],
                read_by=m["read_by"]
            )
            for m in messages
        ],
        total=len(messages)
    )


@router.delete("/games/{game_id}/chat/{message_id}")
async def delete_chat_message(
    game_id: int = Path(..., gt=0),
    message_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_required)
):
    """Delete a chat message (sender or admin only)"""
    # Verify game exists
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    # Delete message
    chat_service = ChatService(db)
    success = chat_service.delete_message(message_id, user.id, game_id)

    if not success:
        raise HTTPException(status_code=404, detail="Message not found or access denied")

    return {"status": "deleted", "message_id": message_id}


@router.post("/games/{game_id}/chat/{message_id}/read")
async def mark_message_read(
    game_id: int = Path(..., gt=0),
    message_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_required)
):
    """Mark a chat message as read"""
    # Verify game exists
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    # Check access permission
    rbac = RBACService(db)
    if not rbac.can_access_game(user.id, game_id):
        raise HTTPException(status_code=403, detail="Access denied to this game")

    # Mark as read
    chat_service = ChatService(db)
    success = chat_service.mark_as_read(message_id, user.id)

    if not success:
        raise HTTPException(status_code=404, detail="Message not found")

    return {"status": "marked_read", "message_id": message_id}
