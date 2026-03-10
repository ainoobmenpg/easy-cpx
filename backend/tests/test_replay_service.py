# Tests for Replay Service
import pytest
from app.services.replay_service import ReplayService, ReplayEventType, ReplayState, create_replay_service


class TestReplayService:
    """Test cases for ReplayService"""

    def test_create_replay_service(self):
        """Test creating a new ReplayService instance"""
        service = create_replay_service(game_id=123)
        assert service.game_id == 123
        assert service._logs == []
        assert service._seed is None

    def test_load_from_logs_empty(self):
        """Test loading from empty log data"""
        service = ReplayService()
        result = service.load_from_logs([])
        assert result is False

    def test_load_from_logs_with_data(self):
        """Test loading from valid log data"""
        service = ReplayService()
        log_data = [
            {
                "event_type": "turn_start",
                "turn": 1,
                "time": "06:00",
                "weather": "clear",
                "seed": 12345
            },
            {
                "event_type": "combat",
                "turn": 1,
                "data": {
                    "attacker": "unit_1",
                    "defender": "unit_2",
                    "outcome": "success"
                }
            },
            {
                "event_type": "turn_end",
                "turn": 1
            }
        ]
        result = service.load_from_logs(log_data)
        assert result is True
        assert len(service._logs) == 3

    def test_get_event_timeline(self):
        """Test getting event timeline"""
        service = ReplayService()
        log_data = [
            {"event_type": "turn_start", "turn": 1, "time": "06:00", "weather": "clear"},
            {"event_type": "combat", "turn": 1, "data": {"attacker": "u1", "defender": "u2", "outcome": "success"}},
            {"event_type": "movement", "turn": 1, "data": {"unit_id": "u1", "from": [10, 10], "to": [12, 10]}},
            {"event_type": "turn_end", "turn": 1},
        ]
        service.load_from_logs(log_data)
        timeline = service.get_event_timeline()
        assert len(timeline) == 4

    def test_get_total_turns(self):
        """Test getting total turns"""
        service = ReplayService()
        log_data = [
            {"event_type": "turn_start", "turn": 1},
            {"event_type": "turn_end", "turn": 1},
            {"event_type": "turn_start", "turn": 2},
            {"event_type": "turn_end", "turn": 2},
            {"event_type": "turn_start", "turn": 3},
            {"event_type": "turn_end", "turn": 3},
        ]
        service.load_from_logs(log_data)
        assert service.get_total_turns() == 3

    def test_get_turn_summary(self):
        """Test getting turn summary"""
        service = ReplayService()
        log_data = [
            {"event_type": "turn_start", "turn": 1, "time": "06:00", "weather": "clear", "seed": 100},
            {"event_type": "combat", "turn": 1, "data": {"attacker": "u1", "defender": "u2"}},
            {"event_type": "movement", "turn": 1, "data": {"unit_id": "u1"}},
            {"event_type": "inject", "turn": 1, "data": {"type": "weather_change", "trigger": "random"}},
            {"event_type": "sitrep", "turn": 1, "data": {"summary": "Test SITREP"}},
            {"event_type": "turn_end", "turn": 1},
        ]
        service.load_from_logs(log_data)
        summary = service.get_turn_summary(1)
        assert summary is not None
        assert summary["turn"] == 1
        assert summary["combat_count"] == 1
        assert summary["movement_count"] == 1
        assert summary["inject_count"] == 1

    def test_get_state_at_turn(self):
        """Test getting state at specific turn"""
        service = ReplayService()
        log_data = [
            {"event_type": "turn_start", "turn": 1, "time": "06:00", "weather": "clear", "seed": 100},
            {"event_type": "turn_end", "turn": 1},
        ]
        service.load_from_logs(log_data)
        state = service.get_state_at_turn(1)
        assert state.turn_number == 1
        assert state.time == "06:00"
        assert state.weather == "clear"

    def test_seed_extraction(self):
        """Test seed extraction from logs"""
        service = ReplayService()
        log_data = [
            {"event_type": "turn_start", "turn": 1, "seed": 99999},
            {"event_type": "turn_end", "turn": 1},
        ]
        service.load_from_logs(log_data)
        assert service.seed == 99999

    def test_turn_seeds_tracking(self):
        """Test turn seeds are tracked correctly"""
        service = ReplayService()
        log_data = [
            {"event_type": "turn_start", "turn": 1, "seed": 100},
            {"event_type": "turn_end", "turn": 1},
            {"event_type": "turn_start", "turn": 2, "seed": 200},
            {"event_type": "turn_end", "turn": 2},
        ]
        service.load_from_logs(log_data)
        turn_seeds = service.get_turn_seeds()
        assert turn_seeds[1] == 100
        assert turn_seeds[2] == 200


class TestReplayEventType:
    """Test cases for ReplayEventType enum"""

    def test_event_types_defined(self):
        """Test all event types are defined"""
        assert ReplayEventType.TURN_START.value == "turn_start"
        assert ReplayEventType.TURN_END.value == "turn_end"
        assert ReplayEventType.MOVEMENT.value == "movement"
        assert ReplayEventType.COMBAT.value == "combat"
        assert ReplayEventType.INJECT.value == "inject"
        assert ReplayEventType.ADJUDICATION.value == "adjudication"
        assert ReplayEventType.SUPPLY.value == "supply"
        assert ReplayEventType.RECON.value == "recon"
        assert ReplayEventType.FRICTION.value == "friction"


class TestReplayState:
    """Test cases for ReplayState"""

    def test_default_state(self):
        """Test default ReplayState values"""
        state = ReplayState()
        assert state.turn_number == 0
        assert state.time == "05:40"
        assert state.weather == "clear"
        assert state.units == {}
        assert state.events == []
        assert state.sitrep is None
        assert state.seed == 0
        assert state.turn_seed == 0
