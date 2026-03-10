# Test for CPX-CYCLES cycle management

import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.cycle_manager import (
    create_initial_cycle,
    advance_cycle,
    get_cycle_penalty,
    get_cycle_summary,
    initialize_game_cycles,
    apply_cycle_penalties,
    CYCLE_DURATION_TURNS,
    EXECUTION_DURATION_TURNS,
)
from app.models import CycleType, CyclePhase, CycleStatus


class TestCycleManager:
    """Test cycle management functions"""

    def test_create_initial_cycle_planning(self):
        """Test creating initial planning cycle"""
        cycle = create_initial_cycle(CycleType.PLANNING, 1)

        assert cycle["phase"] == CyclePhase.PLANNING.value
        assert cycle["deadline_turn"] == 3  # 1 + 2 (duration)
        assert cycle["status"] == CycleStatus.ON_TRACK.value
        assert cycle["cycle_type"] == "planning"
        assert "last_updated" in cycle

    def test_create_initial_cycle_air_tasking(self):
        """Test creating initial air tasking cycle"""
        cycle = create_initial_cycle(CycleType.AIR_TASKING, 1)

        assert cycle["phase"] == CyclePhase.PLANNING.value
        assert cycle["deadline_turn"] == 4  # 1 + 3 (duration)
        assert cycle["status"] == CycleStatus.ON_TRACK.value

    def test_create_initial_cycle_logistics(self):
        """Test creating initial logistics cycle"""
        cycle = create_initial_cycle(CycleType.LOGISTICS, 1)

        assert cycle["phase"] == CyclePhase.PLANNING.value
        assert cycle["deadline_turn"] == 5  # 1 + 4 (duration)
        assert cycle["status"] == CycleStatus.ON_TRACK.value

    def test_advance_cycle_planning_phase(self):
        """Test advancing cycle in planning phase"""
        cycle = create_initial_cycle(CycleType.PLANNING, 1)

        # Turn 1: Should still be planning
        advanced = advance_cycle(cycle, 1)
        assert advanced["phase"] == CyclePhase.PLANNING.value
        assert advanced["status"] == CycleStatus.ON_TRACK.value

    def test_advance_cycle_to_execution(self):
        """Test transitioning from planning to execution"""
        cycle = create_initial_cycle(CycleType.PLANNING, 1)
        # deadline is now 3 (start=1, duration=2)

        # Turn 3: Should transition to execution (last turn of planning)
        advanced = advance_cycle(cycle, 3)
        assert advanced["phase"] == CyclePhase.EXECUTION.value

    def test_advance_cycle_delayed_status(self):
        """Test cycle status becomes delayed"""
        cycle = create_initial_cycle(CycleType.PLANNING, 1)

        # Turn 2: Should be delayed (one turn left before deadline 3)
        advanced = advance_cycle(cycle, 2)
        assert advanced["status"] == CycleStatus.DELAYED.value

    def test_advance_cycle_failed_status(self):
        """Test cycle status becomes failed and new cycle is created"""
        cycle = create_initial_cycle(CycleType.PLANNING, 1)

        # Turn 5 (past deadline 3): Should create new cycle
        advanced = advance_cycle(cycle, 5)
        # New cycle should start at turn 5
        assert advanced["phase"] == CyclePhase.PLANNING.value
        assert advanced["deadline_turn"] == 7  # New cycle: 5 + 2

    def test_get_cycle_penalty_on_track(self):
        """Test no penalty when cycle is on track"""
        cycle = {"phase": "planning", "status": CycleStatus.ON_TRACK.value}
        penalty = get_cycle_penalty(cycle)

        assert penalty == 0.0

    def test_get_cycle_penalty_delayed(self):
        """Test 10% penalty when cycle is delayed"""
        cycle = {"phase": "planning", "status": CycleStatus.DELAYED.value}
        penalty = get_cycle_penalty(cycle)

        assert penalty == 0.1

    def test_get_cycle_penalty_failed(self):
        """Test 20% penalty when cycle is failed"""
        cycle = {"phase": "execution", "status": CycleStatus.FAILED.value}
        penalty = get_cycle_penalty(cycle)

        assert penalty == 0.2

    def test_get_cycle_penalty_none(self):
        """Test no penalty for None cycle"""
        penalty = get_cycle_penalty(None)

        assert penalty == 0.0

    def test_apply_cycle_penalties_single(self):
        """Test applying single cycle penalty"""
        cycles = {
            "planning": {"phase": "planning", "status": CycleStatus.ON_TRACK.value},
        }

        total = apply_cycle_penalties(cycles, 0.0)
        assert total == 0.0

    def test_apply_cycle_penalties_multiple_delayed(self):
        """Test applying multiple delayed cycles"""
        cycles = {
            "planning": {"phase": "planning", "status": CycleStatus.DELAYED.value},
            "air_tasking": {"phase": "execution", "status": CycleStatus.DELAYED.value},
            "logistics": {"phase": "planning", "status": CycleStatus.ON_TRACK.value},
        }

        total = apply_cycle_penalties(cycles, 0.0)
        assert total == 0.2  # 0.1 + 0.1 + 0.0

    def test_apply_cycle_penalties_with_failed(self):
        """Test applying failed cycle penalty"""
        cycles = {
            "planning": {"phase": "planning", "status": CycleStatus.FAILED.value},
            "air_tasking": {"phase": "planning", "status": CycleStatus.ON_TRACK.value},
            "logistics": {"phase": "planning", "status": CycleStatus.ON_TRACK.value},
        }

        total = apply_cycle_penalties(cycles, 0.0)
        assert total == 0.2  # 0.2 + 0.0 + 0.0

    def test_get_cycle_summary(self):
        """Test getting cycle summary"""
        cycles = {
            "planning": {"phase": "planning", "deadline_turn": 2, "status": "on_track", "last_updated": "2026-03-06T05:40:00"},
            "air_tasking": {"phase": "execution", "deadline_turn": 3, "status": "delayed", "last_updated": "2026-03-06T05:40:00"},
            "logistics": None,
        }

        summary = get_cycle_summary(cycles)

        assert len(summary) == 2
        assert summary[0]["type"] == "planning"
        assert summary[1]["type"] == "air_tasking"
        assert summary[1]["status"] == "delayed"

    def test_initialize_game_cycles(self):
        """Test initializing all cycles for a game"""
        cycles = initialize_game_cycles(1)

        assert "planning" in cycles
        assert "air_tasking" in cycles
        assert "logistics" in cycles

        assert cycles["planning"]["phase"] == CyclePhase.PLANNING.value
        assert cycles["air_tasking"]["phase"] == CyclePhase.PLANNING.value
        assert cycles["logistics"]["phase"] == CyclePhase.PLANNING.value

        # deadline = start + duration (planning=2, air_tasking=3, logistics=4)
        assert cycles["planning"]["deadline_turn"] == 3
        assert cycles["air_tasking"]["deadline_turn"] == 4
        assert cycles["logistics"]["deadline_turn"] == 5

    def test_initialize_game_cycles_custom_start(self):
        """Test initializing cycles with custom start turn"""
        cycles = initialize_game_cycles(5)

        assert cycles["planning"]["deadline_turn"] == 7
        assert cycles["air_tasking"]["deadline_turn"] == 8
        assert cycles["logistics"]["deadline_turn"] == 9


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
