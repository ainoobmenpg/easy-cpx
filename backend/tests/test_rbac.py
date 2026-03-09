# RBAC Service Tests
import pytest
from app.models import User, GamePlayer, Game, UserRole
from app.services.rbac_service import RBACService


class TestRBACService:
    """Tests for Role-Based Access Control service"""

    @pytest.fixture
    def rbac_service(self, db_session):
        return RBACService(db_session)

    @pytest.fixture
    def user_blue(self, db_session):
        """Create a blue team user"""
        user = User(username="blue_commander", password_hash="hash123", role=UserRole.BLUE)
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    @pytest.fixture
    def user_red(self, db_session):
        """Create a red team user"""
        user = User(username="red_commander", password_hash="hash456", role=UserRole.RED)
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    @pytest.fixture
    def user_white(self, db_session):
        """Create a white team user (umpire)"""
        user = User(username="umpire", password_hash="hash789", role=UserRole.WHITE)
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    @pytest.fixture
    def user_observer(self, db_session):
        """Create an observer user"""
        user = User(username="observer1", password_hash="hash000", role=UserRole.OBSERVER)
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    def test_create_user(self, rbac_service, db_session):
        """Test user creation"""
        user = rbac_service.create_user("testuser", "passwordhash", "blue")

        assert user.username == "testuser"
        assert user.role == UserRole.BLUE
        assert user.is_active is True

    def test_get_user(self, rbac_service, user_blue):
        """Test getting user by ID"""
        user = rbac_service.get_user(user_blue.id)

        assert user is not None
        assert user.username == "blue_commander"
        assert user.role == UserRole.BLUE

    def test_get_user_by_username(self, rbac_service, user_blue):
        """Test getting user by username"""
        user = rbac_service.get_user_by_username("blue_commander")

        assert user is not None
        assert user.id == user_blue.id

    def test_assign_user_to_game(self, rbac_service, user_blue, sample_game):
        """Test assigning user to a game with a role"""
        gp = rbac_service.assign_user_to_game(user_blue.id, sample_game.id, "blue")

        assert gp.user_id == user_blue.id
        assert gp.game_id == sample_game.id
        assert gp.role == UserRole.BLUE

    def test_assign_user_to_game_updates_existing(self, rbac_service, user_blue, sample_game):
        """Test updating existing game player assignment"""
        # First assignment
        rbac_service.assign_user_to_game(user_blue.id, sample_game.id, "blue")

        # Update role
        gp = rbac_service.assign_user_to_game(user_blue.id, sample_game.id, "white")

        assert gp.role == UserRole.WHITE

    def test_remove_user_from_game(self, rbac_service, user_blue, sample_game):
        """Test removing user from a game"""
        rbac_service.assign_user_to_game(user_blue.id, sample_game.id, "blue")

        result = rbac_service.remove_user_from_game(user_blue.id, sample_game.id)

        assert result is True

        # Verify removed
        gp = rbac_service.get_user_game_role(user_blue.id, sample_game.id)
        assert gp is None

    def test_get_game_players(self, rbac_service, user_blue, user_red, user_white, sample_game):
        """Test getting all players in a game"""
        rbac_service.assign_user_to_game(user_blue.id, sample_game.id, "blue")
        rbac_service.assign_user_to_game(user_red.id, sample_game.id, "red")
        rbac_service.assign_user_to_game(user_white.id, sample_game.id, "white")

        players = rbac_service.get_game_players(sample_game.id)

        assert len(players) == 3
        roles = [p["role"] for p in players]
        assert "blue" in roles
        assert "red" in roles
        assert "white" in roles

    def test_get_user_game_role(self, rbac_service, user_blue, sample_game):
        """Test getting user's role in a game"""
        rbac_service.assign_user_to_game(user_blue.id, sample_game.id, "blue")

        role = rbac_service.get_user_game_role(user_blue.id, sample_game.id)

        assert role == "blue"

    def test_has_permission_blue_cannot_read_enemy_units(self, rbac_service, user_blue, sample_game):
        """Test that blue team cannot read enemy units (Fog of War)"""
        rbac_service.assign_user_to_game(user_blue.id, sample_game.id, "blue")

        can_read = rbac_service.has_permission(user_blue.id, sample_game.id, "read_enemy_units")

        assert can_read is False

    def test_has_permission_white_can_read_enemy_units(self, rbac_service, user_white, sample_game):
        """Test that white team can read enemy units (full visibility)"""
        rbac_service.assign_user_to_game(user_white.id, sample_game.id, "white")

        can_read = rbac_service.has_permission(user_white.id, sample_game.id, "read_enemy_units")

        assert can_read is True

    def test_has_permission_observer_can_read_enemy_units(self, rbac_service, user_observer, sample_game):
        """Test that observer can read enemy units"""
        rbac_service.assign_user_to_game(user_observer.id, sample_game.id, "observer")

        can_read = rbac_service.has_permission(user_observer.id, sample_game.id, "read_enemy_units")

        assert can_read is True

    def test_can_write_orders_blue(self, rbac_service, user_blue, sample_game):
        """Test that blue can write orders"""
        rbac_service.assign_user_to_game(user_blue.id, sample_game.id, "blue")

        can_write = rbac_service.can_write_orders(user_blue.id, sample_game.id)

        assert can_write is True

    def test_cannot_write_orders_observer(self, rbac_service, user_observer, sample_game):
        """Test that observer cannot write orders"""
        rbac_service.assign_user_to_game(user_observer.id, sample_game.id, "observer")

        can_write = rbac_service.can_write_orders(user_observer.id, sample_game.id)

        assert can_write is False

    def test_can_access_game_assigned(self, rbac_service, user_blue, sample_game):
        """Test that assigned user can access game"""
        rbac_service.assign_user_to_game(user_blue.id, sample_game.id, "blue")

        can_access = rbac_service.can_access_game(user_blue.id, sample_game.id)

        assert can_access is True

    def test_cannot_access_game_not_assigned(self, rbac_service, user_observer, sample_game):
        """Test that non-assigned user cannot access game"""
        can_access = rbac_service.can_access_game(user_observer.id, sample_game.id)

        assert can_access is False

    def test_set_player_ready(self, rbac_service, user_blue, sample_game):
        """Test setting player ready status"""
        rbac_service.assign_user_to_game(user_blue.id, sample_game.id, "blue")

        result = rbac_service.set_player_ready(user_blue.id, sample_game.id, True)

        assert result is True

        # Verify
        players = rbac_service.get_game_players(sample_game.id)
        blue_player = next(p for p in players if p["user_id"] == user_blue.id)
        assert blue_player["is_ready"] is True

    def test_get_all_users(self, rbac_service, user_blue, user_red, user_white):
        """Test getting all users"""
        users = rbac_service.get_all_users()

        usernames = [u["username"] for u in users]
        assert "blue_commander" in usernames
        assert "red_commander" in usernames
        assert "umpire" in usernames


