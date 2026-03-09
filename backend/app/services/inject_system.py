# Inject System Service
# MEL/MIL (Master Events List / Inject List) management for Operational CPX
# Provides training event injection with conditions, effects, and audit logging

import logging
import random
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

logger = logging.getLogger("cpx.inject")


class InjectType(Enum):
    """Inject type categories"""
    COMMUNICATIONS_OUTAGE = "communications_outage"
    EW_INTERFERENCE = "ew_interference"
    SUPPLY_INTERDICTION = "supply_interdiction"
    WEATHER_DETERIORATION = "weather_deterioration"
    REINFORCEMENTS = "reinforcements"
    AIR_STRIKE_ALERT = "air_strike_alert"
    CIVILIAN_REFUGEES = "civilian_refugees"
    EQUIPMENT_MALFUNCTION = "equipment_malfunction"
    INTELLIGENCE_REPORT = "intelligence_report"
    COMMAND_DECISION = "command_decision"


class InjectTiming(Enum):
    """When inject triggers"""
    IMMEDIATE = "immediate"
    CONDITIONAL = "conditional"
    SCHEDULED = "scheduled"


class InjectStatus(Enum):
    """Inject status"""
    AVAILABLE = "available"
    TRIGGERED = "triggered"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


# Default inject templates for training scenarios
DEFAULT_INJECTS = [
    {
        "id": "inj_comms_01",
        "name": "通信障害発生",
        "description": "電子戦により、味方通信網に障害が発生した。",
        "type": InjectType.COMMUNICATIONS_OUTAGE.value,
        "timing": InjectTiming.IMMEDIATE.value,
        "effects": [
            {
                "target": "reconnaissance",
                "modifier": -2,
                "duration_turns": 2,
                "description": "偵察値-2、2ターン継続"
            }
        ],
        "observations": [
            {
                "item": "unit_response",
                "expected_response": "代替通信手段への切り替え",
                "evaluation_criteria": "全ユニットが2ターン以内に通信復帰"
            }
        ],
        "evaluation_points": 10,
        "difficulty": "medium"
    },
    {
        "id": "inj_ew_01",
        "name": "EW干涉",
        "description": "敵電子戦機により、GPSと通信が干扰された。",
        "type": InjectType.EW_INTERFERENCE.value,
        "timing": InjectTiming.CONDITIONAL.value,
        "conditions": [
            {
                "type": "turn_number",
                "params": {"min_turn": 3}
            }
        ],
        "effects": [
            {
                "target": "movement",
                "modifier": -1,
                "duration_turns": 1,
                "description": "機動修正-1"
            },
            {
                "target": "reconnaissance",
                "modifier": -1,
                "duration_turns": 1,
                "description": "偵察値-1"
            }
        ],
        "observations": [
            {
                "item": "position_change",
                "expected_response": "敵EW機への対抗措施",
                "evaluation_criteria": "味方が対EW態勢を構築"
            }
        ],
        "evaluation_points": 15,
        "difficulty": "hard"
    },
    {
        "id": "inj_supply_01",
        "name": "補給線遮断",
        "description": "敵の機動により、主要补给線が遮断された。",
        "type": InjectType.SUPPLY_INTERDICTION.value,
        "timing": InjectTiming.CONDITIONAL.value,
        "conditions": [
            {
                "type": "unit_position",
                "params": {"zone": "forward", "min_units": 3}
            }
        ],
        "effects": [
            {
                "target": "supply",
                "modifier": -2,
                "duration_turns": 3,
                "description": "補給効率-50%、3ターン"
            }
        ],
        "observations": [
            {
                "item": "supply_request",
                "expected_response": "代替補給ルートの確保",
                "evaluation_criteria": "2ターン以内に補給再開"
            }
        ],
        "evaluation_points": 20,
        "difficulty": "hard"
    },
    {
        "id": "inj_weather_01",
        "name": "天候悪化",
        "description": "暴雨により、視界と機動が制限される。",
        "type": InjectType.WEATHER_DETERIORATION.value,
        "timing": InjectTiming.SCHEDULED.value,
        "conditions": [
            {
                "type": "turn_number",
                "params": {"min_turn": 2}
            }
        ],
        "effects": [
            {
                "target": "movement",
                "modifier": -1,
                "duration_turns": 2,
                "description": "機動修正-1、2ターン"
            },
            {
                "target": "reconnaissance",
                "modifier": -2,
                "duration_turns": 2,
                "description": "偵察値-2、2ターン"
            }
        ],
        "observations": [
            {
                "item": "terrain_adaptation",
                "expected_response": "天候に適した戦術への移行",
                "evaluation_criteria": "被害を最小限に抑えて行動"
            }
        ],
        "evaluation_points": 10,
        "difficulty": "easy"
    },
    {
        "id": "inj_reinf_01",
        "name": "増援到着",
        "description": "後方待機部队が戦場に到着した。",
        "type": InjectType.REINFORCEMENTS.value,
        "timing": InjectTiming.SCHEDULED.value,
        "conditions": [
            {
                "type": "turn_number",
                "params": {"turn": 4}
            }
        ],
        "effects": [
            {
                "target": "combat",
                "modifier": 1,
                "duration_turns": 1,
                "description": "戦闘修正+1"
            }
        ],
        "observations": [
            {
                "item": "integration",
                "expected_response": "増援の戦線への編入",
                "evaluation_criteria": "増援を効果的に活用"
            }
        ],
        "evaluation_points": 5,
        "difficulty": "easy"
    },
    {
        "id": "inj_intel_01",
        "name": "敵情報報告",
        "description": "偵察により、新たな敵情報が入手された。",
        "type": InjectType.INTELLIGENCE_REPORT.value,
        "timing": InjectTiming.IMMEDIATE.value,
        "effects": [
            {
                "target": "reconnaissance",
                "modifier": 2,
                "duration_turns": 1,
                "description": "偵察値+2（情報活用時）"
            }
        ],
        "observations": [
            {
                "item": "information_usage",
                "expected_response": "入手情報の戦術活用",
                "evaluation_criteria": "情報を元に有利な行動"
            }
        ],
        "evaluation_points": 10,
        "difficulty": "medium"
    }
]


