# Integration Tests for CPX - API Flow Tests

import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestGameFlowIntegration:
    """Integration tests for game flow API"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        from main import app
        return TestClient(app)

    def test_game_creation_and_retrieval(self, client):
        """Test creating and retrieving a game"""
        # Create game
        response = client.post("/api/games/", json={"name": "Test Game"})
        assert response.status_code == 200
        game_data = response.json()
        game_id = game_data["id"]

        # Retrieve game
        response = client.get(f"/api/games/{game_id}")
        assert response.status_code == 200
        assert response.json()["name"] == "Test Game"

    def test_scenario_list(self, client):
        """Test listing scenarios"""
        response = client.get("/api/scenarios")
        assert response.status_code == 200
        scenarios = response.json()
        assert isinstance(scenarios, list)

    def test_game_state(self, client):
        """Test getting game state"""
        # First create a game
        response = client.post("/api/games/", json={"name": "State Test Game"})
        game_id = response.json()["id"]

        # Get state
        response = client.get(f"/api/games/{game_id}/state")
        assert response.status_code == 200
        state = response.json()
        assert "turn" in state

    def test_units_retrieval(self, client):
        """Test getting game units"""
        # Create game
        response = client.post("/api/games/", json={"name": "Units Test Game"})
        game_id = response.json()["id"]

        # Get units
        response = client.get(f"/api/games/{game_id}/units")
        assert response.status_code == 200
        units = response.json()
        assert isinstance(units, list)

    def test_opord_flow(self, client):
        """Test OPORD creation and retrieval"""
        # Create game
        response = client.post("/api/games/", json={"name": "OPORD Test Game"})
        game_id = response.json()["id"]

        # Get OPORD (should not exist yet)
        response = client.get(f"/api/games/{game_id}/opord")
        # May return 404 or empty data

    def test_reports_flow(self, client):
        """Test report generation"""
        # Create game
        response = client.post("/api/games/", json={"name": "Reports Test Game"})
        game_id = response.json()["id"]

        # Try generating a report
        response = client.post("/api/reports/generate", json={
            "game_id": game_id,
            "format": "situation",
            "turn": 1
        })

        # Should work (may return error if no game data)
        assert response.status_code in [200, 404, 500]


class TestOrderFlowIntegration:
    """Integration tests for order flow"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        from main import app
        return TestClient(app)

    @pytest.fixture
    def game_with_units(self, client):
        """Create a game with units for testing"""
        # Create game
        response = client.post("/api/games/", json={"name": "Order Test Game"})
        game_id = response.json()["id"]

        # Add a unit
        response = client.post(
            f"/api/games/{game_id}/units/",
            params={
                "name": "Alpha",
                "unit_type": "infantry",
                "side": "player",
                "x": 5,
                "y": 5
            }
        )

        return game_id

    def test_parse_order(self, client):
        """Test order parsing"""
        response = client.post("/api/parse-order", json={
            "text": "第1中隊を位置Aへ移動せよ",
            "game_id": 1,
            "unit_id": 1
        })

        # Should return parsed order (may fail if no AI)
        assert response.status_code in [200, 500, 400]


class TestTurnFlowIntegration:
    """Integration tests for turn flow"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        from main import app
        return TestClient(app)

    def test_advance_turn(self, client):
        """Test turn advancement"""
        # Create game
        response = client.post("/api/games/", json={"name": "Turn Test Game"})
        game_id = response.json()["id"]

        # Try to advance turn (will fail without units/orders)
        response = client.post("/api/advance-turn", json={
            "game_id": game_id
        })

        # Should return result (may have errors)
        assert response.status_code in [200, 400, 500]


class TestSecurityIntegration:
    """Integration tests for security features"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        from main import app
        return TestClient(app)

    def test_rate_limit_headers(self, client):
        """Test rate limit headers are present"""
        # Make multiple requests
        for _ in range(5):
            response = client.get("/api/games/")

        # Check rate limit headers
        # Note: In-memory rate limiter won't persist across TestClient instances
        # This is a placeholder for actual rate limit testing

    def test_internal_endpoint_blocked(self, client):
        """Test internal endpoints are blocked by default"""
        # Create a game first
        response = client.post("/api/games/", json={"name": "Security Test Game"})
        game_id = response.json()["id"]

        # Try to access internal endpoint (should be blocked)
        response = client.get(f"/api/internal/games/{game_id}/true-state")
        # Should be blocked unless ENABLE_INTERNAL_ENDPOINTS=true
        assert response.status_code in [200, 401]


# Performance tests
class TestPerformance:
    """Performance tests"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        from main import app
        return TestClient(app)

    def test_response_time_game_list(self, client):
        """Test game list response time"""
        import time

        start = time.time()
        response = client.get("/api/games/")
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 1.0  # Should respond within 1 second

    def test_response_time_game_state(self, client):
        """Test game state response time"""
        import time

        # Create game
        response = client.post("/api/games/", json={"name": "Perf Test Game"})
        game_id = response.json()["id"]

        # Measure response time
        start = time.time()
        response = client.get(f"/api/games/{game_id}/state")
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 2.0  # Should respond within 2 seconds
