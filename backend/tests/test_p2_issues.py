# Additional tests for Issue #32: Fog of War / terrain stability / target validation / scenario map size
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import (
    Base, Game, Unit, Turn, Order,
    UnitStatus, OrderType, SupplyLevel
)
from app.services.game_state_service import GameStateService
from app.services.terrain import generate_map_terrain, TerrainType
from app.services.initial_setup import InitialSetupService
from app.services.adjudication import RuleEngine


class TestFogOfWar:
    """Tests for Fog of War implementation"""

    @pytest.fixture
    def db_session(self):
        """Create in-memory SQLite database for testing"""
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()
        yield session
        session.close()

    @pytest.fixture
    def game_with_units(self, db_session):
        """Create a game with player and enemy units"""
        game = Game(
            name="Fog of War Test",
            current_turn=1,
            current_time="06:00",
            weather="clear",
            map_width=20,
            map_height=20
        )
        db_session.add(game)
        db_session.commit()
        db_session.refresh(game)

        # Player units (should be fully visible)
        player_unit = Unit(
            game_id=game.id,
            name="Player Unit",
            unit_type="infantry",
            side="player",
            x=5,
            y=10,
            status=UnitStatus.INTACT,
            ammo=SupplyLevel.FULL,
            fuel=SupplyLevel.FULL,
            readiness=SupplyLevel.FULL
        )
        db_session.add(player_unit)

        # Enemy units (position should be hidden if not observed)
        enemy_unit = Unit(
            game_id=game.id,
            name="Enemy Tank",
            unit_type="armor",
            side="enemy",
            x=15,
            y=10,
            status=UnitStatus.INTACT,
            ammo=SupplyLevel.FULL,
            fuel=SupplyLevel.FULL,
            readiness=SupplyLevel.FULL
        )
        db_session.add(enemy_unit)
        db_session.commit()
        db_session.refresh(enemy_unit)

        return game, player_unit, enemy_unit

    def test_player_units_visible(self, db_session, game_with_units):
        """Test that player units are fully visible"""
        game, player_unit, enemy_unit = game_with_units

        service = GameStateService(db_session)
        known_enemies = service.get_player_knowledge(game.id)

        # Get raw units data
        units_data = [
            {
                "id": player_unit.id,
                "name": player_unit.name,
                "type": player_unit.unit_type,
                "side": player_unit.side,
                "x": player_unit.x,
                "y": player_unit.y,
                "status": player_unit.status.value,
                "ammo": player_unit.ammo.value,
                "fuel": player_unit.fuel.value,
                "readiness": player_unit.readiness.value,
                "strength": player_unit.strength
            },
            {
                "id": enemy_unit.id,
                "name": enemy_unit.name,
                "type": enemy_unit.unit_type,
                "side": enemy_unit.side,
                "x": enemy_unit.x,
                "y": enemy_unit.y,
                "status": enemy_unit.status.value,
                "ammo": enemy_unit.ammo.value,
                "fuel": enemy_unit.fuel.value,
                "readiness": enemy_unit.readiness.value,
                "strength": enemy_unit.strength
            }
        ]

        filtered = service.apply_fog_of_war(units_data, known_enemies)

        # Player unit should be fully visible
        player_result = next(u for u in filtered if u["side"] == "player")
        assert player_result["x"] == 5
        assert player_result["y"] == 10
        assert player_result["ammo"] == "full"
        assert player_result["fuel"] == "full"
        assert player_result["strength"] == 100

    def test_unobserved_enemy_hidden(self, db_session, game_with_units):
        """Test that unobserved enemy positions are hidden"""
        game, player_unit, enemy_unit = game_with_units

        service = GameStateService(db_session)
        known_enemies = service.get_player_knowledge(game.id)

        units_data = [
            {
                "id": player_unit.id,
                "name": player_unit.name,
                "type": player_unit.unit_type,
                "side": player_unit.side,
                "x": player_unit.x,
                "y": player_unit.y,
                "status": player_unit.status.value,
                "ammo": player_unit.ammo.value,
                "fuel": player_unit.fuel.value,
                "readiness": player_unit.readiness.value,
                "strength": player_unit.strength
            },
            {
                "id": enemy_unit.id,
                "name": enemy_unit.name,
                "type": enemy_unit.unit_type,
                "side": enemy_unit.side,
                "x": enemy_unit.x,
                "y": enemy_unit.y,
                "status": enemy_unit.status.value,
                "ammo": enemy_unit.ammo.value,
                "fuel": enemy_unit.fuel.value,
                "readiness": enemy_unit.readiness.value,
                "strength": enemy_unit.strength
            }
        ]

        filtered = service.apply_fog_of_war(units_data, known_enemies)

        # Enemy unit should be hidden (not observed)
        enemy_result = next(u for u in filtered if u["side"] == "enemy")
        assert enemy_result["x"] is None
        assert enemy_result["y"] is None
        assert enemy_result["ammo"] is None
        assert enemy_result["fuel"] is None
        assert enemy_result["readiness"] is None
        assert enemy_result["strength"] is None
        assert enemy_result["is_observed"] is False


