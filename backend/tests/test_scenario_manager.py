# Tests for Scenario Manager Service
import pytest
from app.services.scenario_manager import ScenarioManager
from app.data.scenarios import load_scenarios, get_scenario, validate_scenario


class TestScenarioDataLoader:
    """Tests for scenario data loading functions"""

    def test_load_scenarios_returns_list(self):
        """Test that load_scenarios returns a list"""
        scenarios = load_scenarios()
        assert isinstance(scenarios, list)
        assert len(scenarios) > 0

    def test_load_scenarios_contains_valid_scenarios(self):
        """Test that loaded scenarios have required fields"""
        scenarios = load_scenarios()
        for scenario in scenarios:
            assert "id" in scenario
            assert "name" in scenario
            assert "difficulty" in scenario
            assert "map_size" in scenario

    def test_get_scenario_by_id(self):
        """Test getting a scenario by ID"""
        scenario = get_scenario("defend-the-bridge")
        assert scenario is not None
        assert scenario["id"] == "defend-the-bridge"
        assert scenario["name"] == "橋の防衛"

    def test_get_scenario_returns_none_for_invalid_id(self):
        """Test that invalid ID returns None"""
        scenario = get_scenario("nonexistent-scenario")
        assert scenario is None

    def test_validate_scenario_valid(self):
        """Test validation of valid scenario"""
        scenario = get_scenario("defend-the-bridge")
        assert validate_scenario(scenario) is True

    def test_validate_scenario_missing_field(self):
        """Test validation fails for missing field"""
        invalid_scenario = {
            "id": "test",
            "name": "Test",
            "difficulty": "normal"
            # missing description, map_size
        }
        assert validate_scenario(invalid_scenario) is False

    def test_validate_scenario_invalid_difficulty(self):
        """Test validation fails for invalid difficulty"""
        scenario = get_scenario("defend-the-bridge")
        scenario["difficulty"] = "invalid"
        assert validate_scenario(scenario) is False

    def test_validate_scenario_invalid_map_size(self):
        """Test validation fails for invalid map_size"""
        scenario = get_scenario("defend-the-bridge")
        scenario["map_size"] = {"invalid": "format"}
        assert validate_scenario(scenario) is False


class TestScenarioManager:
    """Tests for ScenarioManager class"""

    def test_init(self):
        """Test ScenarioManager initialization"""
        manager = ScenarioManager()
        assert manager._scenarios_cache is None

    def test_load_scenarios(self):
        """Test loading all scenarios via manager"""
        manager = ScenarioManager()
        scenarios = manager.load_scenarios()
        assert isinstance(scenarios, list)
        assert len(scenarios) > 0

    def test_load_scenarios_returns_summary(self):
        """Test that load_scenarios returns summary without full details"""
        manager = ScenarioManager()
        scenarios = manager.load_scenarios()
        scenario = scenarios[0]
        # Summary should have these fields
        assert "id" in scenario
        assert "name" in scenario
        assert "description" in scenario
        assert "difficulty" in scenario
        assert "map_size" in scenario
        # Should not have detailed fields
        assert "player_forces" not in scenario
        assert "enemy_forces" not in scenario

    def test_get_scenario(self):
        """Test getting detailed scenario by ID"""
        manager = ScenarioManager()
        scenario = manager.get_scenario("defend-the-bridge")
        assert scenario is not None
        assert scenario["id"] == "defend-the-bridge"

    def test_get_scenario_returns_none_for_invalid_id(self):
        """Test getting invalid scenario returns None"""
        manager = ScenarioManager()
        scenario = manager.get_scenario("invalid-id")
        assert scenario is None

    def test_validate_scenario(self):
        """Test scenario validation via manager"""
        manager = ScenarioManager()
        scenario = manager.get_scenario("defend-the-bridge")
        assert manager.validate_scenario(scenario) is True

    def test_validate_scenario_invalid(self):
        """Test validation of invalid scenario"""
        manager = ScenarioManager()
        invalid_scenario = {"id": "test"}
        assert manager.validate_scenario(invalid_scenario) is False

    def test_create_game_from_scenario(self, db_session):
        """Test creating a game from scenario"""
        manager = ScenarioManager()
        result = manager.create_game_from_scenario(
            scenario_id="defend-the-bridge",
            game_name="Test Game",
            db=db_session
        )
        assert "game_id" in result
        assert "scenario_id" in result
        assert result["scenario_id"] == "defend-the-bridge"
        assert result["turn"] == 1

    def test_create_game_invalid_scenario_raises(self, db_session):
        """Test that invalid scenario raises ValueError"""
        manager = ScenarioManager()
        with pytest.raises(ValueError, match="Scenario .* not found"):
            manager.create_game_from_scenario(
                scenario_id="nonexistent",
                game_name="Test Game",
                db=db_session
            )

    def test_create_game_stores_scenario_id(self, db_session):
        """Test that created game stores scenario_id"""
        manager = ScenarioManager()
        result = manager.create_game_from_scenario(
            scenario_id="counter-attack",
            game_name="Test Game",
            db=db_session
        )
        from app.models import Game
        game = db_session.query(Game).filter(Game.id == result["game_id"]).first()
        assert game.scenario_id == "counter-attack"

    def test_create_game_with_all_difficulties(self, db_session):
        """Test creating games with different difficulty scenarios"""
        manager = ScenarioManager()
        difficulties = ["defend-the-bridge", "counter-attack", "breakthrough"]
        for scenario_id in difficulties:
            scenario = get_scenario(scenario_id)
            result = manager.create_game_from_scenario(
                scenario_id=scenario_id,
                game_name=f"Test {scenario_id}",
                db=db_session
            )
            assert result["game_id"] is not None


