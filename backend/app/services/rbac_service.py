# RBAC Service - Role-Based Access Control for multi-role games
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.models import User, GamePlayer, Game, UserRole


class RBACService:
    """Service for handling role-based access control"""

    # Role hierarchy (higher index = more permissions)
    ROLE_HIERARCHY = {
        'admin': 100,
        'white': 50,
        'blue': 30,
        'red': 30,
        'observer': 10,
    }

    # Role permissions
    PERMISSIONS = {
        'blue': {
            'read_own_game': True,
            'write_orders': True,
            'read_sitrep': True,
            'read_allied_units': True,
            'read_enemy_units': False,  # Fog of war
            'read_map': True,
            'read_chat': True,
            'write_chat': True,
        },
        'red': {
            'read_own_game': True,
            'write_orders': True,
            'read_sitrep': True,
            'read_allied_units': True,
            'read_enemy_units': False,  # Fog of war
            'read_map': True,
            'read_chat': True,
            'write_chat': True,
        },
        'white': {
            'read_own_game': True,
            'write_orders': True,
            'read_sitrep': True,
            'read_allied_units': True,
            'read_enemy_units': True,  # Full visibility
            'read_map': True,
            'read_chat': True,
            'write_chat': True,
            'admin_game': True,
        },
        'observer': {
            'read_own_game': True,
            'write_orders': False,
            'read_sitrep': True,
            'read_allied_units': True,
            'read_enemy_units': True,  # Observers see all
            'read_map': True,
            'read_chat': True,
            'write_chat': False,
        },
        'admin': {
            'read_own_game': True,
            'write_orders': True,
            'read_sitrep': True,
            'read_allied_units': True,
            'read_enemy_units': True,
            'read_map': True,
            'read_chat': True,
            'write_chat': True,
            'admin_game': True,
            'admin_system': True,
        },
    }

    def __init__(self, db: Session):
        self.db = db

    def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return self.db.query(User).filter(User.username == username).first()

    def create_user(self, username: str, password_hash: str, role: str = 'observer') -> User:
        """Create a new user"""
        user = User(
            username=username,
            password_hash=password_hash,
            role=UserRole[role.upper()]
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def assign_user_to_game(self, user_id: int, game_id: int, role: str) -> GamePlayer:
        """Assign a user to a game with a specific role"""
        # Check if already assigned
        existing = self.db.query(GamePlayer).filter(
            GamePlayer.user_id == user_id,
            GamePlayer.game_id == game_id
        ).first()

        if existing:
            existing.role = UserRole[role.upper()]
            self.db.commit()
            self.db.refresh(existing)
            return existing

        game_player = GamePlayer(
            user_id=user_id,
            game_id=game_id,
            role=UserRole[role.upper()]
        )
        self.db.add(game_player)
        self.db.commit()
        self.db.refresh(game_player)
        return game_player

    def remove_user_from_game(self, user_id: int, game_id: int) -> bool:
        """Remove a user from a game"""
        game_player = self.db.query(GamePlayer).filter(
            GamePlayer.user_id == user_id,
            GamePlayer.game_id == game_id
        ).first()

        if game_player:
            self.db.delete(game_player)
            self.db.commit()
            return True
        return False

    def get_game_players(self, game_id: int) -> List[Dict[str, Any]]:
        """Get all players assigned to a game"""
        players = self.db.query(GamePlayer, User).join(
            User, GamePlayer.user_id == User.id
        ).filter(GamePlayer.game_id == game_id).all()

        return [
            {
                'user_id': gp.user_id,
                'username': user.username,
                'role': gp.role.value,
                'is_ready': gp.is_ready,
                'joined_at': gp.joined_at.isoformat() if gp.joined_at else None
            }
            for gp, user in players
        ]

    def get_user_game_role(self, user_id: int, game_id: int) -> Optional[str]:
        """Get user's role in a specific game"""
        game_player = self.db.query(GamePlayer).filter(
            GamePlayer.user_id == user_id,
            GamePlayer.game_id == game_id
        ).first()

        return game_player.role.value if game_player else None

    def has_permission(self, user_id: int, game_id: int, permission: str) -> bool:
        """Check if user has specific permission in a game"""
        # Get user's game role
        role = self.get_user_game_role(user_id, game_id)
        if not role:
            # Check if user is admin
            user = self.get_user(user_id)
            if user and user.role == UserRole.ADMIN:
                return self.PERMISSIONS.get('admin', {}).get(permission, False)
            return False

        # Check permission
        role_perms = self.PERMISSIONS.get(role, {})
        return role_perms.get(permission, False)

    def can_read_enemy_units(self, user_id: int, game_id: int) -> bool:
        """Check if user can read enemy unit positions (FoW bypass)"""
        return self.has_permission(user_id, game_id, 'read_enemy_units')

    def can_write_orders(self, user_id: int, game_id: int) -> bool:
        """Check if user can submit orders"""
        return self.has_permission(user_id, game_id, 'write_orders')

    def can_access_game(self, user_id: int, game_id: int) -> bool:
        """Check if user can access a game"""
        # Check if user is assigned to game
        role = self.get_user_game_role(user_id, game_id)
        if role:
            return True

        # Check if user is system admin
        user = self.get_user(user_id)
        return user is not None and user.role == UserRole.ADMIN

    def set_player_ready(self, user_id: int, game_id: int, is_ready: bool) -> bool:
        """Set player ready status"""
        game_player = self.db.query(GamePlayer).filter(
            GamePlayer.user_id == user_id,
            GamePlayer.game_id == game_id
        ).first()

        if game_player:
            game_player.is_ready = is_ready
            self.db.commit()
            return True
        return False

    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users (admin only)"""
        users = self.db.query(User).all()
        return [
            {
                'id': u.id,
                'username': u.username,
                'role': u.role.value,
                'is_active': u.is_active,
                'created_at': u.created_at.isoformat() if u.created_at else None
            }
            for u in users
        ]


# Helper function for checking role in request context
def get_effective_role(user: Optional[User], game_id: Optional[int], db: Session) -> str:
    """Get effective role for a user in a game context"""
    if not user:
        return 'observer'

    # System admin has full access
    if user.role == UserRole.ADMIN:
        return 'admin'

    # Check game-specific role
    if game_id:
        rbac = RBACService(db)
        game_role = rbac.get_user_game_role(user.id, game_id)
        if game_role:
            return game_role

    # Fall back to system role
    return user.role.value