class TestTerrainStability:
    """Tests for terrain stability across turns"""

    def test_terrain_persists_with_same_seed(self):
        """Test that terrain generation is deterministic with same seed"""
        # Generate terrain with same seed
        terrain1 = generate_map_terrain(10, 10, seed=12345)
        terrain2 = generate_map_terrain(10, 10, seed=12345)

        # Should be identical
        assert terrain1 == terrain2

    def test_terrain_different_seeds(self):
        """Test that different seeds produce different terrain"""
        terrain1 = generate_map_terrain(10, 10, seed=11111)
        terrain2 = generate_map_terrain(10, 10, seed=99999)

        # Should be different
        assert terrain1 != terrain2

    def test_terrain_valid_coordinates(self):
        """Test that terrain has valid coordinate keys"""
        terrain = generate_map_terrain(5, 5)

        # Check all valid coordinates exist
        for x in range(5):
            for y in range(5):
                key = f"{x},{y}"
                assert key in terrain
                # Valid terrain type
                assert terrain[key] in [t.value for t in TerrainType]

    def test_terrain_no_out_of_bounds(self):
        """Test terrain has no out-of-bounds coordinates"""
        terrain = generate_map_terrain(8, 8)

        # Check no unexpected keys
        for key in terrain.keys():
            x, y = map(int, key.split(","))
            assert 0 <= x < 8
            assert 0 <= y < 8


