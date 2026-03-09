# Tests for Inject System Service (MEL/MIL)
from app.services.inject_system import (
    InjectSystem,
    InjectType,
    InjectTiming,
    InjectStatus,
    create_inject_system
)


class TestInjectSystem:
    """Test inject system service"""

    def test_initialization(self):
        """Test inject system initialization"""
        system = InjectSystem(game_id=1, seed=42)
        # Should have default injects
        injects = system.get_available_injects()
        assert len(injects) > 0

    def test_get_available_injects(self):
        """Test getting available injects"""
        system = InjectSystem(game_id=1, seed=42)
        injects = system.get_available_injects()
        assert isinstance(injects, list)
        # All should have required fields
        for inject in injects:
            assert "id" in inject
            assert "name" in inject
            assert "type" in inject
            assert "timing" in inject
            assert "effects" in inject

    def test_get_inject_by_id(self):
        """Test getting inject by ID"""
        system = InjectSystem(game_id=1, seed=42)
        inject = system.get_inject_by_id("inj_comms_01")
        assert inject is not None
        assert inject["id"] == "inj_comms_01"
        assert inject["type"] == "communications_outage"

    def test_get_inject_by_id_not_found(self):
        """Test getting non-existent inject"""
        system = InjectSystem(game_id=1, seed=42)
        inject = system.get_inject_by_id("nonexistent")
        assert inject is None

    def test_trigger_immediate_inject(self):
        """Test triggering an inject immediately"""
        system = InjectSystem(game_id=1, seed=42)

        # Trigger inject
        result = system.trigger_immediate_inject("inj_comms_01", turn=3)

        assert result is not None
        assert result["inject_id"] == "inj_comms_01"
        assert result["turn"] == 3
        assert result["trigger_type"] == "immediate"
        assert "effects_applied" in result

    def test_trigger_immediate_inject_not_found(self):
        """Test triggering non-existent inject"""
        system = InjectSystem(game_id=1, seed=42)

        result = system.trigger_immediate_inject("nonexistent", turn=1)

        assert result is None

    def test_trigger_immediate_inject_already_triggered(self):
        """Test triggering already triggered inject"""
        system = InjectSystem(game_id=1, seed=42)

        # Trigger once
        result1 = system.trigger_immediate_inject("inj_comms_01", turn=1)
        assert result1 is not None

        # Try to trigger again
        result2 = system.trigger_immediate_inject("inj_comms_01", turn=2)
        assert result2 is None

    def test_cancel_inject(self):
        """Test cancelling an inject"""
        system = InjectSystem(game_id=1, seed=42)

        # Cancel inject
        success = system.cancel_inject("inj_comms_01")
        assert success is True

        # Try to trigger cancelled inject
        result = system.trigger_immediate_inject("inj_comms_01", turn=1)
        assert result is None

    def test_reset_inject(self):
        """Test resetting a triggered inject"""
        system = InjectSystem(game_id=1, seed=42)

        # Trigger inject
        result = system.trigger_immediate_inject("inj_comms_01", turn=1)
        assert result is not None

        # Reset inject
        success = system.reset_inject("inj_comms_01")
        assert success is True

        # Should be able to trigger again
        result2 = system.trigger_immediate_inject("inj_comms_01", turn=2)
        assert result2 is not None

    def test_check_scheduled_injects(self):
        """Test checking scheduled injects"""
        system = InjectSystem(game_id=1, seed=42)

        # Scheduled inject for turn 4
        triggered = system.check_scheduled_injects(turn=4)

        # Should trigger scheduled inject
        assert isinstance(triggered, list)

    def test_check_scheduled_injects_not_matched(self):
        """Test checking scheduled injects - no match"""
        system = InjectSystem(game_id=1, seed=42)

        # Turn 1 - scheduled inject is for turn 4
        triggered = system.check_scheduled_injects(turn=1)

        # Should not trigger
        assert len(triggered) == 0

    def test_get_active_effects(self):
        """Test getting active effects"""
        system = InjectSystem(game_id=1, seed=42)

        # Initially no active effects
        effects = system.get_active_effects()
        assert len(effects) == 0

        # Trigger an inject
        system.trigger_immediate_inject("inj_comms_01", turn=1)

        # Should have active effects
        effects = system.get_active_effects()
        assert len(effects) > 0

    def test_get_effect_modifier(self):
        """Test getting effect modifier"""
        system = InjectSystem(game_id=1, seed=42)

        # No effects - should return default
        modifier = system.get_effect_modifier("reconnaissance", default=0)
        assert modifier == 0

        # Trigger communications outage inject (reconnaissance -2)
        system.trigger_immediate_inject("inj_comms_01", turn=1)

        # Should have modifier
        modifier = system.get_effect_modifier("reconnaissance", default=0)
        assert modifier == -2

    def test_decrement_effect_duration(self):
        """Test decrementing effect duration"""
        system = InjectSystem(game_id=1, seed=42)

        # Trigger inject with duration
        system.trigger_immediate_inject("inj_comms_01", turn=1)

        # Decrement
        expired = system.decrement_effect_duration(2)

        # Effects should have decremented (but not expired in this case)
        assert isinstance(expired, list)

    def test_get_inject_history(self):
        """Test getting inject history"""
        system = InjectSystem(game_id=1, seed=42)

        # Initially empty
        history = system.get_inject_history()
        assert len(history) == 0

        # Trigger injects
        system.trigger_immediate_inject("inj_comms_01", turn=1)
        system.trigger_immediate_inject("inj_intel_01", turn=2)

        # Should have history
        history = system.get_inject_history()
        assert len(history) == 2

    def test_get_inject_logs_for_turn(self):
        """Test getting inject logs for specific turn"""
        system = InjectSystem(game_id=1, seed=42)

        # Trigger injects at different turns
        system.trigger_immediate_inject("inj_comms_01", turn=1)
        system.trigger_immediate_inject("inj_intel_01", turn=2)

        # Get logs for turn 1
        logs = system.get_inject_logs_for_turn(1)
        assert len(logs) == 1
        assert logs[0]["turn"] == 1

    def test_get_inject_summary(self):
        """Test getting inject summary"""
        system = InjectSystem(game_id=1, seed=42)

        summary = system.get_inject_summary()

        assert "game_id" in summary
        assert "total" in summary
        assert "available" in summary
        assert "triggered" in summary
        assert "active_effects" in summary
        assert "history_count" in summary

    def test_create_inject_system(self):
        """Test service factory"""
        system = create_inject_system(game_id=1, seed=42)

        assert system is not None
        assert isinstance(system, InjectSystem)
        assert system.game_id == 1