class TestDeploymentPositions:
    """Tests for deployment position generation"""

    def test_generate_player_defensive_positions(self):
        """Test player defensive deployment positions"""
        manager = ScenarioManager()
        positions = manager._generate_deployment_positions(
            side="player",
            deployment_type="defensive",
            map_width=50,
            map_height=50,
            forces={"infantry": 3, "armor": 2}
        )
        # 5 total units
        assert len(positions) == 5
        # Player should be on left side (x < 20)
        for pos in positions:
            assert pos["x"] < 20
            # Should be in lower portion (y > 35)
            assert pos["y"] > 35

    def test_generate_player_offensive_positions(self):
        """Test player offensive deployment positions"""
        manager = ScenarioManager()
        positions = manager._generate_deployment_positions(
            side="player",
            deployment_type="offensive",
            map_width=50,
            map_height=50,
            forces={"infantry": 2, "armor": 2}
        )
        assert len(positions) == 4
        # Should be in middle-forward portion
        for pos in positions:
            assert 5 < pos["x"] < 25

    def test_generate_enemy_offensive_positions(self):
        """Test enemy offensive deployment positions"""
        manager = ScenarioManager()
        positions = manager._generate_deployment_positions(
            side="enemy",
            deployment_type="offensive",
            map_width=50,
            map_height=50,
            forces={"infantry": 4, "armor": 3}
        )
        # 7 total units
        assert len(positions) == 7
        # Enemy should be on right side (x > 30)
        for pos in positions:
            assert pos["x"] > 30
            # Should be in upper portion (y < 15)
            assert pos["y"] < 15

    def test_generate_enemy_defensive_positions(self):
        """Test enemy defensive deployment positions"""
        manager = ScenarioManager()
        positions = manager._generate_deployment_positions(
            side="enemy",
            deployment_type="defensive",
            map_width=50,
            map_height=50,
            forces={"infantry": 2}
        )
        assert len(positions) == 2
        # Enemy defensive should be in middle-upper portion
        for pos in positions:
            assert pos["x"] > 30

    def test_positions_within_bounds(self):
        """Test that all positions are within map bounds"""
        manager = ScenarioManager()
        positions = manager._generate_deployment_positions(
            side="player",
            deployment_type="defensive",
            map_width=50,
            map_height=50,
            forces={"infantry": 10, "armor": 10}
        )
        for pos in positions:
            assert 1 <= pos["x"] <= 49
            assert 1 <= pos["y"] <= 49

    def test_positions_have_coordinates(self):
        """Test that positions have x and y coordinates"""
        manager = ScenarioManager()
        positions = manager._generate_deployment_positions(
            side="player",
            deployment_type="defensive",
            map_width=30,
            map_height=30,
            forces={"infantry": 3}
        )
        for pos in positions:
            assert "x" in pos
            assert "y" in pos
            assert isinstance(pos["x"], (int, float))
            assert isinstance(pos["y"], (int, float))


