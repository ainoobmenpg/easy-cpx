"""Tests for AI client (ai_client.py)"""
import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
import httpx
from app.services.ai_client import AIClient


class TestAIClientFallback:
    """Test fallback methods when API is not available"""

    def setup_method(self):
        """Set up test client without API key"""
        self.client = AIClient()
        self.client.api_key = ""  # Force fallback mode

    def test_fallback_parse_attack(self):
        """Test fallback parser with attack keyword"""
        result = self.client._fallback_parse("第1大隊に攻撃命令")
        assert result["order_type"] == "attack"
        assert "攻撃" in result["intent"]

    def test_fallback_parse_defend(self):
        """Test fallback parser with defend keyword"""
        result = self.client._fallback_parse("防衛任務")
        assert result["order_type"] == "defend"

    def test_fallback_parse_defend_alt(self):
        """Test fallback parser with alternate defend keyword"""
        result = self.client._fallback_parse("防御態勢")
        assert result["order_type"] == "defend"

    def test_fallback_parse_recon(self):
        """Test fallback parser with recon keyword"""
        result = self.client._fallback_parse("偵察任務")
        assert result["order_type"] == "recon"

    def test_fallback_parse_retreat(self):
        """Test fallback parser with retreat keyword"""
        result = self.client._fallback_parse("撤退用意")
        assert result["order_type"] == "retreat"

    def test_fallback_parse_supply(self):
        """Test fallback parser with supply keyword"""
        result = self.client._fallback_parse("補給線確保")
        assert result["order_type"] == "supply"

    def test_fallback_parse_english_keywords(self):
        """Test fallback parser with English keywords"""
        result = self.client._fallback_parse("move forward")
        assert result["order_type"] == "move"
        assert "Fallback parser used" in result["assumptions"][0]

    def test_fallback_parse_english_attack(self):
        """Test fallback parser with English attack keyword"""
        result = self.client._fallback_parse("attack enemy")
        assert result["order_type"] == "attack"

    def test_fallback_parse_english_defend(self):
        """Test fallback parser with English defend keyword"""
        result = self.client._fallback_parse("defend position")
        assert result["order_type"] == "defend"

    def test_fallback_parse_english_recon(self):
        """Test fallback parser with English recon keyword"""
        result = self.client._fallback_parse("reconnaissance mission")
        assert result["order_type"] == "recon"

    def test_fallback_parse_english_retreat(self):
        """Test fallback parser with English retreat keyword"""
        result = self.client._fallback_parse("retreat to safety")
        assert result["order_type"] == "retreat"

    def test_fallback_parse_english_supply(self):
        """Test fallback parser with English supply keyword"""
        result = self.client._fallback_parse("supply line")
        assert result["order_type"] == "supply"

    def test_fallback_parse_default(self):
        """Test fallback parser with no keywords"""
        result = self.client._fallback_parse("待機命令")
        assert result["order_type"] == "move"  # Default
        assert result["parameters"]["priority"] == "normal"

    def test_fallback_sitrep_basic(self):
        """Test fallback SITREP generation"""
        game_state = {
            "turn": 1,
            "time": "06:00",
            "weather": "clear",
            "units": [
                {"id": "u1", "side": "player", "name": "第1大隊"},
                {"id": "u2", "side": "enemy", "name": "敵主力"}
            ]
        }
        order_results = [{"order_id": 1, "outcome": "success"}]

        result = self.client._fallback_sitrep(game_state, order_results)

        assert result["turn"] == 1
        assert len(result["sections"]) == 3
        assert result["sections"][0]["type"] == "overview"
        assert result["sections"][1]["type"] == "unit_status"
        assert result["sections"][2]["type"] == "orders_result"
        assert result["sections"][0]["confidence"] == "confirmed"

    def test_fallback_sitrep_no_units(self):
        """Test fallback SITREP with no units"""
        game_state = {"turn": 2, "time": "12:00", "weather": "rain", "units": []}
        order_results = []

        result = self.client._fallback_sitrep(game_state, order_results)

        assert "Player forces: 0 units" in result["sections"][1]["content"]
        assert "Enemy forces: 0 units" in result["sections"][1]["content"]

    def test_fallback_excon_no_enemy_units(self):
        """Test fallback ExCon with no enemy units"""
        game_state = {"units": []}
        result = self.client._fallback_excon(game_state)
        assert result == {"orders": []}

    def test_fallback_excon_player_in_range(self):
        """Test fallback ExCon when player is in range"""
        game_state = {
            "units": [
                {"id": "enemy1", "side": "enemy", "x": 10, "y": 25},
                {"id": "player1", "side": "player", "x": 14, "y": 25}
            ]
        }
        result = self.client._fallback_excon(game_state)
        assert len(result["orders"]) >= 1
        assert result["orders"][0]["order_type"] == "attack"
        assert result["orders"][0]["target_units"] == ["player1"]

    def test_fallback_excon_numerically_superior(self):
        """Test fallback ExCon when enemy is numerically superior"""
        game_state = {
            "units": [
                {"id": "enemy1", "side": "enemy", "x": 35, "y": 25},
                {"id": "enemy2", "side": "enemy", "x": 38, "y": 20},
                {"id": "player1", "side": "player", "x": 10, "y": 25}
            ]
        }
        result = self.client._fallback_excon(game_state)
        assert len(result["orders"]) >= 2
        # At least one should be move toward player
        order_types = [o["order_type"] for o in result["orders"]]
        assert "move" in order_types

    def test_fallback_excon_numerically_inferior(self):
        """Test fallback ExCon when enemy is numerically inferior"""
        game_state = {
            "units": [
                {"id": "enemy1", "side": "enemy", "x": 30, "y": 25},
                {"id": "player1", "side": "player", "x": 10, "y": 25},
                {"id": "player2", "side": "player", "x": 12, "y": 27}
            ]
        }
        result = self.client._fallback_excon(game_state)
        assert len(result["orders"]) >= 1
        # Should approach cautiously (move with small advance)
        assert result["orders"][0]["order_type"] == "move"

    def test_fallback_excon_no_player_units(self):
        """Test fallback ExCon when no player units exist"""
        game_state = {
            "units": [
                {"id": "enemy1", "side": "enemy", "x": 30, "y": 25}
            ]
        }
        result = self.client._fallback_excon(game_state)
        assert result["orders"][0]["order_type"] == "move"

    def test_fallback_excon_max_orders_limited(self):
        """Test fallback ExCon limits orders to 5"""
        game_state = {
            "units": [
                {"id": f"enemy{i}", "side": "enemy", "x": 40 - i, "y": 25}
                for i in range(10)
            ] + [
                {"id": f"player{i}", "side": "player", "x": i * 2, "y": 25}
                for i in range(3)
            ]
        }
        result = self.client._fallback_excon(game_state)
        assert len(result["orders"]) <= 5

    def test_fallback_commentary_success(self):
        """Test fallback commentary with success status"""
        summary = {"mission_status": "success", "player_casualty_rate": 10}
        result = self.client._fallback_commentary(summary)
        assert "素晴らしい" in result

    def test_fallback_commentary_partial(self):
        """Test fallback commentary with partial success"""
        summary = {"mission_status": "partial", "player_casualty_rate": 30}
        result = self.client._fallback_commentary(summary)
        assert "部分的成功" in result

    def test_fallback_commentary_failure_high_casualties(self):
        """Test fallback commentary with failure and high casualties"""
        summary = {"mission_status": "failure", "player_casualty_rate": 60}
        result = self.client._fallback_commentary(summary)
        assert "intended objective" in result

    def test_fallback_commentary_failure_low_casualties(self):
        """Test fallback commentary with failure but low casualties"""
        summary = {"mission_status": "failure", "player_casualty_rate": 20}
        result = self.client._fallback_commentary(summary)
        assert "健闘" in result


