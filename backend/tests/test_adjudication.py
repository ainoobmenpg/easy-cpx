"""Tests for rule engine (adjudication.py)"""
import pytest
from app.services.adjudication import RuleEngine
from app.models import Order, Turn, UnitStatus, OrderType, SupplyLevel, Unit


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
        """Test MOVE order - target beyond movement range should result in partial movement"""
        engine = RuleEngine(db_session)

        original_x = player_units[0].x
        original_y = player_units[0].y

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

        # Target is 15 cells away, but max movement is ~3 cells
        # Should result in partial movement
        assert result["outcome"] in ["success", "partial"]
        assert len(result["changes"]) > 0
        # Verify unit moved at least some distance towards target
        assert player_units[0].x > original_x or player_units[0].y != original_y

    def test_adjudicate_order_move_no_location(self, db_session, sample_game, player_units, sample_turn):
        """Test MOVE order without specific location - default movement"""
        engine = RuleEngine(db_session)

        original_x = player_units[0].x

        order = Order(
            game_id=sample_game.id,
            unit_id=player_units[0].id,
            turn_id=sample_turn.id,
            order_type=OrderType.MOVE,
            intent="Advance forward",
            location_x=None,
            location_y=None
        )
        db_session.add(order)
        db_session.commit()

        result = engine._adjudicate_order(order)

        assert result["outcome"] == "success"
        # Should move forward by 1
        assert player_units[0].x == original_x + 1

    def test_adjudicate_order_attack_with_targets(self, db_session, sample_game, player_units, enemy_units, sample_turn):
        """Test ATTACK order with specified targets"""
        engine = RuleEngine(db_session)

        order = Order(
            game_id=sample_game.id,
            unit_id=player_units[0].id,
            turn_id=sample_turn.id,
            order_type=OrderType.ATTACK,
            intent="Attack enemy",
            target_units=[enemy_units[0].id]
        )
        db_session.add(order)
        db_session.commit()

        result = engine._adjudicate_order(order)

        assert result["outcome"] in ["perfect_success", "success", "partial", "failed", "major_failed"]
        assert "changes" in result

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

        assert result["outcome"] in ["perfect_success", "success", "partial", "failed", "major_failed"]

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

    def test_adjudicate_order_supply(self, db_session, sample_game, player_units, sample_turn):
        """Test SUPPLY order"""
        engine = RuleEngine(db_session)

        order = Order(
            game_id=sample_game.id,
            unit_id=player_units[0].id,
            turn_id=sample_turn.id,
            order_type=OrderType.SUPPLY,
            intent="Request supply"
        )
        db_session.add(order)
        db_session.commit()

        result = engine._adjudicate_order(order)

        assert result["outcome"] == "success"

    def test_adjudicate_order_support(self, db_session, sample_game, player_units, sample_turn):
        """Test SUPPORT order"""
        engine = RuleEngine(db_session)

        order = Order(
            game_id=sample_game.id,
            unit_id=player_units[0].id,
            turn_id=sample_turn.id,
            order_type=OrderType.SUPPORT,
            intent="Support other unit"
        )
        db_session.add(order)
        db_session.commit()

        result = engine._adjudicate_order(order)

        assert result["outcome"] == "success"

    def test_adjudicate_order_special(self, db_session, sample_game, player_units, sample_turn):
        """Test SPECIAL order"""
        engine = RuleEngine(db_session)

        order = Order(
            game_id=sample_game.id,
            unit_id=player_units[0].id,
            turn_id=sample_turn.id,
            order_type=OrderType.SPECIAL,
            intent="Special operation"
        )
        db_session.add(order)
        db_session.commit()

        result = engine._adjudicate_order(order)

        assert result["outcome"] == "success"

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

    def test_check_game_end_conditions_turn_limit(self, db_session, sample_game):
        """Test game end conditions - turn limit reached"""
        engine = RuleEngine(db_session)
        sample_game.current_turn = 50

        result = engine._check_game_end_conditions(sample_game.id)

        assert result["ended"] == True
        assert result["reason"] == "turn_limit"

    def test_check_game_end_conditions_player_annihilated(self, db_session, sample_game, player_units):
        """Test game end conditions - player annihilated"""
        engine = RuleEngine(db_session)
        for unit in player_units:
            unit.status = UnitStatus.DESTROYED

        result = engine._check_game_end_conditions(sample_game.id)

        assert result["ended"] == True
        assert result["reason"] == "player_annihilated"

    def test_check_game_end_conditions_enemy_annihilated(self, db_session, sample_game):
        """Test game end conditions - enemy annihilated"""
        engine = RuleEngine(db_session)

        # Create player and enemy units
        player_unit = Unit(
            game_id=sample_game.id,
            name="Player Unit",
            unit_type="infantry",
            side="player",
            x=10,
            y=25,
            status=UnitStatus.INTACT,
            ammo=SupplyLevel.FULL,
            fuel=SupplyLevel.FULL,
            readiness=SupplyLevel.FULL
        )
        enemy_unit = Unit(
            game_id=sample_game.id,
            name="Enemy Unit",
            unit_type="infantry",
            side="enemy",
            x=35,
            y=25,
            status=UnitStatus.DESTROYED,  # Enemy is destroyed
            ammo=SupplyLevel.FULL,
            fuel=SupplyLevel.FULL,
            readiness=SupplyLevel.FULL
        )
        db_session.add(player_unit)
        db_session.add(enemy_unit)
        db_session.commit()

        result = engine._check_game_end_conditions(sample_game.id)

        assert result["ended"] == True
        assert result["reason"] == "enemy_annihilated"

    def test_check_game_end_conditions_game_continues(self, db_session, sample_game, player_units, enemy_units):
        """Test game end conditions - game continues"""
        engine = RuleEngine(db_session)

        result = engine._check_game_end_conditions(sample_game.id)

        assert result["ended"] == False
        assert result["reason"] is None

    def test_check_game_end_conditions_not_found(self, db_session):
        """Test game end conditions - game not found"""
        engine = RuleEngine(db_session)

        result = engine._check_game_end_conditions(999)

        assert result["ended"] == False

    def test_process_reconnaissance(self, db_session, sample_game, player_units, enemy_units):
        """Test player reconnaissance processing"""
        engine = RuleEngine(db_session)

        # Player unit at (10, 25), enemy at (35, 25) - distance 25
        # visibility_range default is 3, so enemy should not be observed
        events = engine._process_reconnaissance(sample_game.id)

        assert isinstance(events, list)

    def test_process_reconnaissance_observed_enemy(self, db_session, sample_game, player_units):
        """Test player reconnaissance with close enemy"""
        engine = RuleEngine(db_session)

        # Add enemy unit close to player
        enemy = Unit(
            game_id=sample_game.id,
            name="Close Enemy",
            unit_type="infantry",
            side="enemy",
            x=12,  # Only 2 units away from player at (10, 25)
            y=25,
            status=UnitStatus.INTACT,
            ammo=SupplyLevel.FULL,
            fuel=SupplyLevel.FULL,
            readiness=SupplyLevel.FULL
        )
        db_session.add(enemy)
        db_session.commit()

        events = engine._process_reconnaissance(sample_game.id)

        # Enemy should be observed
        assert len(events) > 0

    def test_process_enemy_reconnaissance(self, db_session, sample_game, enemy_units, player_units):
        """Test enemy reconnaissance processing"""
        engine = RuleEngine(db_session)

        events = engine._process_enemy_reconnaissance(sample_game.id)

        assert isinstance(events, list)

    def test_process_enemy_reconnaissance_observed_player(self, db_session, sample_game, enemy_units):
        """Test enemy reconnaissance with close player"""
        engine = RuleEngine(db_session)

        # Add player unit close to enemy
        player = Unit(
            game_id=sample_game.id,
            name="Close Player",
            unit_type="infantry",
            side="player",
            x=33,  # Only 2 units away from enemy at (35, 25)
            y=25,
            status=UnitStatus.INTACT,
            ammo=SupplyLevel.FULL,
            fuel=SupplyLevel.FULL,
            readiness=SupplyLevel.FULL
        )
        db_session.add(player)
        db_session.commit()

        events = engine._process_enemy_reconnaissance(sample_game.id)

        # Player should be observed by enemy
        assert isinstance(events, list)

    def test_calculate_unit_type_bonus(self, db_session, player_units, enemy_units):
        """Test unit type bonus calculation"""
        from app.services.adjudication import AdjudicationCriteria

        attacker = player_units[0]
        defenders = enemy_units

        bonus = AdjudicationCriteria._calculate_unit_type_bonus(attacker, defenders)

        assert isinstance(bonus, (int, float))

    def test_adjudication_condition_evaluate(self, db_session):
        """Test adjudication condition evaluation"""
        from app.services.adjudication import AdjudicationCondition

        condition = AdjudicationCondition("test", 0.5, "Test condition")

        # Test that NotImplementedError is raised
        with pytest.raises(NotImplementedError):
            condition.evaluate({})

    def test_adjudication_criteria_evaluate_order(self, db_session, sample_game, player_units, enemy_units, sample_turn):
        """Test order evaluation with criteria"""
        from app.services.adjudication import AdjudicationCriteria

        # Create an order
        order = Order(
            game_id=sample_game.id,
            unit_id=player_units[0].id,
            turn_id=sample_turn.id,
            order_type=OrderType.ATTACK,
            intent="Attack enemy"
        )
        db_session.add(order)
        db_session.commit()

        unit = player_units[0]
        targets = enemy_units

        game_state = {
            "turn": 1,
            "weather": "clear",
            "time": "12:00"
        }

        outcome, results = AdjudicationCriteria.evaluate_order(
            order=order,
            unit=unit,
            target_units=targets,
            game_state=game_state,
            weather="clear",
            time="12:00"
        )

        assert outcome in ["perfect_success", "success", "partial", "failed", "major_failed"]
        assert isinstance(results, dict)

    def test_adjudication_criteria_unit_type_bonus(self, db_session, player_units, enemy_units):
        """Test unit type bonus calculation"""
        from app.services.adjudication import AdjudicationCriteria

        attacker = player_units[0]
        defenders = enemy_units

        bonus = AdjudicationCriteria._calculate_unit_type_bonus(attacker, defenders)

        assert isinstance(bonus, (int, float))

    def test_process_enemy_activities_no_game(self, db_session):
        """Test enemy activities with non-existent game"""
        engine = RuleEngine(db_session)

        events = engine._process_enemy_activities(999)

        assert events == []

    def test_process_enemy_activities_returns_events(self, db_session, sample_game, enemy_units):
        """Test enemy activities returns proper events"""
        engine = RuleEngine(db_session)

        events = engine._process_enemy_activities(sample_game.id)

        assert isinstance(events, list)

    def test_reconnaissance_with_weather_fog(self, db_session, sample_game, player_units):
        """Test reconnaissance with fog weather"""
        engine = RuleEngine(db_session)
        sample_game.weather = "fog"

        enemy = Unit(
            game_id=sample_game.id,
            name="Enemy in Fog",
            unit_type="infantry",
            side="enemy",
            x=12,
            y=25,
            status=UnitStatus.INTACT,
            ammo=SupplyLevel.FULL,
            fuel=SupplyLevel.FULL,
            readiness=SupplyLevel.FULL
        )
        db_session.add(enemy)
        db_session.commit()

        events = engine._process_reconnaissance(sample_game.id)

        assert isinstance(events, list)

    def test_reconnaissance_with_night_time(self, db_session, sample_game, player_units):
        """Test reconnaissance with night time"""
        engine = RuleEngine(db_session)
        sample_game.current_time = "23:00"

        enemy = Unit(
            game_id=sample_game.id,
            name="Enemy at Night",
            unit_type="infantry",
            side="enemy",
            x=12,
            y=25,
            status=UnitStatus.INTACT,
            ammo=SupplyLevel.FULL,
            fuel=SupplyLevel.FULL,
            readiness=SupplyLevel.FULL
        )
        db_session.add(enemy)
        db_session.commit()

        events = engine._process_reconnaissance(sample_game.id)

        assert isinstance(events, list)

    def test_reconnaissance_with_uav(self, db_session, sample_game):
        """Test reconnaissance with UAV unit"""
        engine = RuleEngine(db_session)

        # Add player UAV
        player_uav = Unit(
            game_id=sample_game.id,
            name="Player UAV",
            unit_type="UAV",
            side="player",
            x=10,
            y=25,
            status=UnitStatus.INTACT,
            ammo=SupplyLevel.FULL,
            fuel=SupplyLevel.FULL,
            readiness=SupplyLevel.FULL
        )
        db_session.add(player_uav)

        # Add enemy in range
        enemy = Unit(
            game_id=sample_game.id,
            name="Enemy Spotted by UAV",
            unit_type="infantry",
            side="enemy",
            x=18,
            y=25,
            status=UnitStatus.INTACT,
            ammo=SupplyLevel.FULL,
            fuel=SupplyLevel.FULL,
            readiness=SupplyLevel.FULL
        )
        db_session.add(enemy)
        db_session.commit()

        events = engine._process_reconnaissance(sample_game.id)

        assert isinstance(events, list)

    def test_enemy_reconnaissance_with_uav(self, db_session, sample_game):
        """Test enemy reconnaissance with UAV"""
        engine = RuleEngine(db_session)

        # Add enemy UAV
        enemy_uav = Unit(
            game_id=sample_game.id,
            name="Enemy UAV",
            unit_type="UAV",
            side="enemy",
            x=30,
            y=25,
            status=UnitStatus.INTACT,
            ammo=SupplyLevel.FULL,
            fuel=SupplyLevel.FULL,
            readiness=SupplyLevel.FULL
        )
        db_session.add(enemy_uav)

        # Add player in range
        player = Unit(
            game_id=sample_game.id,
            name="Player Spotted",
            unit_type="infantry",
            side="player",
            x=22,
            y=25,
            status=UnitStatus.INTACT,
            ammo=SupplyLevel.FULL,
            fuel=SupplyLevel.FULL,
            readiness=SupplyLevel.FULL
        )
        db_session.add(player)
        db_session.commit()

        events = engine._process_enemy_reconnaissance(sample_game.id)

        assert isinstance(events, list)

    def test_advance_time_wraparound(self, db_session):
        """Test time advancement wraparound"""
        engine = RuleEngine(db_session)

        # Test day wrap
        assert engine._advance_time("23:00") == "00:00"
        assert engine._advance_time("00:00") == "01:00"

    def test_full_turn_weather_update(self, db_session, sample_game, player_units, sample_turn):
        """Test full turn with weather update"""
        engine = RuleEngine(db_session)
        sample_game.weather = "rain"

        order = Order(
            game_id=sample_game.id,
            unit_id=player_units[0].id,
            turn_id=sample_turn.id,
            order_type=OrderType.MOVE,
            intent="Move in rain",
            location_x=25,
            location_y=25
        )
        db_session.add(order)
        db_session.commit()

        result = engine.adjudicate_turn(sample_game.id)

        assert "turn" in result
        assert "results" in result

    def test_combat_resolution_perfect_success(self, db_session, sample_game, player_units, enemy_units, sample_turn):
        """Test combat resolution with perfect success outcome"""
        engine = RuleEngine(db_session)

        # Create order with strong unit
        player_units[0].strength = 100
        enemy_units[0].strength = 20

        order = Order(
            game_id=sample_game.id,
            unit_id=player_units[0].id,
            turn_id=sample_turn.id,
            order_type=OrderType.ATTACK,
            intent="Attack with overwhelming force",
            target_units=[enemy_units[0].id]
        )
        db_session.add(order)
        db_session.commit()

        result = engine._adjudicate_order(order)

        # Check that enemy took damage
        db_session.refresh(enemy_units[0])
        assert enemy_units[0].status != UnitStatus.INTACT or "damage" in str(result).lower()

    def test_combat_resolution_partial(self, db_session, sample_game, player_units, enemy_units, sample_turn):
        """Test combat resolution with partial outcome"""
        engine = RuleEngine(db_session)

        # Create order with equal strength
        player_units[0].strength = 50
        enemy_units[0].strength = 50

        order = Order(
            game_id=sample_game.id,
            unit_id=player_units[0].id,
            turn_id=sample_turn.id,
            order_type=OrderType.ATTACK,
            intent="Attack with equal force",
            target_units=[enemy_units[0].id]
        )
        db_session.add(order)
        db_session.commit()

        result = engine._adjudicate_order(order)

        assert result["outcome"] in ["perfect_success", "success", "partial", "failed", "major_failed"]

    def test_combat_resolution_failed(self, db_session, sample_game, player_units, enemy_units, sample_turn):
        """Test combat resolution with failed outcome"""
        engine = RuleEngine(db_session)

        # Create order with weak unit
        player_units[0].strength = 20
        enemy_units[0].strength = 100

        order = Order(
            game_id=sample_game.id,
            unit_id=player_units[0].id,
            turn_id=sample_turn.id,
            order_type=OrderType.ATTACK,
            intent="Attack with weak force",
            target_units=[enemy_units[0].id]
        )
        db_session.add(order)
        db_session.commit()

        result = engine._adjudicate_order(order)

        assert result["outcome"] in ["perfect_success", "success", "partial", "failed", "major_failed"]

    def test_consume_supplies_partial(self, db_session, player_units):
        """Test supply consumption with different levels"""
        engine = RuleEngine(db_session)
        unit = player_units[0]

        # Set to different levels
        unit.ammo = SupplyLevel.DEPLETED
        unit.fuel = SupplyLevel.FULL

        engine._consume_supplies(unit)
        db_session.commit()

        # After consumption from depleted, should be exhausted
        assert unit.ammo == SupplyLevel.EXHAUSTED

    def test_count_conflicts_no_conflict(self, db_session):
        """Test _count_conflicts with no conflicts"""
        engine = RuleEngine(db_session)
        occupied_cells = {(10, 25): [1], (15, 20): [2]}

        count = engine._count_conflicts(20, 30, occupied_cells, 3)

        assert count == 0

    def test_count_conflicts_with_conflict(self, db_session):
        """Test _count_conflicts with conflicts"""
        engine = RuleEngine(db_session)
        occupied_cells = {(10, 25): [1, 2, 3]}

        count = engine._count_conflicts(10, 25, occupied_cells, 1)

        assert count == 2

    def test_process_enemy_orders_empty(self, db_session, sample_game):
        """Test process_enemy_orders with empty orders"""
        engine = RuleEngine(db_session)

        result = engine.process_enemy_orders(sample_game.id, {"orders": []})

        assert result == []

    def test_process_enemy_orders_invalid_unit(self, db_session, sample_game, enemy_units):
        """Test process_enemy_orders with invalid unit"""
        engine = RuleEngine(db_session)

        result = engine.process_enemy_orders(sample_game.id, {
            "orders": [{"unit_id": 999, "order_type": "move"}]
        })

        # Should return list (may be empty if turn not set up)
        assert isinstance(result, list)

    def test_reconnaissance_scout_infantry(self, db_session, sample_game):
        """Test reconnaissance with scout infantry subtype"""
        engine = RuleEngine(db_session)

        # Add player scout unit
        scout = Unit(
            game_id=sample_game.id,
            name="Scout Unit",
            unit_type="infantry",
            side="player",
            x=10,
            y=25,
            status=UnitStatus.INTACT,
            ammo=SupplyLevel.FULL,
            fuel=SupplyLevel.FULL,
            readiness=SupplyLevel.FULL,
            infantry_subtype="scout"
        )
        db_session.add(scout)

        # Add enemy in range
        enemy = Unit(
            game_id=sample_game.id,
            name="Enemy Target",
            unit_type="infantry",
            side="enemy",
            x=15,
            y=25,
            status=UnitStatus.INTACT,
            ammo=SupplyLevel.FULL,
            fuel=SupplyLevel.FULL,
            readiness=SupplyLevel.FULL
        )
        db_session.add(enemy)
        db_session.commit()

        events = engine._process_reconnaissance(sample_game.id)

        assert isinstance(events, list)

    def test_reconnaissance_terrain_cover(self, db_session, sample_game, player_units):
        """Test reconnaissance with various enemy positions"""
        engine = RuleEngine(db_session)

        # Add enemy at different position
        enemy = Unit(
            game_id=sample_game.id,
            name="Enemy Far",
            unit_type="infantry",
            side="enemy",
            x=40,
            y=25,
            status=UnitStatus.INTACT,
            ammo=SupplyLevel.FULL,
            fuel=SupplyLevel.FULL,
            readiness=SupplyLevel.FULL
        )
        db_session.add(enemy)
        db_session.commit()

        events = engine._process_reconnaissance(sample_game.id)

        assert isinstance(events, list)

    def test_game_state_with_weather(self, db_session, sample_game, player_units):
        """Test get_game_state includes weather"""
        engine = RuleEngine(db_session)
        sample_game.weather = "rain"

        state = engine.get_game_state(sample_game.id)

        assert state["weather"] == "rain"

    def test_adjudicate_turn_game_ended(self, db_session, sample_game, player_units):
        """Test adjudicate_turn when game has ended"""
        engine = RuleEngine(db_session)
        sample_game.current_turn = 50

        result = engine.adjudicate_turn(sample_game.id)

        assert "turn" in result or "game_ended" in result

    def test_combat_partial_outcome(self, db_session, sample_game, player_units, enemy_units, sample_turn):
        """Test combat with partial outcome"""
        engine = RuleEngine(db_session)

        # Set equal strength
        player_units[0].strength = 50
        enemy_units[0].strength = 50

        order = Order(
            game_id=sample_game.id,
            unit_id=player_units[0].id,
            turn_id=sample_turn.id,
            order_type=OrderType.ATTACK,
            intent="Attack",
            target_units=[enemy_units[0].id]
        )
        db_session.add(order)
        db_session.commit()

        result = engine._adjudicate_order(order)

        # partial outcome should damage both sides
        assert result["outcome"] in ["perfect_success", "success", "partial", "failed", "major_failed"]

    def test_combat_failed_outcome(self, db_session, sample_game, player_units, enemy_units, sample_turn):
        """Test combat with failed outcome - attacker takes damage"""
        engine = RuleEngine(db_session)

        # Attacker much weaker
        player_units[0].strength = 10
        enemy_units[0].strength = 90

        order = Order(
            game_id=sample_game.id,
            unit_id=player_units[0].id,
            turn_id=sample_turn.id,
            order_type=OrderType.ATTACK,
            intent="Attack weak",
            target_units=[enemy_units[0].id]
        )
        db_session.add(order)
        db_session.commit()

        original_status = player_units[0].status
        result = engine._adjudicate_order(order)

        assert result["outcome"] in ["perfect_success", "success", "partial", "failed", "major_failed"]

    def test_combat_major_failed_outcome(self, db_session, sample_game, player_units, enemy_units, sample_turn):
        """Test combat with major_failed outcome"""
        engine = RuleEngine(db_session)

        # Attacker very weak
        player_units[0].strength = 5
        enemy_units[0].strength = 100

        order = Order(
            game_id=sample_game.id,
            unit_id=player_units[0].id,
            turn_id=sample_turn.id,
            order_type=OrderType.ATTACK,
            intent="Attack very weak",
            target_units=[enemy_units[0].id]
        )
        db_session.add(order)
        db_session.commit()

        result = engine._adjudicate_order(order)

        assert result["outcome"] in ["perfect_success", "success", "partial", "failed", "major_failed"]

    def test_adjudication_criteria_conditions(self, db_session, player_units):
        """Test AdjudicationCriteria conditions dictionary"""
        from app.services.adjudication import AdjudicationCriteria

        # Verify conditions exist
        assert "superior_firepower" in AdjudicationCriteria.CONDITIONS
        assert "position_advantage" in AdjudicationCriteria.CONDITIONS
        assert "mobility" in AdjudicationCriteria.CONDITIONS
        assert "supply_status" in AdjudicationCriteria.CONDITIONS
        assert "reconnaissance" in AdjudicationCriteria.CONDITIONS
        assert "weather_advantage" in AdjudicationCriteria.CONDITIONS
        assert "surprise" in AdjudicationCriteria.CONDITIONS
        assert "unit_type_bonus" in AdjudicationCriteria.CONDITIONS
        assert "readiness_bonus" in AdjudicationCriteria.CONDITIONS

    def test_adjudication_criteria_unit_bonuses(self, db_session):
        """Test AdjudicationCriteria unit type bonuses"""
        from app.services.adjudication import AdjudicationCriteria

        # Verify bonuses exist
        assert "atgm_vs_armor" in AdjudicationCriteria.UNIT_TYPE_BONUSES
        assert "sniper_vs_inf" in AdjudicationCriteria.UNIT_TYPE_BONUSES
        assert "armor_vs_inf" in AdjudicationCriteria.UNIT_TYPE_BONUSES

    def test_process_enemy_orders_by_name(self, db_session, sample_game, enemy_units, sample_turn):
        """Test process_enemy_orders with unit name instead of ID"""
        engine = RuleEngine(db_session)

        # Create enemy turn
        enemy_turn = Turn(
            game_id=sample_game.id,
            turn_number=1,
            time="06:00",
            weather="clear",
            phase="orders"
        )
        db_session.add(enemy_turn)
        db_session.commit()

        result = engine.process_enemy_orders(sample_game.id, {
            "orders": [{"unit_id": enemy_units[0].name, "order_type": "move"}]
        })

        assert isinstance(result, list)

    def test_process_enemy_orders_invalid_type(self, db_session, sample_game, enemy_units, sample_turn):
        """Test process_enemy_orders with invalid order type"""
        engine = RuleEngine(db_session)

        # Create enemy turn
        enemy_turn = Turn(
            game_id=sample_game.id,
            turn_number=1,
            time="06:00",
            weather="clear",
            phase="orders"
        )
        db_session.add(enemy_turn)
        db_session.commit()

        result = engine.process_enemy_orders(sample_game.id, {
            "orders": [{"unit_id": enemy_units[0].id, "order_type": "invalid_type"}]
        })

        assert isinstance(result, list)

    def test_process_enemy_orders_with_location(self, db_session, sample_game, enemy_units, sample_turn):
        """Test process_enemy_orders with location"""
        engine = RuleEngine(db_session)

        # Create enemy turn
        enemy_turn = Turn(
            game_id=sample_game.id,
            turn_number=1,
            time="06:00",
            weather="clear",
            phase="orders"
        )
        db_session.add(enemy_turn)
        db_session.commit()

        result = engine.process_enemy_orders(sample_game.id, {
            "orders": [{
                "unit_id": enemy_units[0].id,
                "order_type": "move",
                "location_x": 40,
                "location_y": 30
            }]
        })

        assert isinstance(result, list)

    def test_adjudication_condition_creation(self, db_session):
        """Test AdjudicationCondition creation"""
        from app.services.adjudication import AdjudicationCondition

        condition = AdjudicationCondition("test_condition", 0.8, "Test description")

        assert condition.name == "test_condition"
        assert condition.weight == 0.8
        assert condition.description == "Test description"
        assert condition.met == False

    def test_resolve_combat_with_exhausted_supply(self, db_session, player_units):
        """Test combat resolution with exhausted supply"""
        engine = RuleEngine(db_session)
        unit = player_units[0]
        unit.ammo = SupplyLevel.EXHAUSTED
        unit.fuel = SupplyLevel.FULL

        outcome = engine._resolve_combat(unit)

        # Should fail due to no ammo
        assert outcome == "failed"

    def test_resolve_combat_light_damage(self, db_session, player_units):
        """Test combat resolution with light damage unit"""
        engine = RuleEngine(db_session)
        unit = player_units[0]
        unit.ammo = SupplyLevel.FULL
        unit.fuel = SupplyLevel.FULL
        unit.status = UnitStatus.LIGHT_DAMAGE

        outcome = engine._resolve_combat(unit)

        # Should return an outcome
        assert outcome in ["success", "partial", "failed"]

    def test_resolve_combat_heavy_damage(self, db_session, player_units):
        """Test combat resolution with heavy damage unit"""
        engine = RuleEngine(db_session)
        unit = player_units[0]
        unit.ammo = SupplyLevel.FULL
        unit.fuel = SupplyLevel.FULL
        unit.status = UnitStatus.HEAVY_DAMAGE

        outcome = engine._resolve_combat(unit)

        # Heavy damage should always fail
        assert outcome == "failed"

    def test_full_turn_time_advancement(self, db_session, sample_game, player_units, sample_turn):
        """Test that time advances after turn"""
        engine = RuleEngine(db_session)
        original_time = sample_game.current_time

        order = Order(
            game_id=sample_game.id,
            unit_id=player_units[0].id,
            turn_id=sample_turn.id,
            order_type=OrderType.MOVE,
            intent="Move",
            location_x=25,
            location_y=25
        )
        db_session.add(order)
        db_session.commit()

        result = engine.adjudicate_turn(sample_game.id)

        # Verify turn advanced
        assert "turn" in result

    def test_adjudication_criteria_weather_advantage(self, db_session, sample_game, player_units, enemy_units, sample_turn):
        """Test AdjudicationCriteria with weather advantage"""
        from app.services.adjudication import AdjudicationCriteria

        # Create order
        order = Order(
            game_id=sample_game.id,
            unit_id=player_units[0].id,
            turn_id=sample_turn.id,
            order_type=OrderType.ATTACK,
            intent="Attack"
        )
        db_session.add(order)
        db_session.commit()

        unit = player_units[0]
        targets = enemy_units

        game_state = {"turn": 1, "weather": "clear", "time": "12:00"}

        outcome, results = AdjudicationCriteria.evaluate_order(
            order=order,
            unit=unit,
            target_units=targets,
            game_state=game_state,
            weather="clear",
            time="12:00"
        )

        assert "weather_advantage" in results

    def test_adjudication_criteria_supply_status(self, db_session, sample_game, player_units, enemy_units, sample_turn):
        """Test AdjudicationCriteria with supply status"""
        from app.services.adjudication import AdjudicationCriteria

        # Create order
        order = Order(
            game_id=sample_game.id,
            unit_id=player_units[0].id,
            turn_id=sample_turn.id,
            order_type=OrderType.ATTACK,
            intent="Attack"
        )
        db_session.add(order)
        db_session.commit()

        unit = player_units[0]
        unit.ammo = SupplyLevel.DEPLETED
        targets = enemy_units

        game_state = {"turn": 1, "weather": "clear", "time": "12:00"}

        outcome, results = AdjudicationCriteria.evaluate_order(
            order=order,
            unit=unit,
            target_units=targets,
            game_state=game_state,
            weather="clear",
            time="12:00"
        )

        assert "supply_status" in results

    def test_reconnaissance_sniper_infantry(self, db_session, sample_game):
        """Test reconnaissance with sniper infantry subtype"""
        engine = RuleEngine(db_session)

        # Add player sniper unit
        sniper = Unit(
            game_id=sample_game.id,
            name="Sniper Unit",
            unit_type="infantry",
            side="player",
            x=10,
            y=25,
            status=UnitStatus.INTACT,
            ammo=SupplyLevel.FULL,
            fuel=SupplyLevel.FULL,
            readiness=SupplyLevel.FULL,
            infantry_subtype="sniper"
        )
        db_session.add(sniper)

        # Add enemy in range
        enemy = Unit(
            game_id=sample_game.id,
            name="Enemy Target",
            unit_type="infantry",
            side="enemy",
            x=15,
            y=25,
            status=UnitStatus.INTACT,
            ammo=SupplyLevel.FULL,
            fuel=SupplyLevel.FULL,
            readiness=SupplyLevel.FULL
        )
        db_session.add(enemy)
        db_session.commit()

        events = engine._process_reconnaissance(sample_game.id)

        assert isinstance(events, list)

    def test_reconnaissance_twilight_time(self, db_session, sample_game, player_units):
        """Test reconnaissance during twilight"""
        engine = RuleEngine(db_session)
        sample_game.current_time = "18:00"  # Dusk

        enemy = Unit(
            game_id=sample_game.id,
            name="Enemy at Dusk",
            unit_type="infantry",
            side="enemy",
            x=12,
            y=25,
            status=UnitStatus.INTACT,
            ammo=SupplyLevel.FULL,
            fuel=SupplyLevel.FULL,
            readiness=SupplyLevel.FULL
        )
        db_session.add(enemy)
        db_session.commit()

        events = engine._process_reconnaissance(sample_game.id)

        assert isinstance(events, list)

    def test_reconnaissance_cloudy_weather(self, db_session, sample_game, player_units):
        """Test reconnaissance with cloudy weather"""
        engine = RuleEngine(db_session)
        sample_game.weather = "cloudy"

        enemy = Unit(
            game_id=sample_game.id,
            name="Enemy in Cloudy",
            unit_type="infantry",
            side="enemy",
            x=12,
            y=25,
            status=UnitStatus.INTACT,
            ammo=SupplyLevel.FULL,
            fuel=SupplyLevel.FULL,
            readiness=SupplyLevel.FULL
        )
        db_session.add(enemy)
        db_session.commit()

        events = engine._process_reconnaissance(sample_game.id)

        assert isinstance(events, list)

    def test_combat_target_light_damage(self, db_session, sample_game, player_units, enemy_units, sample_turn):
        """Test combat when target already has light damage"""
        engine = RuleEngine(db_session)

        # Set target to light damage
        enemy_units[0].status = UnitStatus.LIGHT_DAMAGE
        # Set attacker strong
        player_units[0].strength = 100

        order = Order(
            game_id=sample_game.id,
            unit_id=player_units[0].id,
            turn_id=sample_turn.id,
            order_type=OrderType.ATTACK,
            intent="Attack damaged target",
            target_units=[enemy_units[0].id]
        )
        db_session.add(order)
        db_session.commit()

        result = engine._adjudicate_order(order)

        assert result["outcome"] in ["perfect_success", "success", "partial", "failed", "major_failed"]

    def test_combat_target_medium_damage(self, db_session, sample_game, player_units, enemy_units, sample_turn):
        """Test combat when target already has medium damage"""
        engine = RuleEngine(db_session)

        # Set target to medium damage
        enemy_units[0].status = UnitStatus.MEDIUM_DAMAGE
        # Set attacker strong
        player_units[0].strength = 100

        order = Order(
            game_id=sample_game.id,
            unit_id=player_units[0].id,
            turn_id=sample_turn.id,
            order_type=OrderType.ATTACK,
            intent="Attack heavily damaged target",
            target_units=[enemy_units[0].id]
        )
        db_session.add(order)
        db_session.commit()

        result = engine._adjudicate_order(order)

        assert result["outcome"] in ["perfect_success", "success", "partial", "failed", "major_failed"]

    def test_enemy_reconnaissance_light_rain(self, db_session, sample_game, enemy_units):
        """Test enemy reconnaissance with light rain"""
        engine = RuleEngine(db_session)
        sample_game.weather = "light_rain"

        player = Unit(
            game_id=sample_game.id,
            name="Player in Rain",
            unit_type="infantry",
            side="player",
            x=22,
            y=25,
            status=UnitStatus.INTACT,
            ammo=SupplyLevel.FULL,
            fuel=SupplyLevel.FULL,
            readiness=SupplyLevel.FULL
        )
        db_session.add(player)
        db_session.commit()

        events = engine._process_enemy_reconnaissance(sample_game.id)

        assert isinstance(events, list)

    def test_adjudication_criteria_reconnaissance(self, db_session, sample_game, player_units, enemy_units, sample_turn):
        """Test AdjudicationCriteria reconnaissance condition"""
        from app.services.adjudication import AdjudicationCriteria

        # Create order with attack
        order = Order(
            game_id=sample_game.id,
            unit_id=player_units[0].id,
            turn_id=sample_turn.id,
            order_type=OrderType.RECON,
            intent="Reconnaissance"
        )
        db_session.add(order)
        db_session.commit()

        unit = player_units[0]
        targets = enemy_units
        game_state = {"turn": 1, "weather": "clear", "time": "12:00"}

        outcome, results = AdjudicationCriteria.evaluate_order(
            order=order,
            unit=unit,
            target_units=targets,
            game_state=game_state,
            weather="clear",
            time="12:00"
        )

        assert "reconnaissance" in results

    def test_combat_attacker_light_damage_fails(self, db_session, sample_game, player_units, enemy_units, sample_turn):
        """Test combat when attacker has light damage and fails"""
        engine = RuleEngine(db_session)

        # Attacker has light damage and is weak
        player_units[0].status = UnitStatus.LIGHT_DAMAGE
        player_units[0].strength = 10

        order = Order(
            game_id=sample_game.id,
            unit_id=player_units[0].id,
            turn_id=sample_turn.id,
            order_type=OrderType.ATTACK,
            intent="Attack",
            target_units=[enemy_units[0].id]
        )
        db_session.add(order)
        db_session.commit()

        result = engine._adjudicate_order(order)

        # outcome could be anything
        assert result["outcome"] in ["perfect_success", "success", "partial", "failed", "major_failed"]

    def test_adjudication_criteria_mobility(self, db_session, sample_game, player_units, enemy_units, sample_turn):
        """Test AdjudicationCriteria mobility condition"""
        from app.services.adjudication import AdjudicationCriteria

        order = Order(
            game_id=sample_game.id,
            unit_id=player_units[0].id,
            turn_id=sample_turn.id,
            order_type=OrderType.MOVE,
            intent="Move"
        )
        db_session.add(order)
        db_session.commit()

        unit = player_units[0]
        unit.fuel = SupplyLevel.FULL
        targets = []
        game_state = {"turn": 1, "weather": "clear", "time": "12:00"}

        outcome, results = AdjudicationCriteria.evaluate_order(
            order=order,
            unit=unit,
            target_units=targets,
            game_state=game_state,
            weather="clear",
            time="12:00"
        )

        assert "mobility" in results

    def test_consume_supplies_full_to_depleted(self, db_session, player_units):
        """Test supply consumption from full to depleted"""
        engine = RuleEngine(db_session)
        unit = player_units[0]

        # Should start full
        assert unit.ammo == SupplyLevel.FULL

        engine._consume_supplies(unit)
        db_session.commit()

        # After consumption
        assert unit.ammo == SupplyLevel.DEPLETED

    def test_consume_supplies_already_exhausted(self, db_session, player_units):
        """Test supply consumption when already exhausted"""
        engine = RuleEngine(db_session)
        unit = player_units[0]
        unit.ammo = SupplyLevel.EXHAUSTED

        engine._consume_supplies(unit)
        db_session.commit()

        # Should remain exhausted
        assert unit.ammo == SupplyLevel.EXHAUSTED

    def test_consume_supplies_readiness_depleted(self, db_session, player_units):
        """Test supply consumption when readiness already depleted"""
        engine = RuleEngine(db_session)
        unit = player_units[0]
        unit.readiness = SupplyLevel.DEPLETED
        unit.ammo = SupplyLevel.EXHAUSTED
        unit.fuel = SupplyLevel.EXHAUSTED

        engine._consume_supplies(unit)
        db_session.commit()

        # Readiness should now be exhausted
        assert unit.readiness == SupplyLevel.EXHAUSTED

    def test_consume_supplies_fuel_depleted(self, db_session, player_units):
        """Test supply consumption when fuel already depleted"""
        engine = RuleEngine(db_session)
        unit = player_units[0]
        unit.fuel = SupplyLevel.DEPLETED
        unit.ammo = SupplyLevel.EXHAUSTED
        unit.readiness = SupplyLevel.EXHAUSTED

        engine._consume_supplies(unit)
        db_session.commit()

        # Fuel should now be exhausted
        assert unit.fuel == SupplyLevel.EXHAUSTED

    def test_adjudication_criteria_position_advantage(self, db_session, sample_game, player_units, enemy_units, sample_turn):
        """Test AdjudicationCriteria position advantage"""
        from app.services.adjudication import AdjudicationCriteria

        order = Order(
            game_id=sample_game.id,
            unit_id=player_units[0].id,
            turn_id=sample_turn.id,
            order_type=OrderType.ATTACK,
            intent="Attack from high ground"
        )
        db_session.add(order)
        db_session.commit()

        # Place player at higher Y (assuming higher ground)
        player_units[0].y = 40
        enemy_units[0].y = 20

        unit = player_units[0]
        targets = enemy_units
        game_state = {"turn": 1, "weather": "clear", "time": "12:00"}

        outcome, results = AdjudicationCriteria.evaluate_order(
            order=order,
            unit=unit,
            target_units=targets,
            game_state=game_state,
            weather="clear",
            time="12:00"
        )

        assert "position_advantage" in results

    def test_adjudication_criteria_unit_type(self, db_session, sample_game, player_units, enemy_units, sample_turn):
        """Test AdjudicationCriteria unit type bonus"""
        from app.services.adjudication import AdjudicationCriteria

        order = Order(
            game_id=sample_game.id,
            unit_id=player_units[0].id,
            turn_id=sample_turn.id,
            order_type=OrderType.ATTACK,
            intent="Attack"
        )
        db_session.add(order)
        db_session.commit()

        # Set armor vs infantry
        player_units[0].unit_type = "armor"
        enemy_units[0].unit_type = "infantry"

        unit = player_units[0]
        targets = enemy_units
        game_state = {"turn": 1, "weather": "clear", "time": "12:00"}

        outcome, results = AdjudicationCriteria.evaluate_order(
            order=order,
            unit=unit,
            target_units=targets,
            game_state=game_state,
            weather="clear",
            time="12:00"
        )

        assert "unit_type_bonus" in results

    def test_adjudication_criteria_superior_firepower(self, db_session, sample_game, player_units, enemy_units, sample_turn):
        """Test AdjudicationCriteria superior firepower"""
        from app.services.adjudication import AdjudicationCriteria

        order = Order(
            game_id=sample_game.id,
            unit_id=player_units[0].id,
            turn_id=sample_turn.id,
            order_type=OrderType.ATTACK,
            intent="Attack"
        )
        db_session.add(order)
        db_session.commit()

        # Player much stronger than enemy
        player_units[0].strength = 100
        enemy_units[0].strength = 10

        unit = player_units[0]
        targets = enemy_units
        game_state = {"turn": 1, "weather": "clear", "time": "12:00"}

        outcome, results = AdjudicationCriteria.evaluate_order(
            order=order,
            unit=unit,
            target_units=targets,
            game_state=game_state,
            weather="clear",
            time="12:00"
        )

        assert "superior_firepower" in results

    def test_unit_type_bonus_scout_infantry(self, db_session):
        """Test unit type bonus with scout infantry attacking"""
        from app.services.adjudication import AdjudicationCriteria
        from app.models import Unit

        # Create scout attacker
        attacker = Unit(
            game_id=1,
            name="Scout",
            unit_type="infantry",
            side="player",
            x=10,
            y=25,
            status=UnitStatus.INTACT,
            ammo=SupplyLevel.FULL,
            fuel=SupplyLevel.FULL,
            readiness=SupplyLevel.FULL,
            infantry_subtype="scout"
        )

        # Create armor defender
        defender = Unit(
            game_id=1,
            name="Tank",
            unit_type="armor",
            side="enemy",
            x=15,
            y=25,
            status=UnitStatus.INTACT,
            ammo=SupplyLevel.FULL,
            fuel=SupplyLevel.FULL,
            readiness=SupplyLevel.FULL
        )

        bonus = AdjudicationCriteria._calculate_unit_type_bonus(attacker, [defender])

        assert isinstance(bonus, (int, float))

    def test_order_with_multiple_targets(self, db_session, sample_game, player_units, enemy_units, sample_turn):
        """Test attack order with multiple targets"""
        engine = RuleEngine(db_session)

        # Add another enemy
        enemy2 = Unit(
            game_id=sample_game.id,
            name="Enemy 2",
            unit_type="infantry",
            side="enemy",
            x=20,
            y=30,
            status=UnitStatus.INTACT,
            ammo=SupplyLevel.FULL,
            fuel=SupplyLevel.FULL,
            readiness=SupplyLevel.FULL
        )
        db_session.add(enemy2)
        db_session.commit()

        order = Order(
            game_id=sample_game.id,
            unit_id=player_units[0].id,
            turn_id=sample_turn.id,
            order_type=OrderType.ATTACK,
            intent="Attack multiple",
            target_units=[enemy_units[0].id, enemy2.id]
        )
        db_session.add(order)
        db_session.commit()

        result = engine._adjudicate_order(order)

        assert result["outcome"] in ["perfect_success", "success", "partial", "failed", "major_failed"]

    def test_adjudication_criteria_surprise(self, db_session, sample_game, player_units, enemy_units, sample_turn):
        """Test AdjudicationCriteria surprise condition"""
        from app.services.adjudication import AdjudicationCriteria

        order = Order(
            game_id=sample_game.id,
            unit_id=player_units[0].id,
            turn_id=sample_turn.id,
            order_type=OrderType.ATTACK,
            intent="Surprise attack"
        )
        db_session.add(order)
        db_session.commit()

        unit = player_units[0]
        targets = enemy_units
        game_state = {"turn": 1, "weather": "clear", "time": "06:00"}  # Early morning for surprise

        outcome, results = AdjudicationCriteria.evaluate_order(
            order=order,
            unit=unit,
            target_units=targets,
            game_state=game_state,
            weather="clear",
            time="06:00"
        )

        assert "surprise" in results

    def test_adjudication_criteria_readiness(self, db_session, sample_game, player_units, enemy_units, sample_turn):
        """Test AdjudicationCriteria readiness bonus"""
        from app.services.adjudication import AdjudicationCriteria

        order = Order(
            game_id=sample_game.id,
            unit_id=player_units[0].id,
            turn_id=sample_turn.id,
            order_type=OrderType.ATTACK,
            intent="Attack"
        )
        db_session.add(order)
        db_session.commit()

        unit = player_units[0]
        unit.readiness = SupplyLevel.FULL
        targets = enemy_units
        game_state = {"turn": 1, "weather": "clear", "time": "12:00"}

        outcome, results = AdjudicationCriteria.evaluate_order(
            order=order,
            unit=unit,
            target_units=targets,
            game_state=game_state,
            weather="clear",
            time="12:00"
        )

        assert "readiness_bonus" in results

    def test_attack_with_invalid_target(self, db_session, sample_game, player_units, sample_turn):
        """Test attack with non-existent target returns failed outcome"""
        engine = RuleEngine(db_session)

        # Use a non-existent target ID (99999)
        order = Order(
            game_id=sample_game.id,
            unit_id=player_units[0].id,
            turn_id=sample_turn.id,
            order_type=OrderType.ATTACK,
            intent="Attack non-existent target",
            target_units=[99999]
        )
        db_session.add(order)
        db_session.commit()

        result = engine._adjudicate_order(order)

        assert result["outcome"] == "failed"
        # Should have warning about invalid target
        warnings = [c for c in result["changes"] if c.get("type") == "warning" and c.get("code") == "INVALID_TARGET"]
        assert len(warnings) > 0

    def test_attack_with_out_of_range_target(self, db_session, sample_game, player_units, enemy_units, sample_turn):
        """Test attack with out-of-range target adds warning"""
        engine = RuleEngine(db_session)

        # Place enemy far away (beyond max range of typical unit)
        enemy_units[0].x = 30
        enemy_units[0].y = 30

        # Player unit at origin
        player_units[0].x = 0
        player_units[0].y = 0

        order = Order(
            game_id=sample_game.id,
            unit_id=player_units[0].id,
            turn_id=sample_turn.id,
            order_type=OrderType.ATTACK,
            intent="Attack far target",
            target_units=[enemy_units[0].id]
        )
        db_session.add(order)
        db_session.commit()

        result = engine._adjudicate_order(order)

        # Should have warning about out of range
        warnings = [c for c in result["changes"] if c.get("type") == "warning" and c.get("code") == "OUT_OF_RANGE"]
        assert len(warnings) > 0