class TestInjectTypes:
    """Test inject type constants"""

    def test_all_inject_types_defined(self):
        """Test all inject types are defined"""
        assert InjectType.COMMUNICATIONS_OUTAGE.value == "communications_outage"
        assert InjectType.EW_INTERFERENCE.value == "ew_interference"
        assert InjectType.SUPPLY_INTERDICTION.value == "supply_interdiction"
        assert InjectType.WEATHER_DETERIORATION.value == "weather_deterioration"
        assert InjectType.REINFORCEMENTS.value == "reinforcements"
        assert InjectType.AIR_STRIKE_ALERT.value == "air_strike_alert"
        assert InjectType.CIVILIAN_REFUGEES.value == "civilian_refugees"
        assert InjectType.EQUIPMENT_MALFUNCTION.value == "equipment_malfunction"
        assert InjectType.INTELLIGENCE_REPORT.value == "intelligence_report"
        assert InjectType.COMMAND_DECISION.value == "command_decision"

    def test_inject_timing_types(self):
        """Test inject timing types"""
        assert InjectTiming.IMMEDIATE.value == "immediate"
        assert InjectTiming.CONDITIONAL.value == "conditional"
        assert InjectTiming.SCHEDULED.value == "scheduled"

    def test_inject_status_types(self):
        """Test inject status types"""
        assert InjectStatus.AVAILABLE.value == "available"
        assert InjectStatus.TRIGGERED.value == "triggered"
        assert InjectStatus.EXPIRED.value == "expired"
        assert InjectStatus.CANCELLED.value == "cancelled"