class TestRolePermissions:
    """Tests for role permission definitions"""

    def test_blue_permissions(self):
        """Test blue team permissions"""
        perms = RBACService.PERMISSIONS["blue"]

        assert perms["read_own_game"] is True
        assert perms["write_orders"] is True
        assert perms["read_enemy_units"] is False  # Fog of War

    def test_red_permissions(self):
        """Test red team permissions"""
        perms = RBACService.PERMISSIONS["red"]

        assert perms["read_own_game"] is True
        assert perms["write_orders"] is True
        assert perms["read_enemy_units"] is False  # Fog of War

    def test_white_permissions(self):
        """Test white team permissions"""
        perms = RBACService.PERMISSIONS["white"]

        assert perms["read_own_game"] is True
        assert perms["write_orders"] is True
        assert perms["read_enemy_units"] is True  # Full visibility
        assert perms["admin_game"] is True

    def test_observer_permissions(self):
        """Test observer permissions"""
        perms = RBACService.PERMISSIONS["observer"]

        assert perms["read_own_game"] is True
        assert perms["write_orders"] is False
        assert perms["read_enemy_units"] is True  # Full visibility (observer)
        assert perms["write_chat"] is False

    def test_admin_permissions(self):
        """Test admin permissions"""
        perms = RBACService.PERMISSIONS["admin"]

        assert perms["admin_system"] is True
        assert perms["admin_game"] is True
        assert perms["write_orders"] is True


class TestNotificationService:
    """Tests for notification service"""

    def test_notification_service_creation(self):
        """Test creating notification service"""
        from app.services.notification_service import NotificationService, get_notification_service

        service = NotificationService()

        assert service is not None
        assert service.get_connection_count(999) == 0

    def test_get_global_notification_service(self):
        """Test getting global notification service"""
        from app.services.notification_service import get_notification_service

        service1 = get_notification_service()
        service2 = get_notification_service()

        # Same instance
        assert service1 is service2

    def test_subscribe_unsubscribe(self):
        """Test subscribing and unsubscribing"""
        from app.services.notification_service import NotificationService

        service = NotificationService()

        # Mock websocket
        class MockWS:
            pass

        ws = MockWS()

        service.subscribe(1, ws)
        assert service.get_connection_count(1) == 1

        service.unsubscribe(ws)
        assert service.get_connection_count(1) == 0

    def test_broadcast_message(self):
        """Test broadcasting messages"""
        from app.services.notification_service import NotificationService, NotificationType

        service = NotificationService()

        class MockWS:
            def __init__(self):
                self.sent = []

            def send(self, msg):
                self.sent.append(msg)

        ws1 = MockWS()
        ws2 = MockWS()

        service.subscribe(1, ws1)
        service.subscribe(1, ws2)

        service.broadcast_to_game(1, NotificationType.TURN_ADVANCE, {"turn": 2})

        assert len(ws1.sent) == 1
        assert len(ws2.sent) == 1
