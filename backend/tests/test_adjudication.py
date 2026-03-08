"""Tests for rule engine (adjudication.py)"""
import pytest
from app.services.adjudication import RuleEngine
from app.models import Order, Turn, UnitStatus, OrderType, SupplyLevel


class TestRuleEngine:
    """Test cases for RuleEngine"""

    def test_get_game_state(self, db_session, sample_game, player_units):
        """Test getting game state"""
        engine = RuleEngine(db_session)
        state = engine.get_game_state(sample_game.id)

        assert state["game_id"] == sample_game.id
        assert state["turn"] == 1
        assert state["time"] == "06:00"
        assert state["weather"] == "clear"
        assert len(state["units"]) == 2

    def test_get_game_state_not_found(self, db_session):
        """Test getting non-existent game state"""
        engine = RuleEngine(db_session)
        result = engine.get_game_state(999)
        assert "error" in result

    def test_adjudicate_turn_creates_turn(self, db_session, sample_game, player_units, sample_turn):
        """Test that adjudicate_turn creates a turn"""
        engine = RuleEngine(db_session)
        result = engine.adjudicate_turn(sample_game.id)

        assert "turn" in result
        assert result["turn"] == 1

    def test_adjudicate_order_move(self, db_session, sample_game, player_units, sample_turn):
        """Test MOVE order"""
        engine = RuleEngine(db_session)

        order = Order(
            game_id=sample_game.id,
            unit_id=player_units[0].id,
            turn_id=sample_turn.id,
            order_type=OrderType.MOVE,
            intent="Move to new position",
            location_x=20,
            location_y=30
        )
        db_session.add(order)
        db_session.commit()

        result = engine._adjudicate_order(order)

        assert result["outcome"] == "success"
        assert len(result["changes"]) > 0

    def test_adjudicate_order_attack(self, db_session, sample_game, player_units, sample_turn):
        """Test ATTACK order"""
        engine = RuleEngine(db_session)

        order = Order(
            game_id=sample_game.id,
            unit_id=player_units[0].id,
            turn_id=sample_turn.id,
            order_type=OrderType.ATTACK,
            intent="Attack enemy"
        )
        db_session.add(order)
        db_session.commit()

        result = engine._adjudicate_order(order)

        assert result["outcome"] in ["success", "partial", "failed"]

    def test_adjudicate_order_defend(self, db_session, sample_game, player_units, sample_turn):
        """Test DEFEND order"""
        engine = RuleEngine(db_session)

        order = Order(
            game_id=sample_game.id,
            unit_id=player_units[0].id,
            turn_id=sample_turn.id,
            order_type=OrderType.DEFEND,
            intent="Defend position"
        )
        db_session.add(order)
        db_session.commit()

        result = engine._adjudicate_order(order)

        assert result["outcome"] == "success"

    def test_adjudicate_order_recon(self, db_session, sample_game, player_units, sample_turn):
        """Test RECON order"""
        engine = RuleEngine(db_session)

        order = Order(
            game_id=sample_game.id,
            unit_id=player_units[0].id,
            turn_id=sample_turn.id,
            order_type=OrderType.RECON,
            intent="Reconnaissance"
        )
        db_session.add(order)
        db_session.commit()

        result = engine._adjudicate_order(order)

        assert result["outcome"] == "success"

    def test_adjudicate_order_retreat(self, db_session, sample_game, player_units, sample_turn):
        """Test RETREAT order"""
        engine = RuleEngine(db_session)

        original_x = player_units[0].x
        order = Order(
            game_id=sample_game.id,
            unit_id=player_units[0].id,
            turn_id=sample_turn.id,
            order_type=OrderType.RETREAT,
            intent="Retreat"
        )
        db_session.add(order)
        db_session.commit()

        result = engine._adjudicate_order(order)

        assert result["outcome"] == "success"
        # x should decrease (move backwards)
        assert player_units[0].x < original_x

    def test_adjudicate_order_unit_not_found(self, db_session, sample_game, sample_turn):
        """Test order with non-existent unit"""
        engine = RuleEngine(db_session)

        order = Order(
            game_id=sample_game.id,
            unit_id=999,
            turn_id=sample_turn.id,
            order_type=OrderType.MOVE,
            intent="Move"
        )
        db_session.add(order)
        db_session.commit()

        result = engine._adjudicate_order(order)

        assert result["outcome"] == "failed"
        assert "reason" in result

    def test_consume_supplies(self, db_session, player_units):
        """Test supply consumption"""
        engine = RuleEngine(db_session)
        unit = player_units[0]

        # Initial state
        assert unit.ammo == SupplyLevel.FULL
        assert unit.fuel == SupplyLevel.FULL

        engine._consume_supplies(unit)
        db_session.commit()

        # After consumption
        assert unit.ammo == SupplyLevel.DEPLETED
        assert unit.fuel == SupplyLevel.DEPLETED

    def test_advance_time(self, db_session):
        """Test time advancement"""
        engine = RuleEngine(db_session)

        # Test hour progression
        assert engine._advance_time("06:00") == "07:00"
        assert engine._advance_time("23:00") == "00:00"

    def test_process_enemy_activities(self, db_session, sample_game, enemy_units):
        """Test enemy AI activities"""
        engine = RuleEngine(db_session)

        events = engine._process_enemy_activities(sample_game.id)

        assert len(events) > 0
        assert events[0]["type"] == "enemy_move"

    def test_full_turn_with_orders(self, db_session, sample_game, player_units, sample_turn):
        """Test full turn processing with orders"""
        engine = RuleEngine(db_session)

        # Add an order
        order = Order(
            game_id=sample_game.id,
            unit_id=player_units[0].id,
            turn_id=sample_turn.id,
            order_type=OrderType.MOVE,
            intent="Advance",
            location_x=25,
            location_y=25
        )
        db_session.add(order)
        db_session.commit()

        # Run adjudication
        result = engine.adjudicate_turn(sample_game.id)

        assert "turn" in result
        assert "results" in result
        assert len(result["results"]) > 0

    def test_resolve_combat_with_ammo(self, db_session, player_units):
        """Test combat resolution with ammo"""
        engine = RuleEngine(db_session)
        unit = player_units[0]
        unit.ammo = SupplyLevel.FULL
        unit.status = UnitStatus.INTACT

        outcome = engine._resolve_combat(unit)

        assert outcome in ["success", "partial", "failed"]

    def test_resolve_combat_no_ammo(self, db_session, player_units):
        """Test combat resolution without ammo"""
        engine = RuleEngine(db_session)
        unit = player_units[0]
        unit.ammo = SupplyLevel.EXHAUSTED

        outcome = engine._resolve_combat(unit)

        assert outcome == "failed"
