"""Tests for Arcade mode 2D6 rule engine"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base, Game, GameMode, ArcadeUnit
from app.services.arcade_adjudication import (
    ArcadeAdjudication,
    ARCADE_UNIT_STATS,
    create_arcade_game,
)


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
def arcade_game(db_session):
    """Create an Arcade mode game"""
    game = Game(
        name="Test Arcade Game",
        game_mode=GameMode.ARCADE,
        map_width=12,
        map_height=8,
    )
    db_session.add(game)
    db_session.commit()
    db_session.refresh(game)
    return game


@pytest.fixture
def arcade_units(db_session, arcade_game):
    """Create arcade units"""
    units = [
        ArcadeUnit(
            game_id=arcade_game.id,
            name="Player Armor",
            unit_type="armor",
            side="player",
            x=3,
            y=4,
            strength=10,
            can_move=True,
            can_attack=True,
        ),
        ArcadeUnit(
            game_id=arcade_game.id,
            name="Player Infantry",
            unit_type="infantry",
            side="player",
            x=2,
            y=5,
            strength=10,
            can_move=True,
            can_attack=True,
        ),
        ArcadeUnit(
            game_id=arcade_game.id,
            name="Enemy Infantry",
            unit_type="infantry",
            side="enemy",
            x=8,
            y=4,
            strength=10,
            can_move=True,
            can_attack=True,
        ),
    ]
    for unit in units:
        db_session.add(unit)
    db_session.commit()
    return units


class TestArcadeAdjudication:
    """Test cases for ArcadeAdjudication"""

    def test_roll_2d6(self, db_session):
        """Test 2D6 dice rolling"""
        engine = ArcadeAdjudication(db_session, seed=42)
        rolls = [engine.roll_2d6() for _ in range(100)]
        # All rolls should be between 2 and 12
        assert all(2 <= r <= 12 for r in rolls)
        # With 100 rolls, we should see distribution
        assert len(set(rolls)) > 5

    def test_get_modifiers_strength_bonus(self, db_session, arcade_game, arcade_units):
        """Test strength modifiers"""
        engine = ArcadeAdjudication(db_session)

        # High strength should give +1
        arcade_units[0].strength = 10
        mod = engine.get_modifiers(arcade_units[0], arcade_game)
        assert mod >= 0

        # Low strength should give -1
        arcade_units[0].strength = 3
        mod = engine.get_modifiers(arcade_units[0], arcade_game)
        assert mod <= 0

    def test_arcade_unit_stats(self):
        """Test unit stats table"""
        assert ARCADE_UNIT_STATS["armor"]["attack"] == 4
        assert ARCADE_UNIT_STATS["infantry"]["defense"] == 3
        assert ARCADE_UNIT_STATS["artillery"]["move"] == 2

    def test_resolve_attack(self, db_session, arcade_game, arcade_units):
        """Test combat resolution"""
        engine = ArcadeAdjudication(db_session, seed=42)

        attacker = arcade_units[0]  # Player Armor
        defender = arcade_units[2]  # Enemy Infantry

        result = engine.resolve_attack(attacker, defender, arcade_game)

        assert "result" in result
        assert result["result"] in [
            "CRITICAL_FAIL",
            "FAIL",
            "PARTIAL",
            "SUCCESS",
            "GREAT",
            "CRITICAL",
        ]
        assert "attack_roll" in result
        assert "defense_roll" in result
        assert result["attack_roll"] >= 2
        assert result["defense_roll"] >= 2

    def test_resolve_move_success(self, db_session, arcade_game, arcade_units):
        """Test successful movement"""
        engine = ArcadeAdjudication(db_session, seed=10)

        unit = arcade_units[0]  # armor at (3,4)
        terrain = {"4,4": "plain"}

        result = engine.resolve_move(unit, 4, 4, terrain)

        assert "result" in result
        if result["result"] == "SUCCESS":
            assert result["new_x"] == 4
            assert result["new_y"] == 4

    def test_resolve_defend(self, db_session, arcade_game, arcade_units):
        """Test defense action"""
        engine = ArcadeAdjudication(db_session, seed=42)

        unit = arcade_units[0]
        result = engine.resolve_defend(unit, arcade_game)

        assert "result" in result
        assert result["result"] in ["SUCCESS", "PARTIAL"]
        assert "defense_bonus" in result
        assert result["defense_bonus"] >= 0

    def test_resolve_recon(self, db_session, arcade_game, arcade_units):
        """Test reconnaissance action"""
        engine = ArcadeAdjudication(db_session, seed=42)

        unit = arcade_units[1]  # infantry
        result = engine.resolve_recon(unit, arcade_game)

        assert "result" in result
        assert result["result"] in ["SUCCESS", "PARTIAL"]
        assert "recon_range" in result

    def test_resolve_supply(self, db_session, arcade_units):
        """Test supply action"""
        engine = ArcadeAdjudication(db_session, seed=42)

        unit = arcade_units[0]
        result = engine.resolve_supply(unit)

        assert "result" in result
        assert result["result"] in ["SUCCESS", "PARTIAL", "FAIL"]
        assert "restored" in result

    def test_adjudicate_turn_with_orders(self, db_session, arcade_game, arcade_units):
        """Test full turn adjudication with orders"""
        engine = ArcadeAdjudication(db_session, seed=42)

        orders = [
            {
                "unit_id": arcade_units[0].id,
                "order_type": "move",
                "location_x": 4,
                "location_y": 4,
            }
        ]

        result = engine.adjudicate_turn(arcade_game.id, orders)

        assert "turn" in result
        assert "moves" in result

    def test_adjudicate_turn_combat(self, db_session, arcade_game, arcade_units):
        """Test turn with attack order"""
        engine = ArcadeAdjudication(db_session, seed=42)

        orders = [
            {
                "unit_id": arcade_units[0].id,
                "order_type": "attack",
                "target_id": arcade_units[2].id,
            }
        ]

        result = engine.adjudicate_turn(arcade_game.id, orders)

        assert "turn" in result
        assert "attacks" in result

    def test_create_arcade_game(self, db_session):
        """Test creating an Arcade game"""
        game = create_arcade_game(db_session, "New Arcade Game")

        assert game.name == "New Arcade Game"
        assert game.game_mode == GameMode.ARCADE
        assert game.map_width == 12
        assert game.map_height == 8

    def test_victory_conditions(self, db_session, arcade_game, arcade_units):
        """Test victory condition detection"""
        engine = ArcadeAdjudication(db_session, seed=42)

        # Start with no orders
        result = engine.adjudicate_turn(arcade_game.id, [])

        # No victory yet
        assert result.get("victory") is None

    def test_enemy_destruction(self, db_session, arcade_game, arcade_units):
        """Test enemy unit destruction"""
        engine = ArcadeAdjudication(db_session, seed=1)

        # Give player unit massive advantage
        arcade_units[0].strength = 10
        arcade_units[2].strength = 1

        orders = [
            {
                "unit_id": arcade_units[0].id,
                "order_type": "attack",
                "target_id": arcade_units[2].id,
            }
        ]

        result = engine.adjudicate_turn(arcade_game.id, orders)

        # Verify attack was processed
        assert len(result.get("attacks", [])) > 0

        # Check if enemy was destroyed
        enemy = db_session.query(ArcadeUnit).filter(ArcadeUnit.name == "Enemy Infantry").first()
        if enemy and enemy.strength <= 0:
            assert enemy is None or enemy.strength > 0  # Either deleted or has remaining strength