class InjectSystem:
    """
    MEL/MIL System for training event injection

    Manages injects, conditions, effects, and audit logging.
    Provides white cell (EXCON) with ability to trigger events
    for training purposes.
    """

    def __init__(self, game_id: int, seed: Optional[int] = None):
        self.game_id = game_id
        self._random = random.Random(seed)
        self._available_injects: Dict[str, Dict[str, Any]] = {}
        self._active_effects: List[Dict[str, Any]] = []
        self._inject_history: List[Dict[str, Any]] = []
        self._initialize_injects()

    def _initialize_injects(self) -> None:
        """Initialize injects from default templates"""
        for inject in DEFAULT_INJECTS:
            self._available_injects[inject["id"]] = inject.copy()
            self._available_injects[inject["id"]]["status"] = InjectStatus.AVAILABLE.value

    def get_available_injects(self) -> List[Dict[str, Any]]:
        """Get list of available injects"""
        return [
            {k: v for k, v in inj.items() if k != "status"}
            for inj in self._available_injects.values()
            if inj.get("status") == InjectStatus.AVAILABLE.value
        ]

    def get_inject_by_id(self, inject_id: str) -> Optional[Dict[str, Any]]:
        """Get inject by ID"""
        return self._available_injects.get(inject_id)

    def trigger_immediate_inject(
        self,
        inject_id: str,
        turn: int,
        game_state: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Trigger an inject immediately"""
        inject = self._available_injects.get(inject_id)
        if not inject:
            logger.warning(f"Inject {inject_id} not found")
            return None

        if inject.get("status") != InjectStatus.AVAILABLE.value:
            logger.warning(f"Inject {inject_id} is not available (status: {inject.get('status')})")
            return None

        # Apply effects
        effects_applied = self._apply_inject_effects(inject, turn)

        # Create log entry
        log_entry = {
            "inject_id": inject_id,
            "inject_name": inject.get("name"),
            "game_id": self.game_id,
            "turn": turn,
            "timestamp": datetime.utcnow().isoformat(),
            "trigger_type": "immediate",
            "effects_applied": effects_applied,
            "results": {
                "status": "success",
                "message": f"Inject {inject.get('name')} triggered successfully"
            }
        }

        self._inject_history.append(log_entry)

        # Update inject status
        inject["status"] = InjectStatus.TRIGGERED.value
        inject["triggered_turn"] = turn

        logger.info(f"Inject {inject_id} triggered at turn {turn}")

        return log_entry

    def check_conditional_injects(
        self,
        turn: int,
        game_state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Check and trigger conditional injects"""
        triggered = []

        for inject_id, inject in self._available_injects.items():
            if inject.get("timing") != InjectTiming.CONDITIONAL.value:
                continue
            if inject.get("status") != InjectStatus.AVAILABLE.value:
                continue

            # Check conditions
            if self._check_conditions(inject.get("conditions", []), turn, game_state):
                log_entry = self.trigger_immediate_inject(inject_id, turn, game_state)
                if log_entry:
                    triggered.append(log_entry)

        return triggered

    def check_scheduled_injects(
        self,
        turn: int,
        game_state: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Check and trigger scheduled injects"""
        triggered = []

        for inject_id, inject in self._available_injects.items():
            if inject.get("timing") != InjectTiming.SCHEDULED.value:
                continue
            if inject.get("status") != InjectStatus.AVAILABLE.value:
                continue

            # Check if scheduled turn matches
            conditions = inject.get("conditions", [])
            for cond in conditions:
                if cond.get("type") == "turn_number":
                    scheduled_turn = cond.get("params", {}).get("turn")
                    if scheduled_turn == turn:
                        log_entry = self.trigger_immediate_inject(inject_id, turn, game_state)
                        if log_entry:
                            triggered.append(log_entry)

        return triggered

    def _check_conditions(
        self,
        conditions: List[Dict[str, Any]],
        turn: int,
        game_state: Dict[str, Any]
    ) -> bool:
        """Check if inject conditions are met"""
        if not conditions:
            return True

        for cond in conditions:
            cond_type = cond.get("type")
            params = cond.get("params", {})

            if cond_type == "turn_number":
                min_turn = params.get("min_turn", 1)
                max_turn = params.get("max_turn", 999)
                if turn < min_turn or turn > max_turn:
                    return False

            elif cond_type == "unit_position":
                # Check unit positions
                zone = params.get("zone")
                min_units = params.get("min_units", 1)
                if zone == "forward":
                    # Check how many units are in forward area
                    forward_count = self._count_forward_units(game_state)
                    if forward_count < min_units:
                        return False

            elif cond_type == "unit_status":
                # Check unit status conditions
                pass  # Placeholder for more complex checks

            elif cond_type == "random":
                probability = params.get("probability", 0.5)
                if self._random.random() > probability:
                    return False

            elif cond_type == "game_state":
                # Check game state conditions
                key = params.get("key")
                expected_value = params.get("value")
                if game_state.get(key) != expected_value:
                    return False

        return True

    def _count_forward_units(self, game_state: Dict[str, Any]) -> int:
        """Count units in forward area"""
        units = game_state.get("units", [])
        forward_threshold = game_state.get("map_height", 30) * 0.6

        count = 0
        for unit in units:
            if unit.get("side") == "player" and unit.get("y", 0) > forward_threshold:
                count += 1

        return count

    def _apply_inject_effects(
        self,
        inject: Dict[str, Any],
        turn: int
    ) -> List[Dict[str, Any]]:
        """Apply inject effects to game state"""
        effects = inject.get("effects", [])
        applied = []

        for effect in effects:
            active_effect = {
                "inject_id": inject.get("id"),
                "inject_name": inject.get("name"),
                "target": effect.get("target"),
                "modifier": effect.get("modifier"),
                "duration_turns": effect.get("duration_turns", 1),
                "description": effect.get("description"),
                "applied_turn": turn,
                "remaining_turns": effect.get("duration_turns", 1)
            }
            self._active_effects.append(active_effect)
            applied.append(active_effect)

        return applied

    def get_active_effects(self) -> List[Dict[str, Any]]:
        """Get currently active effects"""
        return [
            {k: v for k, v in effect.items() if k != "remaining_turns"}
            for effect in self._active_effects
        ]

    def get_effect_modifier(
        self,
        target: str,
        default: int = 0
    ) -> int:
        """Get modifier for a specific target"""
        total = default
        for effect in self._active_effects:
            if effect.get("target") == target:
                total += effect.get("modifier", 0)
        return total

    def decrement_effect_duration(self, new_turn: int) -> List[Dict[str, Any]]:
        """Decrement effect durations at turn end"""
        expired = []

        for effect in self._active_effects:
            effect["remaining_turns"] -= 1
            if effect["remaining_turns"] <= 0:
                expired.append(effect)

        # Remove expired effects
        self._active_effects = [
            e for e in self._active_effects
            if e.get("remaining_turns", 0) > 0
        ]

        return expired

    def get_inject_history(self) -> List[Dict[str, Any]]:
        """Get inject trigger history"""
        return self._inject_history.copy()

    def get_inject_logs_for_turn(self, turn: int) -> List[Dict[str, Any]]:
        """Get inject logs for specific turn"""
        return [
            log for log in self._inject_history
            if log.get("turn") == turn
        ]

    def cancel_inject(self, inject_id: str) -> bool:
        """Cancel an available inject"""
        inject = self._available_injects.get(inject_id)
        if not inject:
            return False

        if inject.get("status") == InjectStatus.AVAILABLE.value:
            inject["status"] = InjectStatus.CANCELLED.value
            return True

        return False

    def reset_inject(self, inject_id: str) -> bool:
        """Reset a triggered inject to available"""
        inject = self._available_injects.get(inject_id)
        if not inject:
            return False

        inject["status"] = InjectStatus.AVAILABLE.value
        inject.pop("triggered_turn", None)
        return True

    def get_inject_summary(self) -> Dict[str, Any]:
        """Get summary of all injects"""
        return {
            "game_id": self.game_id,
            "total": len(self._available_injects),
            "available": sum(1 for i in self._available_injects.values() if i.get("status") == InjectStatus.AVAILABLE.value),
            "triggered": sum(1 for i in self._available_injects.values() if i.get("status") == InjectStatus.TRIGGERED.value),
            "active_effects": len(self._active_effects),
            "history_count": len(self._inject_history)
        }


# Service instance factory
def create_inject_system(game_id: int, seed: Optional[int] = None) -> InjectSystem:
    """Create an inject system instance"""
    return InjectSystem(game_id, seed)
