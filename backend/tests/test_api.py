"""Tests for API endpoints"""
import pytest
from fastapi.testclient import TestClient
from app.models import Base, Game
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Create test database before importing app
TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def test_db():
    """Create fresh database for each test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(test_db):
    """Create test client with database override"""
    from app.database import get_db
    from main import app

    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


class TestHealthEndpoint:
    """Test health check endpoint"""

    def test_health_check(self, client):
        """Test /health returns healthy"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    def test_root(self, client):
        """Test / returns message"""
        response = client.get("/")
        assert response.status_code == 200
        assert "Operational CPX API" in response.json()["message"]


class TestGameEndpoints:
    """Test game API endpoints"""

    def test_create_game(self, client, test_db):
        """Test POST /api/games/ creates a game"""
        response = client.post("/api/games/", json={"name": "Test Game"})
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Game"
        assert "id" in data

    def test_get_game(self, client, test_db):
        """Test GET /api/games/{id} returns game"""
        # Create game first
        game = Game(name="Test Game")
        test_db.add(game)
        test_db.commit()
        test_db.refresh(game)

        response = client.get(f"/api/games/{game.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Game"
        assert data["current_turn"] == 1

    def test_get_game_not_found(self, client):
        """Test GET /api/games/{id} with invalid id"""
        response = client.get("/api/games/999")
        assert response.status_code == 404

    def test_get_game_units(self, client, test_db):
        """Test GET /api/games/{id}/units - returns FoW-filtered game state"""
        # Create game and units
        from app.models import Unit, UnitStatus, SupplyLevel

        game = Game(name="Test Game")
        test_db.add(game)
        test_db.commit()
        test_db.refresh(game)

        unit = Unit(
            game_id=game.id,
            name="Test Unit",
            unit_type="infantry",
            side="player",
            x=10,
            y=10,
            status=UnitStatus.INTACT,
            ammo=SupplyLevel.FULL,
            fuel=SupplyLevel.FULL,
            readiness=SupplyLevel.FULL
        )
        test_db.add(unit)
        test_db.commit()

        response = client.get(f"/api/games/{game.id}/units")
        assert response.status_code == 200
        data = response.json()
        # Now returns full game state with FoW applied (not just units array)
        assert "units" in data
        assert len(data["units"]) == 1
        assert data["units"][0]["name"] == "Test Unit"

    def test_create_unit(self, client, test_db):
        """Test POST /api/games/{id}/units/"""
        game = Game(name="Test Game")
        test_db.add(game)
        test_db.commit()
        test_db.refresh(game)

        response = client.post(
            f"/api/games/{game.id}/units/",
            params={
                "name": "New Unit",
                "unit_type": "infantry",
                "side": "player",
                "x": 10,
                "y": 20
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Unit"


class TestOrderEndpoints:
    """Test order API endpoints"""

    def test_parse_order(self, client, test_db):
        """Test POST /api/parse-order"""
        game = Game(name="Test Game", current_turn=1, current_time="06:00", weather="clear")
        test_db.add(game)
        test_db.commit()
        test_db.refresh(game)

        response = client.post(
            "/api/parse-order",
            json={
                "player_input": "前進して攻撃",
                "game_id": game.id
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "order_type" in data

    def test_parse_order_game_not_found(self, client):
        """Test parse order with invalid game"""
        response = client.post(
            "/api/parse-order",
            json={
                "player_input": "test",
                "game_id": 999
            }
        )
        assert response.status_code == 404

    def test_create_order(self, client, test_db):
        """Test POST /api/orders/"""
        from app.models import Unit, UnitStatus, SupplyLevel

        game = Game(name="Test Game")
        test_db.add(game)
        test_db.commit()
        test_db.refresh(game)

        unit = Unit(
            game_id=game.id,
            name="Test Unit",
            unit_type="infantry",
            side="player",
            x=10,
            y=10,
            status=UnitStatus.INTACT,
            ammo=SupplyLevel.FULL,
            fuel=SupplyLevel.FULL,
            readiness=SupplyLevel.FULL
        )
        test_db.add(unit)
        test_db.commit()
        test_db.refresh(unit)

        response = client.post(
            "/api/orders/",
            json={
                "unit_id": unit.id,
                "order_type": "move",
                "intent": "Move forward",
                "location_x": 20,
                "location_y": 20
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "submitted"

    def test_create_order_unit_not_found(self, client, test_db):
        """Test create order with invalid unit"""
        response = client.post(
            "/api/orders/",
            json={
                "unit_id": 999,
                "order_type": "move",
                "intent": "test"
            }
        )
        assert response.status_code == 404


class TestGameStateEndpoint:
    """Test game state endpoint"""

    def test_get_game_state(self, client, test_db):
        """Test GET /api/games/{id}/state"""
        game = Game(name="Test Game", current_turn=1, current_time="06:00", weather="clear")
        test_db.add(game)
        test_db.commit()
        test_db.refresh(game)

        response = client.get(f"/api/games/{game.id}/state")
        assert response.status_code == 200
        data = response.json()
        assert data["turn"] == 1
        assert data["time"] == "06:00"

    def test_get_game_state_not_found(self, client):
        """Test get game state with invalid id"""
        response = client.get("/api/games/999/state")
        assert response.status_code == 404


class TestAdvanceTurnEndpoint:
    """Test advance turn endpoint"""

    def test_advance_turn(self, client, test_db):
        """Test POST /api/advance-turn"""
        from app.models import Unit, UnitStatus, SupplyLevel, Turn

        game = Game(name="Test Game", current_turn=1, current_time="06:00", weather="clear")
        test_db.add(game)
        test_db.commit()
        test_db.refresh(game)

        # Add a unit
        unit = Unit(
            game_id=game.id,
            name="Test Unit",
            unit_type="infantry",
            side="player",
            x=10,
            y=10,
            status=UnitStatus.INTACT,
            ammo=SupplyLevel.FULL,
            fuel=SupplyLevel.FULL,
            readiness=SupplyLevel.FULL
        )
        test_db.add(unit)
        test_db.commit()

        # Add an order
        from app.models import Order, OrderType
        turn = Turn(
            game_id=game.id,
            turn_number=1,
            time="06:00",
            weather="clear",
            phase="orders"
        )
        test_db.add(turn)
        test_db.commit()
        test_db.refresh(turn)

        order = Order(
            game_id=game.id,
            unit_id=unit.id,
            turn_id=turn.id,
            order_type=OrderType.MOVE,
            intent="Move forward",
            location_x=20,
            location_y=20
        )
        test_db.add(order)
        test_db.commit()

        response = client.post(
            "/api/advance-turn",
            json={"game_id": game.id}
        )
        assert response.status_code == 200
        data = response.json()
        assert "turn" in data
        assert "results" in data

    def test_advance_turn_game_not_found(self, client):
        """Test advance turn with invalid game"""
        response = client.post(
            "/api/advance-turn",
            json={"game_id": 999}
        )
        assert response.status_code == 404


class TestSitrepEndpoint:
    """Test SITREP endpoint"""

    def test_get_sitrep(self, client, test_db):
        """Test GET /api/games/{id}/sitrep"""
        from app.models import Turn

        game = Game(name="Test Game", current_turn=2, current_time="07:00", weather="clear")
        test_db.add(game)
        test_db.commit()
        test_db.refresh(game)

        # Add a turn with SITREP
        turn = Turn(
            game_id=game.id,
            turn_number=1,
            time="06:00",
            weather="clear",
            phase="orders",
            sitrep="Test SITREP message"
        )
        test_db.add(turn)
        test_db.commit()

        response = client.get(f"/api/games/{game.id}/sitrep")
        assert response.status_code == 200

    def test_get_sitrep_not_found(self, client, test_db):
        """Test get SITREP with no available SITREP"""
        game = Game(name="Test Game", current_turn=1, current_time="06:00", weather="clear")
        test_db.add(game)
        test_db.commit()
        test_db.refresh(game)

        response = client.get(f"/api/games/{game.id}/sitrep")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    def test_get_sitrep_game_not_found(self, client):
        """Test get SITREP with invalid game"""
        response = client.get("/api/games/999/sitrep")
        assert response.status_code == 404