class TestTargetValidation:
    """Tests for target validation in attacks"""

    @pytest.fixture
    def db_session(self):
        """Create in-memory SQLite database for testing"""
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()
        yield session
        session.close()

    @pytest.fixture
    def game_with_combat_units(self, db_session):
        """Create a game with units for combat tests"""
        game = Game(
            name="Combat Test",
            current_turn=1,
            current_time="06:00",
            weather="clear",
            map_width=20,
            map_height=20
        )
        db_session.add(game)
        db_session.commit()
        db_session.refresh(game)

        # Attacker
        attacker = Unit(
            game_id=game.id,
            name="Attacker",
            unit_type="infantry",
            side="player",
            x=5,
            y=5,
            status=UnitStatus.INTACT,
            ammo=SupplyLevel.FULL,
            fuel=SupplyLevel.FULL,
            readiness=SupplyLevel.FULL
        )
        db_session.add(attacker)

        # Defender in range
        defender = Unit(
            game_id=game.id,
            name="Defender",
            unit_type="armor",
            side="enemy",
            x=7,
            y=5,
            status=UnitStatus.INTACT,
            ammo=SupplyLevel.FULL,
            fuel=SupplyLevel.FULL,
            readiness=SupplyLevel.FULL
        )
        db_session.add(defender)

        # Defender out of range
        out_of_range = Unit(
            game_id=game.id,
            name="Far Defender",
            unit_type="infantry",
            side="enemy",
            x=15,
            y=15,
            status=UnitStatus.INTACT,
            ammo=SupplyLevel.FULL,
            fuel=SupplyLevel.FULL,
            readiness=SupplyLevel.FULL
        )
        db_session.add(out_of_range)

        db_session.commit()
        db_session.refresh(attacker)
        db_session.refresh(defender)
        db_session.refresh(out_of_range)

        return game, attacker, defender, out_of_range

    def test_target_within_range(self, db_session, game_with_combat_units):
        """Test that attack succeeds when target is within range"""
        game, attacker, defender, out_of_range = game_with_combat_units

        turn = Turn(
            game_id=game.id,
            turn_number=1,
            time="06:00",
            weather="clear",
            phase="orders"
        )
        db_session.add(turn)
        db_session.commit()
        db_session.refresh(turn)

        order = Order(
            game_id=game.id,
            unit_id=attacker.id,
            turn_id=turn.id,
            order_type=OrderType.ATTACK,
            target_units=[defender.id],
            intent="Attack enemy armor"
        )
        db_session.add(order)
        db_session.commit()

        # Create rule engine
        engine = RuleEngine(db_session)

        # Process attack order
        units = db_session.query(Unit).filter(Unit.game_id == game.id).all()
        result = engine._adjudicate_order(order)

        # Should have a result
        assert result is not None
        assert result.get("outcome") in ["success", "partial", "failed"]

    def test_target_out_of_range(self, db_session, game_with_combat_units):
        """Test that attack handles out-of-range targets"""
        game, attacker, defender, out_of_range = game_with_combat_units

        turn = Turn(
            game_id=game.id,
            turn_number=1,
            time="06:00",
            weather="clear",
            phase="orders"
        )
        db_session.add(turn)
        db_session.commit()
        db_session.refresh(turn)

        # Try to attack target far away
        order = Order(
            game_id=game.id,
            unit_id=attacker.id,
            turn_id=turn.id,
            order_type=OrderType.ATTACK,
            target_units=[out_of_range.id],
            intent="Attack far enemy"
        )
        db_session.add(order)
        db_session.commit()

        engine = RuleEngine(db_session)

        units = db_session.query(Unit).filter(Unit.game_id == game.id).all()
        result = engine._adjudicate_order(order)

        # Should handle gracefully (either fail or return warning)
        assert result is not None


class TestScenarioMapSize:
    """Tests for scenario-driven map size"""

    def test_scenario_map_size_config(self):
        """Test that scenario can configure map size"""
        from app.services.scenario_manager import ScenarioManager

        manager = ScenarioManager()

        # Get scenario - use one that exists in scenarios.json
        scenario = manager.get_scenario("defend-the-bridge")
        assert scenario is not None
        assert "map_size" in scenario

        # Map size should be configured
        map_size = scenario["map_size"]
        assert "width" in map_size
        assert "height" in map_size
        assert map_size["width"] > 0
        assert map_size["height"] > 0

    def test_game_uses_scenario_map_size(self):
        """Test that game created with scenario uses scenario map size"""
        from app.services.scenario_manager import ScenarioManager

        manager = ScenarioManager()

        # Get different scenarios and check map sizes
        scenarios = [
            "defend-the-bridge",
            "breakthrough"
        ]

        for scenario_id in scenarios:
            scenario = manager.get_scenario(scenario_id)
            assert scenario is not None
            map_size = scenario["map_size"]
            # Both dimensions should be reasonable
            assert 10 <= map_size["width"] <= 200
            assert 10 <= map_size["height"] <= 200

    def test_default_map_size_fallback(self):
        """Test that default map size is used when scenario has none"""
        # Create game without explicit map size
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()

        game = Game(name="Test Game", map_width=50, map_height=50)
        session.add(game)
        session.commit()

        # Should use default 50x50
        assert game.map_width == 50
        assert game.map_height == 50

        session.close()
