# Chat Service - Role-based chat channel management
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import ChatMessage, User, GamePlayer, UserRole
from app.services.rbac_service import RBACService
import logging

logger = logging.getLogger("chat_service")


class ChatService:
    """Service for handling role-based chat messages"""

    VALID_CHANNELS = ["all", "blue", "red", "white", "observer"]

    def __init__(self, db: Session):
        self.db = db
        self.rbac = RBACService(db)

    def create_message(
        self,
        game_id: int,
        user_id: int,
        content: str,
        channel: str = "all",
        turn: Optional[int] = None
    ) -> ChatMessage:
        """Create a new chat message"""
        # Validate channel
        if channel not in self.VALID_CHANNELS:
            channel = "all"

        # Get user info
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")

        # Create message
        message = ChatMessage(
            game_id=game_id,
            user_id=user_id,
            username=user.username,
            content=content,
            channel=channel,
            turn=turn
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)

        logger.info(f"chat_message_created: message_id={message.id}, game_id={game_id}, user_id={user_id}, channel={channel}")

        return message

    def get_messages(
        self,
        game_id: int,
        user_id: int,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get chat messages visible to the user based on their role"""
        # Get user's role in this game
        game_role = self.rbac.get_user_game_role(user_id, game_id)

        # Build query
        query = self.db.query(ChatMessage).filter(ChatMessage.game_id == game_id)

        # Filter by timestamp if provided
        if since:
            query = query.filter(ChatMessage.created_at > since)

        # Filter by channel visibility based on role
        # - blue: sees "all" + "blue"
        # - red: sees "all" + "red"
        # - white: sees all channels
        # - observer: sees "all" + "observer"
        if game_role == "white" or game_role == "admin":
            # White/Admin sees everything
            pass
        elif game_role == "blue":
            query = query.filter(
                (ChatMessage.channel == "all") | (ChatMessage.channel == "blue")
            )
        elif game_role == "red":
            query = query.filter(
                (ChatMessage.channel == "all") | (ChatMessage.channel == "red")
            )
        elif game_role == "observer":
            query = query.filter(
                (ChatMessage.channel == "all") | (ChatMessage.channel == "observer")
            )
        else:
            # Unknown role - only see "all"
            query = query.filter(ChatMessage.channel == "all")

        # Order by created_at desc (newest first), then limit
        query = query.order_by(ChatMessage.created_at.desc()).limit(limit)

        messages = query.all()

        # Convert to dict
        return [
            {
                "id": m.id,
                "game_id": m.game_id,
                "user_id": m.user_id,
                "username": m.username,
                "content": m.content,
                "channel": m.channel,
                "created_at": m.created_at.isoformat() if m.created_at else None,
                "turn": m.turn,
                "read_by": m.read_by
            }
            for m in messages
        ]

    def mark_as_read(self, message_id: int, user_id: int) -> bool:
        """Mark a message as read by a user"""
        message = self.db.query(ChatMessage).filter(ChatMessage.id == message_id).first()

        if not message:
            return False

        # Update read_by
        read_by = message.read_by or {}
        read_by[str(user_id)] = datetime.utcnow().isoformat()
        message.read_by = read_by

        self.db.commit()
        return True

    def can_write(self, user_id: int, game_id: int, channel: str) -> bool:
        """Check if user can write to a specific channel"""
        # Check write_chat permission
        if not self.rbac.has_permission(user_id, game_id, "write_chat"):
            return False

        # Get user's role
        game_role = self.rbac.get_user_game_role(user_id, game_id)

        # Role-based channel restrictions
        if channel == "blue" and game_role != "blue":
            return False
        if channel == "red" and game_role != "red":
            return False
        if channel == "white" and game_role not in ["white", "admin"]:
            return False
        if channel == "observer" and game_role != "observer":
            return False

        return True

    def get_user_unread_count(self, user_id: int, game_id: int) -> int:
        """Get count of unread messages for a user"""
        # This is a simplified version - in production you'd track last_read_at per user
        # For now, return 0 as we don't have per-user read tracking
        return 0

    def delete_message(self, message_id: int, user_id: int, game_id: int) -> bool:
        """Delete a message (only by sender or admin)"""
        message = self.db.query(ChatMessage).filter(ChatMessage.id == message_id).first()

        if not message:
            return False

        # Check if user is sender or admin
        if message.user_id != user_id:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user or user.role != UserRole.ADMIN:
                return False

        self.db.delete(message)
        self.db.commit()
        return True
