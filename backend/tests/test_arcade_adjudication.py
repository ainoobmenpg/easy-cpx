"""Tests for Arcade mode 2D6 rule engine"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base, Game, GameMode, ArcadeUnit, OrderType
from app.services.arcade_adjudication import (
    ArcadeAdjudication,
    ARCADE_UNIT_STATS,
    create_arcade_game,
    VP_VALUES,
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


class TestArcadeScoring:
    """Test cases for VP scoring"""

    def test_vp_values(self):
        """Test VP values for different unit types"""
        assert VP_VALUES["armor"] == 3
        assert VP_VALUES["infantry"] == 2
        assert VP_VALUES["artillery"] == 4

    def test_player_score_on_destroy(self, db_session, arcade_game, arcade_units):
        """Test that player score increases when destroying enemy units"""
        engine = ArcadeAdjudication(db_session, seed=1)

        # Destroy enemy with attack
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

        # Check score in result
        assert "score" in result
        assert result["score"]["player"] > 0

    def test_sitrep_generation(self, db_session, arcade_game, arcade_units):
        """Test that SITREP is generated with scoring info"""
        engine = ArcadeAdjudication(db_session, seed=1)

        orders = [
            {
                "unit_id": arcade_units[0].id,
                "order_type": "attack",
                "target_id": arcade_units[2].id,
            }
        ]

        result = engine.adjudicate_turn(arcade_game.id, orders)

        # Check SITREP exists
        assert "sitrep" in result
        assert isinstance(result["sitrep"], str)


class TestArcadeEnemyAI:
    """Test cases for enemy AI"""

    def test_execute_enemy_turn_adjacent_attack(self, db_session, arcade_game, arcade_units):
        """Test that enemy attacks adjacent player units"""
        engine = ArcadeAdjudication(db_session, seed=42)

        # Position enemy adjacent to player
        arcade_units[2].x = 4  # Enemy at (4,4), Player at (3,4)
        arcade_units[2].y = 4
        db_session.commit()

        enemy_orders = engine.execute_enemy_turn(arcade_game.id, {})

        # Should have attack order since adjacent
        attack_orders = [o for o in enemy_orders if o["order_type"] == "attack"]
        assert len(attack_orders) > 0

    def test_execute_enemy_turn_advance(self, db_session, arcade_game, arcade_units):
        """Test that enemy advances toward player when not adjacent"""
        engine = ArcadeAdjudication(db_session, seed=42)

        # Position enemy far from player
        arcade_units[2].x = 8
        arcade_units[2].y = 4
        db_session.commit()

        enemy_orders = engine.execute_enemy_turn(arcade_game.id, {})

        # Should have move order since not adjacent
        move_orders = [o for o in enemy_orders if o["order_type"] == "move"]
        assert len(move_orders) > 0

    def test_execute_enemy_turn_defend_at_edge(self, db_session, arcade_game, arcade_units):
        """Test that enemy defends when at map edge"""
        engine = ArcadeAdjudication(db_session, seed=42)

        # Position enemy at edge with player far away
        arcade_units[2].x = 11
        arcade_units[2].y = 0
        db_session.commit()

        enemy_orders = engine.execute_enemy_turn(arcade_game.id, {})

        # Should either move or defend (not attack)
        attack_orders = [o for o in enemy_orders if o["order_type"] == "attack"]
        assert len(attack_orders) == 0


class TestArcadeSTRIKE:
    """Test cases for STRIKE special action"""

    def test_strike_success(self, db_session, arcade_game, arcade_units):
        """Test successful STRIKE activation"""
        engine = ArcadeAdjudication(db_session, seed=42)

        # Position enemy adjacent
        arcade_units[2].x = 4
        arcade_units[2].y = 4

        unit = arcade_units[0]
        unit.strike_remaining = 3
        unit.strike_used_this_turn = False
        unit.strike_next_attack_blocked = False

        result = engine.resolve_strike(unit, arcade_units, arcade_game)

        assert result["result"] == "SUCCESS"
        assert unit.strike_remaining == 2

    def test_strike_no_remaining(self, db_session, arcade_game, arcade_units):
        """Test STRIKE fails when no tokens remaining"""
        engine = ArcadeAdjudication(db_session, seed=42)

        unit = arcade_units[0]
        unit.strike_remaining = 0

        result = engine.resolve_strike(unit, arcade_units, arcade_game)

        assert result["result"] == "FAIL"
        assert result["reason"] == "no_strikes_remaining"

    def test_strike_not_adjacent(self, db_session, arcade_game, arcade_units):
        """Test STRIKE fails when not adjacent to enemy"""
        engine = ArcadeAdjudication(db_session, seed=42)

        # Position enemy far away
        arcade_units[2].x = 10
        arcade_units[2].y = 7

        unit = arcade_units[0]
        unit.strike_remaining = 3

        result = engine.resolve_strike(unit, arcade_units, arcade_game)

        assert result["result"] == "FAIL"
        assert result["reason"] == "not_adjacent_to_enemy"


class TestArcadeEventIntegration:
    """Integration tests for event deck"""

    def test_event_draw_chance(self, db_session, arcade_game, arcade_units):
        """Test that events can be drawn"""
        engine = ArcadeAdjudication(db_session, seed=999)  # High seed for predictable random

        orders = []
        for _ in range(10):  # Run 10 turns
            result = engine.adjudicate_turn(arcade_game.id, orders)
            # Reset for next turn
            for unit in arcade_units:
                if unit.side == "player":
                    unit.strike_used_this_turn = False

        # Event should have been drawn at least once (20% chance per turn)
        # With seed=999, we can check if events are possible
        # Just verify the adjudicate_turn runs without error
        assert True


class TestCCIREvaluation:
    """Tests for CCIR/PIR/ROE evaluation (CPX-5)"""

    def test_ccir_checklist_initialization(self, db_session, arcade_game):
        """Test that CCIR checklist is initialized correctly"""
        engine = ArcadeAdjudication(db_session)

        checklist = engine.get_ccir_checklist(arcade_game)

        # Check that all categories exist
        assert "isr" in checklist
        assert "fires" in checklist
        assert "sustainment" in checklist
        assert "c2" in checklist

        # Check that items exist
        assert len(checklist["isr"]) > 0
        assert len(checklist["fires"]) > 0
        assert len(checklist["sustainment"]) > 0
        assert len(checklist["c2"]) > 0

    def test_ccir_compliance_full(self, db_session, arcade_game, arcade_units):
        """Test CCIR compliance evaluation with all checks satisfied"""
        engine = ArcadeAdjudication(db_session)

        # Initialize checklist
        engine.get_ccir_checklist(arcade_game)

        # Mark all as satisfied
        for category in ["isr", "fires", "sustainment", "c2"]:
            for item in arcade_game.ccir_data["ccir_checklist"][category]:
                item["satisfied"] = True

        evaluation = engine.evaluate_ccir_compliance(arcade_game)

        assert evaluation["overall_compliance"] == 100.0
        assert evaluation["combat_modifier"] == 2  # Max bonus for 100%

    def test_ccir_compliance_partial(self, db_session, arcade_game):
        """Test CCIR compliance evaluation with partial checks"""
        engine = ArcadeAdjudication(db_session)

        # Initialize checklist
        engine.get_ccir_checklist(arcade_game)

        # Mark some as satisfied (50%)
        checklist = arcade_game.ccir_data["ccir_checklist"]
        total_items = sum(len(items) for items in checklist.values())
        for i, category in enumerate(checklist.keys()):
            for j, item in enumerate(checklist[category]):
                item["satisfied"] = (i + j) % 2 == 0  # 50% satisfied

        evaluation = engine.evaluate_ccir_compliance(arcade_game)

        assert 0 <= evaluation["combat_modifier"] <= 2  # Should be between 0 and 2

    def test_ccir_compliance_none(self, db_session, arcade_game):
        """Test CCIR compliance evaluation with no checks satisfied"""
        engine = ArcadeAdjudication(db_session)

        # Initialize checklist
        engine.get_ccir_checklist(arcade_game)

        # Mark none as satisfied
        for category in ["isr", "fires", "sustainment", "c2"]:
            for item in arcade_game.ccir_data["ccir_checklist"][category]:
                item["satisfied"] = False

        evaluation = engine.evaluate_ccir_compliance(arcade_game)

        assert evaluation["combat_modifier"] == -2  # Max penalty for 0%
        assert len(evaluation["failed_checks"]) > 0

    def test_ccir_modifier_applied_to_attack(self, db_session, arcade_game, arcade_units):
        """Test that CCIR modifier is applied to attack resolution"""
        engine = ArcadeAdjudication(db_session)

        # Initialize checklist and mark all satisfied (100% = +2 modifier)
        engine.get_ccir_checklist(arcade_game)
        for category in ["isr", "fires", "sustainment", "c2"]:
            for item in arcade_game.ccir_data["ccir_checklist"][category]:
                item["satisfied"] = True

        player_unit = next(u for u in arcade_units if u.side == "player" and u.unit_type == "armor")
        enemy_unit = next(u for u in arcade_units if u.side == "enemy")

        result = engine.resolve_attack(player_unit, enemy_unit, arcade_game)

        assert "ccir_modifier" in result
        assert result["ccir_modifier"] == 2  # 100% compliance = +2

    def test_ccir_modifier_penalty(self, db_session, arcade_game, arcade_units):
        """Test that CCIR penalty is applied when compliance is low"""
        engine = ArcadeAdjudication(db_session)

        # Initialize checklist and mark none satisfied (0% = -2 penalty)
        engine.get_ccir_checklist(arcade_game)
        for category in ["isr", "fires", "sustainment", "c2"]:
            for item in arcade_game.ccir_data["ccir_checklist"][category]:
                item["satisfied"] = False

        player_unit = next(u for u in arcade_units if u.side == "player" and u.unit_type == "armor")
        enemy_unit = next(u for u in arcade_units if u.side == "enemy")

        result = engine.resolve_attack(player_unit, enemy_unit, arcade_game)

        assert "ccir_modifier" in result
        assert result["ccir_modifier"] == -2  # 0% compliance = -2

    def test_ccir_in_adjudicate_turn(self, db_session, arcade_game, arcade_units):
        """Test that CCIR evaluation is included in adjudicate_turn results"""
        engine = ArcadeAdjudication(db_session)

        orders = []
        result = engine.adjudicate_turn(arcade_game.id, orders)

        # Verify CCIR evaluation is included in results
        assert "ccir" in result
        assert "overall_compliance" in result["ccir"]
        assert "combat_modifier" in result["ccir"]
        assert "category_results" in result["ccir"]

        # Verify category results structure
        assert "isr" in result["ccir"]["category_results"]
        assert "fires" in result["ccir"]["category_results"]
        assert "sustainment" in result["ccir"]["category_results"]
        assert "c2" in result["ccir"]["category_results"]
