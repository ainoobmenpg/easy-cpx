"""Tests for debriefing service"""
import pytest
from unittest.mock import AsyncMock, patch
from app.services.debriefing import DebriefingGenerator
from app.models import Game, Unit, Turn, Order, UnitStatus, OrderType, SupplyLevel


class TestDebriefingGenerator:
    """Test cases for DebriefingGenerator"""

    def test_calculate_statistics(self, db_session, sample_game, player_units, enemy_units):
        """Test statistics calculation"""
        generator = DebriefingGenerator()
        stats = generator._calculate_statistics(db_session, sample_game)

        assert "player" in stats
        assert "enemy" in stats
        assert "resources" in stats
        assert "operations" in stats

        assert stats["player"]["initial_count"] == 2
        assert stats["enemy"]["initial_count"] == 1

    def test_calculate_statistics_with_destroyed_units(self, db_session, sample_game, enemy_units):
        """Test statistics with destroyed units"""
        # Add player unit that is destroyed
        destroyed_unit = Unit(
            game_id=sample_game.id,
            name="Destroyed Unit",
            unit_type="infantry",
            side="player",
            x=10,
            y=10,
            status=UnitStatus.DESTROYED,
            ammo=SupplyLevel.EXHAUSTED,
            fuel=SupplyLevel.EXHAUSTED,
            readiness=SupplyLevel.EXHAUSTED,
            strength=0
        )
        db_session.add(destroyed_unit)

        # Add intact player unit
        intact_unit = Unit(
            game_id=sample_game.id,
            name="Intact Unit",
            unit_type="armor",
            side="player",
            x=15,
            y=15,
            status=UnitStatus.INTACT,
            ammo=SupplyLevel.FULL,
            fuel=SupplyLevel.FULL,
            readiness=SupplyLevel.FULL,
            strength=100
        )
        db_session.add(intact_unit)
        db_session.commit()

        generator = DebriefingGenerator()
        stats = generator._calculate_statistics(db_session, sample_game)

        assert stats["player"]["destroyed"] == 1
        assert stats["player"]["intact"] == 1
        assert stats["player"]["casualty_rate"] == 50.0

    def test_calculate_resource_consumption(self, db_session, player_units):
        """Test resource consumption calculation"""
        generator = DebriefingGenerator()

        # Set different supply levels
        player_units[0].ammo = SupplyLevel.EXHAUSTED
        player_units[0].fuel = SupplyLevel.DEPLETED
        player_units[1].ammo = SupplyLevel.DEPLETED
        player_units[1].fuel = SupplyLevel.FULL

        result = generator._calculate_resource_consumption(player_units, "ammo")

        assert result["depleted"] == 1
        assert result["low"] == 1

        result = generator._calculate_resource_consumption(player_units, "fuel")

        assert result["depleted"] == 0
        assert result["low"] == 1

    def test_calculate_readiness_impact(self, db_session, player_units):
        """Test readiness impact calculation"""
        generator = DebriefingGenerator()

        # Set different readiness levels
        player_units[0].readiness = SupplyLevel.EXHAUSTED
        player_units[1].readiness = SupplyLevel.DEPLETED

        result = generator._calculate_readiness_impact(player_units)

        assert result == 2

    def test_evaluate_mission_success(self):
        """Test mission evaluation - success case"""
        generator = DebriefingGenerator()

        stats = {
            "player": {"casualty_rate": 20.0},
            "enemy": {"destruction_rate": 60.0}
        }
        game = None

        result = generator._evaluate_mission(stats, game)

        assert result["status"] == "success"
        assert "acceptable losses" in result["description"]

    def test_evaluate_mission_partial(self):
        """Test mission evaluation - partial success case"""
        generator = DebriefingGenerator()

        stats = {
            "player": {"casualty_rate": 40.0},
            "enemy": {"destruction_rate": 40.0}
        }
        game = None

        result = generator._evaluate_mission(stats, game)

        assert result["status"] == "partial"

    def test_evaluate_mission_failed(self):
        """Test mission evaluation - failure case"""
        generator = DebriefingGenerator()

        stats = {
            "player": {"casualty_rate": 60.0},
            "enemy": {"destruction_rate": 10.0}
        }
        game = None

        result = generator._evaluate_mission(stats, game)

        assert result["status"] == "failed"

    def test_calculate_grade_s(self):
        """Test grade calculation - S rank"""
        generator = DebriefingGenerator()

        stats = {
            "player": {"casualty_rate": 10.0},
            "enemy": {"destruction_rate": 80.0},
            "resources": {"ammo_depleted_units": 0, "fuel_depleted_units": 0}
        }
        mission_result = {"status": "success"}

        grade = generator._calculate_grade(stats, mission_result)

        assert grade == "S"

    def test_calculate_grade_a(self):
        """Test grade calculation - A rank"""
        generator = DebriefingGenerator()

        stats = {
            "player": {"casualty_rate": 0.0},
            "enemy": {"destruction_rate": 50.0},
            "resources": {"ammo_depleted_units": 0, "fuel_depleted_units": 0}
        }
        mission_result = {"status": "partial"}

        grade = generator._calculate_grade(stats, mission_result)

        assert grade == "A"

    def test_calculate_grade_b(self):
        """Test grade calculation - B rank"""
        generator = DebriefingGenerator()

        stats = {
            "player": {"casualty_rate": 10.0},
            "enemy": {"destruction_rate": 50.0},
            "resources": {"ammo_depleted_units": 0, "fuel_depleted_units": 0}
        }
        mission_result = {"status": "partial"}

        grade = generator._calculate_grade(stats, mission_result)

        assert grade == "B"

    def test_calculate_grade_c(self):
        """Test grade calculation - C rank"""
        generator = DebriefingGenerator()

        stats = {
            "player": {"casualty_rate": 20.0},
            "enemy": {"destruction_rate": 30.0},
            "resources": {"ammo_depleted_units": 3, "fuel_depleted_units": 0}
        }
        mission_result = {"status": "partial"}

        grade = generator._calculate_grade(stats, mission_result)

        assert grade == "C"

    def test_calculate_grade_d(self):
        """Test grade calculation - D rank"""
        generator = DebriefingGenerator()

        stats = {
            "player": {"casualty_rate": 80.0},
            "enemy": {"destruction_rate": 10.0},
            "resources": {"ammo_depleted_units": 5, "fuel_depleted_units": 5}
        }
        mission_result = {"status": "failed"}

        grade = generator._calculate_grade(stats, mission_result)

        assert grade == "D"

    def test_calculate_resource_score(self):
        """Test resource score calculation"""
        generator = DebriefingGenerator()

        # No depletion
        resources = {"ammo_depleted_units": 0, "fuel_depleted_units": 0}
        score = generator._calculate_resource_score(resources)
        assert score == 10

        # 1-2 units
        resources = {"ammo_depleted_units": 1, "fuel_depleted_units": 0}
        score = generator._calculate_resource_score(resources)
        assert score == 7

        # 3-5 units
        resources = {"ammo_depleted_units": 2, "fuel_depleted_units": 2}
        score = generator._calculate_resource_score(resources)
        assert score == 4

        # 6+ units
        resources = {"ammo_depleted_units": 3, "fuel_depleted_units": 3}
        score = generator._calculate_resource_score(resources)
        assert score == 1

    def test_fallback_commentary_success(self):
        """Test fallback commentary - success"""
        generator = DebriefingGenerator()

        summary = {"mission_status": "success"}
        result = generator._fallback_commentary(summary)

        assert "Excellent" in result

    def test_fallback_commentary_partial(self):
        """Test fallback commentary - partial"""
        generator = DebriefingGenerator()

        summary = {"mission_status": "partial"}
        result = generator._fallback_commentary(summary)

        assert "mixed results" in result

    def test_fallback_commentary_failed(self):
        """Test fallback commentary - failed"""
        generator = DebriefingGenerator()

        summary = {"mission_status": "failed"}
        result = generator._fallback_commentary(summary)

        assert "did not achieve" in result

    def test_generate_recommendations_casualties(self):
        """Test recommendations based on casualties"""
        generator = DebriefingGenerator()

        stats = {
            "player": {"casualty_rate": 40.0},
            "resources": {"ammo_depleted_units": 0, "fuel_depleted_units": 0},
            "enemy": {"destruction_rate": 20.0}
        }
        mission_result = {"status": "partial"}

        result = generator._generate_recommendations(stats, mission_result)

        assert any("casualties" in r for r in result)

    def test_generate_recommendations_ammo(self):
        """Test recommendations based on ammo depletion"""
        generator = DebriefingGenerator()

        stats = {
            "player": {"casualty_rate": 10.0},
            "resources": {"ammo_depleted_units": 1, "fuel_depleted_units": 0},
            "enemy": {"destruction_rate": 50.0}
        }
        mission_result = {"status": "success"}

        result = generator._generate_recommendations(stats, mission_result)

        assert any("ammunition" in r for r in result)

    def test_generate_recommendations_fuel(self):
        """Test recommendations based on fuel depletion"""
        generator = DebriefingGenerator()

        stats = {
            "player": {"casualty_rate": 10.0},
            "resources": {"ammo_depleted_units": 0, "fuel_depleted_units": 1},
            "enemy": {"destruction_rate": 50.0}
        }
        mission_result = {"status": "success"}

        result = generator._generate_recommendations(stats, mission_result)

        assert any("fuel" in r for r in result)

    def test_generate_recommendations_aggressive(self):
        """Test recommendations for aggressive tactics"""
        generator = DebriefingGenerator()

        stats = {
            "player": {"casualty_rate": 20.0},
            "resources": {"ammo_depleted_units": 0, "fuel_depleted_units": 0},
            "enemy": {"destruction_rate": 10.0}
        }
        mission_result = {"status": "failed"}

        result = generator._generate_recommendations(stats, mission_result)

        assert any("aggressive" in r for r in result)

    def test_generate_recommendations_satisfactory(self):
        """Test recommendations when performance is satisfactory"""
        generator = DebriefingGenerator()

        stats = {
            "player": {"casualty_rate": 10.0},
            "resources": {"ammo_depleted_units": 0, "fuel_depleted_units": 0},
            "enemy": {"destruction_rate": 60.0}
        }
        mission_result = {"status": "success"}

        result = generator._generate_recommendations(stats, mission_result)

        assert any("satisfactory" in r for r in result)

    @pytest.mark.asyncio
    async def test_generate_commentary_with_ai(self):
        """Test commentary generation with AI"""
        generator = DebriefingGenerator()

        summary = {
            "operations": {
                "total_turns": 5
            },
            "player": {
                "casualty_rate": 20.0
            },
            "enemy": {
                "destruction_rate": 60.0
            },
            "resources": {
                "ammo_depleted_units": 0,
                "fuel_depleted_units": 0
            }
        }

        # Mock AI client
        with patch.object(generator.ai, 'generate_debriefing_comment', new_callable=AsyncMock) as mock_ai:
            mock_ai.return_value = "AI generated commentary"

            result = await generator._generate_commentary(summary, {"status": "success"}, None)

            assert result == "AI generated commentary"
            mock_ai.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_commentary_fallback(self):
        """Test commentary generation fallback when AI fails"""
        generator = DebriefingGenerator()

        summary = {
            "operations": {
                "total_turns": 5
            },
            "player": {
                "casualty_rate": 20.0
            },
            "enemy": {
                "destruction_rate": 60.0
            },
            "resources": {
                "ammo_depleted_units": 0,
                "fuel_depleted_units": 0
            }
        }

        # Mock AI client to raise exception
        with patch.object(generator.ai, 'generate_debriefing_comment', new_callable=AsyncMock) as mock_ai:
            mock_ai.side_effect = Exception("AI unavailable")

            result = await generator._generate_commentary(summary, {"status": "success"}, None)

            assert "Excellent" in result

    @pytest.mark.asyncio
    async def test_generate_debriefing(self, db_session, sample_game, player_units, enemy_units):
        """Test full debriefing generation"""
        generator = DebriefingGenerator()

        # Mock AI
        with patch.object(generator.ai, 'generate_debriefing_comment', new_callable=AsyncMock) as mock_ai:
            mock_ai.return_value = "Test commentary"

            result = await generator.generate_debriefing(sample_game.id, db_session)

            assert "game_id" in result
            assert "statistics" in result
            assert "mission_result" in result
            assert "grade" in result
            assert "commentary" in result
            assert "recommendations" in result

            assert result["grade"] in ["S", "A", "B", "C", "D"]

    @pytest.mark.asyncio
    async def test_generate_debriefing_game_not_found(self, db_session):
        """Test debriefing generation with non-existent game"""
        generator = DebriefingGenerator()

        with pytest.raises(ValueError):
            await generator.generate_debriefing(999, db_session)

    @pytest.mark.asyncio
    async def test_generate_debriefing_with_orders(self, db_session, sample_game, player_units, enemy_units, sample_turn):
        """Test debriefing generation with orders in turns"""
        # Add orders to turn
        order = Order(
            game_id=sample_game.id,
            unit_id=player_units[0].id,
            turn_id=sample_turn.id,
            order_type=OrderType.MOVE,
            intent="Move forward",
            location_x=20,
            location_y=20
        )
        db_session.add(order)
        db_session.commit()

        generator = DebriefingGenerator()

        with patch.object(generator.ai, 'generate_debriefing_comment', new_callable=AsyncMock) as mock_ai:
            mock_ai.return_value = "Test commentary"

            result = await generator.generate_debriefing(sample_game.id, db_session)

            assert result["statistics"]["operations"]["total_orders"] == 1

    def test_calculate_statistics_empty_units(self, db_session):
        """Test statistics calculation with no units"""
        # Create game with no units
        game = Game(name="Empty Game", current_turn=1, current_time="06:00", weather="clear")
        db_session.add(game)
        db_session.commit()

        generator = DebriefingGenerator()
        stats = generator._calculate_statistics(db_session, game)

        assert stats["player"]["initial_count"] == 0
        assert stats["enemy"]["initial_count"] == 0
        assert stats["player"]["casualty_rate"] == 0.0
        assert stats["enemy"]["destruction_rate"] == 0.0

    def test_calculate_statistics_heavy_damage(self, db_session, sample_game, player_units):
        """Test statistics with heavily damaged units"""
        player_units[0].status = UnitStatus.HEAVY_DAMAGE
        player_units[1].status = UnitStatus.MEDIUM_DAMAGE

        generator = DebriefingGenerator()
        stats = generator._calculate_statistics(db_session, sample_game)

        assert stats["player"]["damaged"] == 2
        assert stats["player"]["light_damage"] == 0
        assert stats["player"]["intact"] == 0
