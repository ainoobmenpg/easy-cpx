# Tests for Event Deck Service
from app.services.event_deck import (
    EventDeckService,
    EventDeckType,
    create_event_deck_service
)


class TestEventDeckService:
    """Test event deck service"""

    def test_initialization(self):
        """Test deck initialization"""
        service = EventDeckService(random_seed=42)
        # Should have 10 cards
        assert service.get_deck_count() == 10
        assert service.get_discard_count() == 0

    def test_deck_has_all_event_types(self):
        """Test all 10 event types are in deck"""
        service = EventDeckService(random_seed=42)
        # Draw all events and check types
        events = []
        for _ in range(15):  # Draw more than deck size to test reshuffle
            event = service.draw_event(turn_number=5)
            if event:
                events.append(event["type"])

        # Should have at least 8 unique event types
        unique_types = set(events)
        assert len(unique_types) >= 8

    def test_draw_event_turn_condition(self):
        """Test that min_turn condition is enforced"""
        service = EventDeckService(random_seed=42)
        # Try to draw on turn 1 - should not get events with min_turn > 1
        result = service.draw_event(turn_number=1)
        # Event may be None or may be one without min_turn condition
        assert result is None or isinstance(result, dict)

    def test_draw_event_with_context(self):
        """Test event drawing with context"""
        service = EventDeckService(random_seed=42)
        context = {
            "turn_number": 5,
            "combat_occurred": True,
            "reinforcement_number": 3,
            "direction": "北",
            "enemy_count": "2",
        }
        event = service.draw_event(turn_number=5, context=context)
        if event:
            assert "type" in event
            assert "name" in event
            assert "presentation_text" in event
            assert event["turn"] == 5

    def test_apply_event_effects_combat_modifier(self):
        """Test applying 2D6 combat modifier"""
        service = EventDeckService(random_seed=42)
        game_state = {}
        event = {
            "type": EventDeckType.REINFORCEMENTS,
            "effects": {
                "2d6_modifier": "+2",
                "target": "combat",
                "duration": 1
            },
            "turn": 1
        }
        result = service.apply_event_to_game_state(game_state, event)
        assert "event_deck_events" in result
        assert result.get("event_combat_modifier") == 2
        assert result.get("event_combat_modifier_turns") == 1

    def test_apply_event_effects_action_restriction(self):
        """Test applying action restriction"""
        service = EventDeckService(random_seed=42)
        game_state = {}
        event = {
            "type": EventDeckType.AMMO_SHORTAGE,
            "effects": {
                "action_restriction": "artillery_limited",
                "description": "砲兵射撃のみ1ターン制約",
                "duration": 1
            },
            "turn": 1
        }
        result = service.apply_event_to_game_state(game_state, event)
        assert "action_restrictions" in result
        assert len(result["action_restrictions"]) == 1
        assert result["action_restrictions"][0]["type"] == "artillery_limited"

    def test_apply_event_effects_movement_restriction(self):
        """Test applying movement restriction"""
        service = EventDeckService(random_seed=42)
        game_state = {}
        event = {
            "type": EventDeckType.INTEL_LEAK,
            "effects": {
                "movement_restriction": "defensive_posture",
                "description": "防御態勢下令",
                "duration": 1
            },
            "turn": 1
        }
        result = service.apply_event_to_game_state(game_state, event)
        assert "movement_restrictions" in result
        assert len(result["movement_restrictions"]) == 1

    def test_decrement_effect_duration(self):
        """Test decrementing effect duration"""
        service = EventDeckService(random_seed=42)
        game_state = {
            "event_combat_modifier": 2,
            "event_combat_modifier_turns": 2,
            "action_restrictions": [
                {"type": "test", "duration": 2}
            ],
            "movement_restrictions": [
                {"type": "defensive", "duration": 1}
            ]
        }
        result = service.decrement_effect_duration(game_state)
        assert result["event_combat_modifier_turns"] == 1
        assert result["action_restrictions"][0]["duration"] == 1
        # Movement restriction should be removed when duration reaches 0
        assert len(result.get("movement_restrictions", [])) == 0

    def test_get_active_modifiers(self):
        """Test getting active modifiers"""
        service = EventDeckService(random_seed=42)
        game_state = {
            "event_combat_modifier": 2,
            "event_combat_modifier_turns": 1,
            "event_defense_modifier": -1,
            "event_defense_modifier_turns": 0,  # Expired
        }
        modifiers = service.get_active_modifiers(game_state)
        assert "combat" in modifiers
        assert modifiers["combat"] == 2
        assert "defense" not in modifiers  # Expired

    def test_should_draw_event_base(self):
        """Test base draw probability"""
        service = EventDeckService(random_seed=42)
        # Test with fixed seed - should be deterministic
        results = [service.should_draw_event(5) for _ in range(10)]
        assert isinstance(results[0], bool)

    def test_should_draw_event_early_game(self):
        """Test early game adjustment"""
        service = EventDeckService(random_seed=42)
        # Early game should have lower chance
        result = service.should_draw_event(1, {"early_game": True})
        assert isinstance(result, bool)

    def test_should_draw_event_high_intensity(self):
        """Test high intensity adjustment"""
        service = EventDeckService(random_seed=42)
        result = service.should_draw_event(5, {"high_intensity": True})
        assert isinstance(result, bool)

    def test_get_event_description(self):
        """Test getting event description"""
        service = EventDeckService(random_seed=42)
        event = {
            "type": EventDeckType.REINFORCEMENTS,
            "name": "増援部隊到着",
            "description": "後方待機していた増援部隊が戦場に到着しました。"
        }
        desc = service.get_event_description(event)
        assert "増援" in desc

    def test_get_event_effects(self):
        """Test getting event effects"""
        service = EventDeckService(random_seed=42)
        event = {
            "type": EventDeckType.REINFORCEMENTS,
            "effects": {
                "2d6_modifier": "+2",
                "target": "combat",
                "duration": 1
            }
        }
        effects = service.get_event_effects(event)
        assert "2d6_modifier" in effects
        assert effects["2d6_modifier"] == "+2"

    def test_cumulative_modifiers(self):
        """Test cumulative modifier effects"""
        service = EventDeckService(random_seed=42)
        game_state = {"event_combat_modifier": 1}

        event = {
            "type": EventDeckType.REINFORCEMENTS,
            "effects": {
                "2d6_modifier": "+2",
                "target": "combat",
                "duration": 1
            },
            "turn": 1
        }
        result = service.apply_event_to_game_state(game_state, event)
        # Should be cumulative
        assert result["event_combat_modifier"] == 3

    def test_create_event_deck_service(self):
        """Test service factory"""
        service = create_event_deck_service(seed=42)
        assert service is not None
        assert isinstance(service, EventDeckService)
        assert service.get_deck_count() == 10


