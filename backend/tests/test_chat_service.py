# Chat Service Tests
import pytest
from app.models import Base, Game, User, UserRole, GamePlayer
from app.services.chat_service import ChatService
from app.services.auth_service import AuthService


@pytest.fixture
def setup_users(db_session):
    """Create test users with different roles"""
    auth_service = AuthService(db_session)

    # Create users
    blue_user = User(
        username="blue_commander",
        password_hash=auth_service.hash_password("password"),
        role=UserRole.BLUE
    )
    red_user = User(
        username="red_commander",
        password_hash=auth_service.hash_password("password"),
        role=UserRole.RED
    )
    white_user = User(
        username="white_umpire",
        password_hash=auth_service.hash_password("password"),
        role=UserRole.WHITE
    )
    observer_user = User(
        username="observer1",
        password_hash=auth_service.hash_password("password"),
        role=UserRole.OBSERVER
    )

    db_session.add_all([blue_user, red_user, white_user, observer_user])
    db_session.commit()
    db_session.refresh(blue_user)
    db_session.refresh(red_user)
    db_session.refresh(white_user)
    db_session.refresh(observer_user)

    return {
        "blue": blue_user,
        "red": red_user,
        "white": white_user,
        "observer": observer_user
    }


@pytest.fixture
def setup_game_with_players(db_session, sample_game, setup_users):
    """Assign users to the game with different roles"""
    users = setup_users

    # Assign roles to game
    blue_player = GamePlayer(user_id=users["blue"].id, game_id=sample_game.id, role=UserRole.BLUE)
    red_player = GamePlayer(user_id=users["red"].id, game_id=sample_game.id, role=UserRole.RED)
    white_player = GamePlayer(user_id=users["white"].id, game_id=sample_game.id, role=UserRole.WHITE)
    observer_player = GamePlayer(user_id=users["observer"].id, game_id=sample_game.id, role=UserRole.OBSERVER)

    db_session.add_all([blue_player, red_player, white_player, observer_player])
    db_session.commit()

    return {
        "game": sample_game,
        "users": users
    }