class TestAIClientWithAPIKey:
    """Test methods when API key is available"""

    def setup_method(self):
        """Set up test client with API key"""
        self.client = AIClient()
        self.client.api_key = "test_api_key"

    @pytest.mark.asyncio
    async def test_parse_order_with_api_success(self):
        """Test parse_order with successful API response"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "order_type": "attack",
                        "target_units": ["unit1"],
                        "intent": "destroy enemy",
                        "location": {"x": 20, "y": 25},
                        "parameters": {"priority": "high"},
                        "assumptions": []
                    })
                }
            }]
        }

        # Mock the async context manager
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("app.services.ai_client.httpx.AsyncClient", return_value=mock_client):
            result = await self.client.parse_order("攻撃用意", {"turn": 1, "time": "06:00"})

        assert result["order_type"] == "attack"
        assert result["target_units"] == ["unit1"]

    @pytest.mark.asyncio
    async def test_parse_order_api_error_fallback(self):
        """Test parse_order falls back on API error"""
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=Exception("API Error"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("app.services.ai_client.httpx.AsyncClient", return_value=mock_client):
            result = await self.client.parse_order("攻撃命令", {"turn": 1})

        assert "order_type" in result
        assert "assumptions" in result
        assert "Fallback parser used" in result["assumptions"][0]

    @pytest.mark.asyncio
    async def test_generate_sitrep_with_api_success(self):
        """Test generate_sitrep with successful API response"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "turn": 1,
                        "timestamp": "2024-01-01T12:00:00",
                        "sections": [
                            {"type": "overview", "content": "Test", "confidence": "confirmed"}
                        ],
                        "map_updates": []
                    })
                }
            }]
        }

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        game_state = {"turn": 1, "time": "06:00", "units": []}
        with patch("app.services.ai_client.httpx.AsyncClient", return_value=mock_client):
            result = await self.client.generate_sitrep(game_state, [])

        assert result["turn"] == 1
        assert len(result["sections"]) == 1

    @pytest.mark.asyncio
    async def test_generate_sitrep_api_error_fallback(self):
        """Test generate_sitrep falls back on API error"""
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=Exception("API Error"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("app.services.ai_client.httpx.AsyncClient", return_value=mock_client):
            result = await self.client.generate_sitrep({"turn": 1}, [])

        assert "sections" in result
        assert result["turn"] == 1

    @pytest.mark.asyncio
    async def test_generate_excon_orders_with_api_success(self):
        """Test generate_excon_orders with successful API response"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "orders": [
                            {
                                "unit_id": "enemy1",
                                "order_type": "attack",
                                "target": {"x": 10, "y": 25},
                                "target_units": ["player1"],
                                "intent": "attack player"
                            }
                        ]
                    })
                }
            }]
        }

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        game_state = {"turn": 1, "units": [{"id": "enemy1", "side": "enemy"}]}
        with patch("app.services.ai_client.httpx.AsyncClient", return_value=mock_client):
            result = await self.client.generate_excon_orders(game_state)

        assert len(result["orders"]) == 1
        assert result["orders"][0]["order_type"] == "attack"

    @pytest.mark.asyncio
    async def test_generate_excon_orders_api_error_fallback(self):
        """Test generate_excon_orders falls back on API error"""
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=Exception("API Error"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("app.services.ai_client.httpx.AsyncClient", return_value=mock_client):
            result = await self.client.generate_excon_orders({"units": []})

        assert "orders" in result

    @pytest.mark.asyncio
    async def test_generate_debriefing_comment_with_api_success(self):
        """Test generate_debriefing_comment with successful API response"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "Great job commander."
                }
            }]
        }

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        summary = {"total_turns": 5}
        with patch("app.services.ai_client.httpx.AsyncClient", return_value=mock_client):
            result = await self.client.generate_debriefing_comment(summary)

        assert result == "Great job commander."

    @pytest.mark.asyncio
    async def test_generate_debriefing_comment_api_error_fallback(self):
        """Test generate_debriefing_comment falls back on API error"""
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=Exception("API Error"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("app.services.ai_client.httpx.AsyncClient", return_value=mock_client):
            result = await self.client.generate_debriefing_comment({"mission_status": "success"})

        assert "素晴らしい" in result

    @pytest.mark.asyncio
    async def test_generate_debriefing_comment_empty_response(self):
        """Test generate_debriefing_comment with empty response"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": ""
                }
            }]
        }

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        summary = {"mission_status": "partial"}
        with patch("app.services.ai_client.httpx.AsyncClient", return_value=mock_client):
            result = await self.client.generate_debriefing_comment(summary)

        assert "部分的成功" in result


class TestAIClientEdgeCases:
    """Test edge cases and boundary conditions"""

    def setup_method(self):
        """Set up test client"""
        self.client = AIClient()
        self.client.api_key = ""  # Force fallback mode

    def test_fallback_parse_empty_input(self):
        """Test fallback parser with empty input"""
        result = self.client._fallback_parse("")
        assert result["order_type"] == "move"
        assert result["parameters"]["priority"] == "normal"

    def test_fallback_parse_mixed_keywords(self):
        """Test fallback parser with mixed language keywords"""
        result = self.client._fallback_parse("攻撃と防守")
        # First matching keyword wins
        assert result["order_type"] == "attack"

    def test_fallback_sitrep_missing_keys(self):
        """Test fallback SITREP with missing game state keys"""
        game_state = {}
        order_results = []

        result = self.client._fallback_sitrep(game_state, order_results)

        assert result["turn"] == 1  # Default
        assert "06:00" in result["sections"][0]["content"]  # Default time

    def test_fallback_excon_unit_without_position(self):
        """Test fallback ExCon with unit missing position"""
        game_state = {
            "units": [
                {"id": "enemy1", "side": "enemy"},  # No x, y
                {"id": "player1", "side": "player", "x": 10, "y": 25}
            ]
        }
        result = self.client._fallback_excon(game_state)
        # Should use default position (25)
        assert len(result["orders"]) >= 1

    def test_fallback_commentary_missing_status(self):
        """Test fallback commentary with missing status"""
        summary = {}  # No mission_status
        result = self.client._fallback_commentary(summary)
        # Should default to failure without casualties > 50
        assert "intended objective" in result

    @pytest.mark.asyncio
    async def test_parse_order_game_context_all_fields(self):
        """Test parse_order with complete game context"""
        self.client.api_key = "test_key"
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "order_type": "defend",
                        "target_units": [],
                        "intent": "defend area",
                        "location": None,
                        "parameters": {"priority": "low"},
                        "assumptions": []
                    })
                }
            }]
        }

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        game_context = {
            "turn": 5,
            "time": "18:00",
            "weather": "rain"
        }
        with patch("app.services.ai_client.httpx.AsyncClient", return_value=mock_client):
            result = await self.client.parse_order("defend position", game_context)

        assert result["order_type"] == "defend"

    @pytest.mark.asyncio
    async def test_generate_sitrep_empty_units(self):
        """Test generate_sitrep with empty units list"""
        self.client.api_key = "test_key"
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "turn": 1,
                        "timestamp": "2024-01-01T12:00:00",
                        "sections": [],
                        "map_updates": []
                    })
                }
            }]
        }

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("app.services.ai_client.httpx.AsyncClient", return_value=mock_client):
            result = await self.client.generate_sitrep({}, [])

        assert "sections" in result
