import pytest
import sys
import os

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base, Game, Unit, Turn, Order, UnitStatus, OrderType, SupplyLevel


@pytest.fixture
def db_session():
    """Create in-memory SQLite database for testing"""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def sample_game(db_session):
    """Create a sample game"""
    game = Game(name="Test Game", current_turn=1, current_time="06:00", weather="clear")
    db_session.add(game)
    db_session.commit()
    db_session.refresh(game)
    return game


@pytest.fixture
def player_units(db_session, sample_game):
    """Create player units"""
    units = [
        Unit(
            game_id=sample_game.id,
            name="第1大隊",
            unit_type="infantry",
            side="player",
            x=10,
            y=25,
            status=UnitStatus.INTACT,
            ammo=SupplyLevel.FULL,
            fuel=SupplyLevel.FULL,
            readiness=SupplyLevel.FULL
        ),
        Unit(
            game_id=sample_game.id,
            name="第2大隊",
            unit_type="armor",
            side="player",
            x=15,
            y=20,
            status=UnitStatus.INTACT,
            ammo=SupplyLevel.FULL,
            fuel=SupplyLevel.FULL,
            readiness=SupplyLevel.FULL
        ),
    ]
    for unit in units:
        db_session.add(unit)
    db_session.commit()
    return units


@pytest.fixture
def enemy_units(db_session, sample_game):
    """Create enemy units"""
    units = [
        Unit(
            game_id=sample_game.id,
            name="敵主力",
            unit_type="infantry",
            side="enemy",
            x=35,
            y=25,
            status=UnitStatus.INTACT,
            ammo=SupplyLevel.FULL,
            fuel=SupplyLevel.FULL,
            readiness=SupplyLevel.FULL
        ),
    ]
    for unit in units:
        db_session.add(unit)
    db_session.commit()
    return units


@pytest.fixture
def sample_turn(db_session, sample_game):
    """Create a sample turn"""
    turn = Turn(
        game_id=sample_game.id,
        turn_number=1,
        time="06:00",
        weather="clear",
        phase="orders"
    )
    db_session.add(turn)
    db_session.commit()
    db_session.refresh(turn)
    return turn