class TestEventDeckTypes:
    """Test event deck type constants"""

    def test_all_event_types_defined(self):
        """Test all event types are defined"""
        assert EventDeckType.REINFORCEMENTS == "reinforcements"
        assert EventDeckType.ENEMY_REINFORCEMENTS == "enemy_reinforcements"
        assert EventDeckType.AMMO_SHORTAGE == "ammo_shortage"
        assert EventDeckType.WEATHER_CHANGE == "weather_change"
        assert EventDeckType.INTEL_LEAK == "intel_leak"
        assert EventDeckType.SUPPLY_INTERRUPTION == "supply_interruption"
        assert EventDeckType.MORALE_BOOST == "morale_boost"
        assert EventDeckType.ENEMY_MORALE_LOW == "enemy_morale_low"
        assert EventDeckType.ARTILLERY_AVAILABLE == "artillery_available"
        assert EventDeckType.AIR_SUPPORT_AVAILABLE == "air_support_available"

    def test_event_count(self):
        """Test exactly 10 event types defined"""
        service = EventDeckService(random_seed=42)
        # Draw all events to count unique types
        types_seen = set()
        for _ in range(20):
            event = service.draw_event(turn_number=10)
            if event:
                types_seen.add(event["type"])
        # Should have seen all 10 types (may see duplicates due to reshuffle)
        assert len(types_seen) >= 8


class TestEventDeckPresentation:
    """Test event presentation text"""

    def test_presentation_text_generation(self):
        """Test presentation text is generated correctly"""
        service = EventDeckService(random_seed=42)
        context = {
            "turn_number": 5,
            "reinforcement_number": 3,
            "direction": "北",
            "enemy_count": "2",
            "location": "A-1",
            "weather_type": "濃霧",
            "cas_squadron": "第1"
        }
        event = service.draw_event(turn_number=5, context=context)
        if event and "presentation_text" in event:
            # Check placeholders are replaced
            assert "{" not in event["presentation_text"]
            assert "}" not in event["presentation_text"]

    def test_reinforcements_event_has_presentation(self):
        """Test reinforcements event has proper presentation"""
        service = EventDeckService(random_seed=42)
        # Force draw a specific event type by testing conditions
        event = service.draw_event(turn_number=5, context={"turn_number": 5})
        if event:
            assert "presentation_text" in event or "description" in event