class TestChatService:
    """Tests for ChatService"""

    def test_create_message_all_channel(self, db_session, setup_game_with_players):
        """Test creating a message in the 'all' channel"""
        chat_service = ChatService(db_session)
        data = setup_game_with_players
        game = data["game"]
        blue_user = data["users"]["blue"]

        message = chat_service.create_message(
            game_id=game.id,
            user_id=blue_user.id,
            content="Hello everyone!",
            channel="all",
            turn=1
        )

        assert message.id is not None
        assert message.content == "Hello everyone!"
        assert message.channel == "all"
        assert message.user_id == blue_user.id

    def test_create_message_blue_channel(self, db_session, setup_game_with_players):
        """Test creating a message in the blue-only channel"""
        chat_service = ChatService(db_session)
        data = setup_game_with_players
        game = data["game"]
        blue_user = data["users"]["blue"]

        message = chat_service.create_message(
            game_id=game.id,
            user_id=blue_user.id,
            content="Blue team message",
            channel="blue",
            turn=1
        )

        assert message.channel == "blue"

    def test_create_message_invalid_channel(self, db_session, setup_game_with_players):
        """Test that invalid channel defaults to 'all'"""
        chat_service = ChatService(db_session)
        data = setup_game_with_players
        game = data["game"]
        blue_user = data["users"]["blue"]

        message = chat_service.create_message(
            game_id=game.id,
            user_id=blue_user.id,
            content="Test",
            channel="invalid_channel",
            turn=1
        )

        assert message.channel == "all"

    def test_get_messages_all_channel_visible_to_blue(self, db_session, setup_game_with_players):
        """Test that blue can see 'all' channel messages"""
        chat_service = ChatService(db_session)
        data = setup_game_with_players
        game = data["game"]
        blue_user = data["users"]["blue"]

        # Create message in "all" channel
        chat_service.create_message(
            game_id=game.id,
            user_id=blue_user.id,
            content="Public message",
            channel="all",
            turn=1
        )

        # Get messages as blue user
        messages = chat_service.get_messages(game_id=game.id, user_id=blue_user.id)

        assert len(messages) == 1
        assert messages[0]["content"] == "Public message"

    def test_get_messages_blue_cannot_see_red_channel(self, db_session, setup_game_with_players):
        """Test that blue cannot see red channel messages"""
        chat_service = ChatService(db_session)
        data = setup_game_with_players
        game = data["game"]
        blue_user = data["users"]["blue"]
        red_user = data["users"]["red"]

        # Create message in red channel
        chat_service.create_message(
            game_id=game.id,
            user_id=red_user.id,
            content="Red secret message",
            channel="red",
            turn=1
        )

        # Get messages as blue user - should not see red messages
        messages = chat_service.get_messages(game_id=game.id, user_id=blue_user.id)

        assert len(messages) == 0

    def test_get_messages_white_sees_all(self, db_session, setup_game_with_players):
        """Test that white/umpire can see all channels"""
        chat_service = ChatService(db_session)
        data = setup_game_with_players
        game = data["game"]
        blue_user = data["users"]["blue"]
        red_user = data["users"]["red"]
        white_user = data["users"]["white"]

        # Create messages in different channels
        chat_service.create_message(
            game_id=game.id,
            user_id=blue_user.id,
            content="Blue message",
            channel="blue",
            turn=1
        )
        chat_service.create_message(
            game_id=game.id,
            user_id=red_user.id,
            content="Red message",
            channel="red",
            turn=1
        )

        # White should see all
        messages = chat_service.get_messages(game_id=game.id, user_id=white_user.id)

        assert len(messages) == 2

    def test_can_write_blue_to_blue_channel(self, db_session, setup_game_with_players):
        """Test that blue can write to blue channel"""
        chat_service = ChatService(db_session)
        data = setup_game_with_players
        game = data["game"]
        blue_user = data["users"]["blue"]

        can_write = chat_service.can_write(user_id=blue_user.id, game_id=game.id, channel="blue")

        assert can_write is True

    def test_cannot_write_blue_to_red_channel(self, db_session, setup_game_with_players):
        """Test that blue cannot write to red channel"""
        chat_service = ChatService(db_session)
        data = setup_game_with_players
        game = data["game"]
        blue_user = data["users"]["blue"]

        can_write = chat_service.can_write(user_id=blue_user.id, game_id=game.id, channel="red")

        assert can_write is False

    def test_observer_cannot_write(self, db_session, setup_game_with_players):
        """Test that observer cannot write to chat"""
        chat_service = ChatService(db_session)
        data = setup_game_with_players
        game = data["game"]
        observer_user = data["users"]["observer"]

        can_write = chat_service.can_write(user_id=observer_user.id, game_id=game.id, channel="all")

        assert can_write is False

    def test_mark_as_read(self, db_session, setup_game_with_players):
        """Test marking a message as read"""
        chat_service = ChatService(db_session)
        data = setup_game_with_players
        game = data["game"]
        blue_user = data["users"]["blue"]

        message = chat_service.create_message(
            game_id=game.id,
            user_id=blue_user.id,
            content="Test message",
            channel="all",
            turn=1
        )

        success = chat_service.mark_as_read(message.id, blue_user.id)

        assert success is True

    def test_delete_own_message(self, db_session, setup_game_with_players):
        """Test that user can delete their own message"""
        chat_service = ChatService(db_session)
        data = setup_game_with_players
        game = data["game"]
        blue_user = data["users"]["blue"]

        message = chat_service.create_message(
            game_id=game.id,
            user_id=blue_user.id,
            content="Test message to delete",
            channel="all",
            turn=1
        )

        success = chat_service.delete_message(message.id, blue_user.id, game.id)

        assert success is True

    def test_get_messages_with_since_filter(self, db_session, setup_game_with_players):
        """Test filtering messages by timestamp"""
        from datetime import datetime, timedelta

        chat_service = ChatService(db_session)
        data = setup_game_with_players
        game = data["game"]
        blue_user = data["users"]["blue"]

        # Create a message
        message = chat_service.create_message(
            game_id=game.id,
            user_id=blue_user.id,
            content="Old message",
            channel="all",
            turn=1
        )

        # Get messages since after the message was created
        since = datetime.utcnow()
        messages = chat_service.get_messages(game_id=game.id, user_id=blue_user.id, since=since)

        assert len(messages) == 0  # Message was created before 'since'
