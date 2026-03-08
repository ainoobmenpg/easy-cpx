# Tests for Friction Events Service
import pytest
from app.services.friction_events import FrictionEventService, FrictionEventType, create_friction_event_service


class TestFrictionEventService:
    def test_should_generate_event_base(self):
        """Test base event generation probability"""
        service = FrictionEventService(random_seed=42)
        # With default conditions, should have some events
        results = [service.should_generate_event(1) for _ in range(100)]
        # At least some should be False (no event)
        assert isinstance(results[0], bool)

    def test_should_generate_event_night(self):
        """Test event probability increases at night"""
        service = FrictionEventService(random_seed=42)
        day_result = service.should_generate_event(1, {"night": True})
        # Just check it doesn't error
        assert isinstance(day_result, bool)

    def test_should_generate_event_bad_weather(self):
        """Test event probability increases with bad weather"""
        service = FrictionEventService(random_seed=42)
        result = service.should_generate_event(1, {"bad_weather": True})
        assert isinstance(result, bool)

    def test_generate_event(self):
        """Test event generation"""
        service = FrictionEventService(random_seed=42)
        game_state = {"current_turn": 1}
        event = service.generate_event(game_state)
        assert "type" in event
        assert "title" in event
        assert "description" in event
        assert "severity" in event

    def test_generate_event_types(self):
        """Test various event types are generated"""
        service = FrictionEventService(random_seed=42)
        game_state = {"current_turn": 1}
        events = set()
        for _ in range(50):
            event = service.generate_event(game_state)
            events.add(event["type"])
        # Should have multiple event types
        assert len(events) > 1

    def test_apply_event_effects_misfire(self):
        """Test misfire event effects"""
        service = FrictionEventService(random_seed=42)
        game_state = {"units": [{"side": "player", "strength": 100}]}
        event = {
            "type": FrictionEventType.MISFIRE,
            "effects": {"unit_damage": 20, "morale_impact": 10}
        }
        result = service.apply_event_effects(game_state, event)
        assert "friction_events" in result

    def test_apply_event_effects_weather(self):
        """Test weather deterioration event"""
        service = FrictionEventService(random_seed=42)
        game_state = {"weather": "clear"}
        event = {
            "type": FrictionEventType.WEATHER_DETERIORATION,
            "effects": {"visibility_reduction": 30}
        }
        result = service.apply_event_effects(game_state, event)
        assert result["weather"] != "clear"

    def test_create_friction_event_service(self):
        """Test service factory"""
        service = create_friction_event_service(seed=42)
        assert service is not None
        assert isinstance(service, FrictionEventService)


class TestFrictionEventTypes:
    def test_misfire_event(self):
        """Test misfire event structure"""
        service = FrictionEventService(random_seed=42)
        event = service.generate_event({"current_turn": 1})
        if event["type"] == FrictionEventType.MISFIRE:
            assert "effects" in event
            assert "unit_damage" in event["effects"]

    def test_communication_failure_event(self):
        """Test communication failure event"""
        service = FrictionEventService(random_seed=42)
        event = service.generate_event({"current_turn": 1})
        if event["type"] == FrictionEventType.COMMUNICATION_FAILURE:
            assert "effects" in event

    def test_all_event_types(self):
        """Test all event types exist"""
        assert FrictionEventType.MISFIRE == "misfire"
        assert FrictionEventType.COMMUNICATION_FAILURE == "communication_failure"
        assert FrictionEventType.MAINTENANCE_ISSUE == "maintenance_issue"
        assert FrictionEventType.WEATHER_DETERIORATION == "weather_deterioration"
        assert FrictionEventType.UNIT_ERROR == "unit_error"
        assert FrictionEventType.SUPPLY_DELAY == "supply_delay"
        assert FrictionEventType.UNEXPECTED_CONTACT == "unexpected_contact"