class TestCreateUnits:
    """Tests for unit creation from scenario"""

    def test_create_player_units(self, db_session):
        """Test creating player units from scenario"""
        manager = ScenarioManager()
        # First create a game
        result = manager.create_game_from_scenario(
            scenario_id="counter-attack",
            game_name="Test Game",
            db=db_session
        )
        game_id = result["game_id"]

        # Query units
        from app.models import Unit
        units = db_session.query(Unit).filter(Unit.game_id == game_id).all()

        # Should have player units
        player_units = [u for u in units if u.side == "player"]
        assert len(player_units) > 0

    def test_create_enemy_units(self, db_session):
        """Test creating enemy units from scenario"""
        manager = ScenarioManager()
        result = manager.create_game_from_scenario(
            scenario_id="counter-attack",
            game_name="Test Game",
            db=db_session
        )
        game_id = result["game_id"]

        from app.models import Unit
        units = db_session.query(Unit).filter(Unit.game_id == game_id).all()

        # Should have enemy units
        enemy_units = [u for u in units if u.side == "enemy"]
        assert len(enemy_units) > 0

    def test_units_have_correct_properties(self, db_session):
        """Test that created units have correct properties"""
        manager = ScenarioManager()
        result = manager.create_game_from_scenario(
            scenario_id="night-recon",
            game_name="Test Game",
            db=db_session
        )
        game_id = result["game_id"]

        from app.models import Unit
        units = db_session.query(Unit).filter(Unit.game_id == game_id).all()

        for unit in units:
            assert unit.name is not None
            assert unit.unit_type is not None
            assert unit.side in ["player", "enemy"]
            assert unit.status is not None
            assert unit.ammo is not None
            assert unit.fuel is not None


class TestScenarioManagerEdgeCases:
    """Tests for edge cases and error handling"""

    def test_empty_forces(self):
        """Test handling of empty forces"""
        manager = ScenarioManager()
        # Empty forces should return empty list (not raise error)
        # Note: Current implementation has a bug with division by zero
        # This test will pass once the bug is fixed
        positions = manager._generate_deployment_positions(
            side="player",
            deployment_type="defensive",
            map_width=50,
            map_height=50,
            forces={}
        )
        assert len(positions) == 0

    def test_single_unit(self):
        """Test deployment with single unit"""
        manager = ScenarioManager()
        positions = manager._generate_deployment_positions(
            side="player",
            deployment_type="defensive",
            map_width=50,
            map_height=50,
            forces={"infantry": 1}
        )
        assert len(positions) == 1
        assert positions[0]["x"] > 0
        assert positions[0]["y"] > 0

    def test_large_force_count(self):
        """Test deployment with large number of units"""
        manager = ScenarioManager()
        positions = manager._generate_deployment_positions(
            side="player",
            deployment_type="offensive",
            map_width=100,
            map_height=100,
            forces={"infantry": 20, "armor": 15, "artillery": 10}
        )
        # Total = 45 units
        assert len(positions) == 45

    def test_small_map(self):
        """Test deployment on small map"""
        manager = ScenarioManager()
        positions = manager._generate_deployment_positions(
            side="enemy",
            deployment_type="offensive",
            map_width=10,
            map_height=10,
            forces={"infantry": 2}
        )
        assert len(positions) == 2
        # Positions should still be within bounds
        for pos in positions:
            assert 1 <= pos["x"] <= 9
            assert 1 <= pos["y"] <= 9
