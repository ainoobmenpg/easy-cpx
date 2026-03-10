# Cycle Management Service
# Handles Planning/Air/Logistics cycle tracking for CPX

from datetime import datetime
from typing import Any
from app.models import CycleType, CyclePhase, CycleStatus


# Cycle duration in turns
CYCLE_DURATION_TURNS = {
    CycleType.PLANNING: 2,
    CycleType.AIR_TASKING: 3,
    CycleType.LOGISTICS: 4,
}

# Execution phase duration
EXECUTION_DURATION_TURNS = {
    CycleType.PLANNING: 1,
    CycleType.AIR_TASKING: 1,
    CycleType.LOGISTICS: 2,
}


def create_initial_cycle(cycle_type: CycleType, start_turn: int = 1) -> dict[str, Any]:
    """Create initial cycle state.

    Args:
        cycle_type: Type of cycle
        start_turn: Starting turn number

    Returns:
        Cycle state dict
    """
    duration = CYCLE_DURATION_TURNS.get(cycle_type, 2)
    # deadline is the last turn of the cycle (inclusive)
    return {
        "phase": CyclePhase.PLANNING.value,
        "deadline_turn": start_turn + duration,
        "status": CycleStatus.ON_TRACK.value,
        "last_updated": datetime.utcnow().isoformat(),
        "cycle_type": cycle_type.value,
    }


def advance_cycle(cycle_state: dict[str, Any], current_turn: int) -> dict[str, Any]:
    """Advance cycle to next state based on current turn.

    Args:
        cycle_state: Current cycle state
        current_turn: Current turn number

    Returns:
        Updated cycle state
    """
    if not cycle_state:
        return cycle_state

    phase = cycle_state.get("phase", CyclePhase.PLANNING.value)
    deadline = cycle_state.get("deadline_turn", current_turn)
    cycle_type = cycle_state.get("cycle_type", "planning")

    # Check if deadline passed
    if current_turn > deadline:
        # Move to next cycle
        return create_initial_cycle(CycleType(cycle_type), current_turn)

    # Check if planning phase should transition to execution
    if phase == CyclePhase.PLANNING.value:
        execution_duration = EXECUTION_DURATION_TURNS.get(CycleType(cycle_type), 1)
        execution_deadline = deadline - execution_duration + 1

        if current_turn >= execution_deadline:
            cycle_state["phase"] = CyclePhase.EXECUTION.value

    # Update status based on time remaining
    turns_remaining = deadline - current_turn
    if turns_remaining <= 0:
        cycle_state["status"] = CycleStatus.FAILED.value
    elif turns_remaining == 1:
        cycle_state["status"] = CycleStatus.DELAYED.value
    else:
        cycle_state["status"] = CycleStatus.ON_TRACK.value

    cycle_state["last_updated"] = datetime.utcnow().isoformat()
    return cycle_state


def get_cycle_penalty(cycle_state: dict[str, Any]) -> float:
    """Calculate adjudication penalty based on cycle status.

    Args:
        cycle_state: Current cycle state

    Returns:
        Penalty modifier (0.0 to 1.0, higher = worse)
    """
    if not cycle_state:
        return 0.0

    status = cycle_state.get("status", CycleStatus.ON_TRACK.value)

    # Adjudication v1.6 penalties
    if status == CycleStatus.FAILED.value:
        return 0.2  # 20% penalty
    elif status == CycleStatus.DELAYED.value:
        return 0.1  # 10% penalty

    return 0.0


def get_cycle_summary(cycles: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """Get summary of all cycles for UI display.

    Args:
        cycles: Dict of cycle_type -> cycle_state

    Returns:
        List of cycle summaries
    """
    summary = []
    for cycle_type, cycle_state in cycles.items():
        if cycle_state:
            summary.append({
                "type": cycle_type,
                "phase": cycle_state.get("phase"),
                "deadline_turn": cycle_state.get("deadline_turn"),
                "status": cycle_state.get("status"),
                "last_updated": cycle_state.get("last_updated"),
            })
    return summary


def initialize_game_cycles(start_turn: int = 1) -> dict[str, dict[str, Any]]:
    """Initialize all cycles for a new game.

    Args:
        start_turn: Starting turn number

    Returns:
        Dict of cycle_type -> cycle_state
    """
    return {
        "planning": create_initial_cycle(CycleType.PLANNING, start_turn),
        "air_tasking": create_initial_cycle(CycleType.AIR_TASKING, start_turn),
        "logistics": create_initial_cycle(CycleType.LOGISTICS, start_turn),
    }


def apply_cycle_penalties(
    cycles: dict[str, dict[str, Any]],
    base_modifier: float = 0.0
) -> float:
    """Apply all cycle penalties to base modifier.

    Args:
        cycles: Dict of cycle_type -> cycle_state
        base_modifier: Base modifier from other sources

    Returns:
        Total modifier with penalties applied
    """
    total_penalty = 0.0

    for cycle_state in cycles.values():
        if cycle_state:
            total_penalty += get_cycle_penalty(cycle_state)

    return base_modifier + total_penalty