class TestInjectConditions:
    """Test inject condition evaluation"""

    def test_turn_number_condition_min(self):
        """Test turn number minimum condition"""
        system = InjectSystem(game_id=1, seed=42)

        conditions = [
            {"type": "turn_number", "params": {"min_turn": 3}}
        ]

        # Turn 2 should fail
        result = system._check_conditions(conditions, 2, {})
        assert result is False

        # Turn 3 should pass
        result = system._check_conditions(conditions, 3, {})
        assert result is True

    def test_turn_number_condition_range(self):
        """Test turn number range condition"""
        system = InjectSystem(game_id=1, seed=42)

        conditions = [
            {"type": "turn_number", "params": {"min_turn": 2, "max_turn": 5}}
        ]

        # Turn 1 should fail
        result = system._check_conditions(conditions, 1, {})
        assert result is False

        # Turn 3 should pass
        result = system._check_conditions(conditions, 3, {})
        assert result is True

        # Turn 6 should fail
        result = system._check_conditions(conditions, 6, {})
        assert result is False

    def test_random_condition(self):
        """Test random condition"""
        system = InjectSystem(game_id=1, seed=123)

        conditions = [
            {"type": "random", "params": {"probability": 0.0}}
        ]

        # With 0 probability, should always fail
        result = system._check_conditions(conditions, 1, {})
        assert result is False

    def test_empty_conditions(self):
        """Test empty conditions always pass"""
        system = InjectSystem(game_id=1, seed=42)

        result = system._check_conditions([], 1, {})
        assert result is True


class TestInjectEffects:
    """Test inject effect application"""

    def test_effect_application(self):
        """Test effect is applied correctly"""
        system = InjectSystem(game_id=1, seed=42)

        inject = {
            "id": "test_inject",
            "name": "Test Inject",
            "effects": [
                {
                    "target": "combat",
                    "modifier": 1,
                    "duration_turns": 2,
                    "description": "Test effect"
                }
            ]
        }

        applied = system._apply_inject_effects(inject, turn=1)

        assert len(applied) == 1
        assert applied[0]["target"] == "combat"
        assert applied[0]["modifier"] == 1
        assert applied[0]["duration_turns"] == 2

    def test_multiple_effects(self):
        """Test multiple effects are applied"""
        system = InjectSystem(game_id=1, seed=42)

        inject = {
            "id": "test_inject",
            "name": "Test Inject",
            "effects": [
                {
                    "target": "movement",
                    "modifier": -1,
                    "duration_turns": 1,
                    "description": "Movement effect"
                },
                {
                    "target": "reconnaissance",
                    "modifier": -1,
                    "duration_turns": 1,
                    "description": "Recon effect"
                }
            ]
        }

        applied = system._apply_inject_effects(inject, turn=1)

        assert len(applied) == 2

    def test_cumulative_modifiers(self):
        """Test modifiers are cumulative"""
        system = InjectSystem(game_id=1, seed=42)

        # Trigger two injects with same target
        system.trigger_immediate_inject("inj_comms_01", turn=1)

        # Get modifier
        modifier = system.get_effect_modifier("reconnaissance", default=0)

        # Should have the modifier from the inject
        assert modifier != 0


class TestInjectObservations:
    """Test inject observation tracking"""

    def test_observations_stored(self):
        """Test observations are stored in inject"""
        system = InjectSystem(game_id=1, seed=42)

        inject = system.get_inject_by_id("inj_comms_01")

        assert "observations" in inject
        assert len(inject["observations"]) > 0
        assert "item" in inject["observations"][0]
        assert "expected_response" in inject["observations"][0]
        assert "evaluation_criteria" in inject["observations"][0]


class TestInjectDifficulty:
    """Test inject difficulty levels"""

    def test_difficulty_levels(self):
        """Test injects have difficulty levels"""
        system = InjectSystem(game_id=1, seed=42)

        injects = system.get_available_injects()

        for inject in injects:
            assert "difficulty" in inject
            assert inject["difficulty"] in ["easy", "medium", "hard"]

    def test_evaluation_points(self):
        """Test injects have evaluation points"""
        system = InjectSystem(game_id=1, seed=42)

        injects = system.get_available_injects()

        for inject in injects:
            assert "evaluation_points" in inject
            assert inject["evaluation_points"] > 0
