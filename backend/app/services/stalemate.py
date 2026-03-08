# Stalemate Detection and Resolution for Operational CPX
# Implements stalemate rules when there's no significant action for multiple turns
from enum import Enum
from dataclasses import dataclass
from typing import Optional
import random


class StalemateType(Enum):
    """Types of stalemate situations"""
    TACTICAL = "tactical"       # Neither side can advance
    LOGISTICAL = "logistical"   # Both sides out of supplies
    MUTUAL_PARALYSIS = "mutual_paralysis"  # Neither side can move
    COMMAND_STALEMATE = "command_stalemate"  # No clear objective


@dataclass
class StalemateEvent:
    """An event caused by stalemate conditions"""
    event_id: int
    stalemate_type: StalemateType
    turn: int
    description: str
    response_required: bool = False
    resolved: bool = False


class StalemateSystem:
    """
    Detects and resolves stalemate conditions

    When there's no significant action for multiple turns:
    - Enemy aggressive action
    - Commander pressure
    - External events
    """

    # Thresholds for stalemate detection
    INACTIVE_TURN_THRESHOLD = 2  # Turns without significant action
    MOVEMENT_THRESHOLD = 2.0     # Units moved less than this = inactive

    def __init__(self, seed: Optional[int] = None):
        self._random = random.Random(seed)
        self._inactive_turns = 0
        self._last_combat_turn = 0
        self._last_movement_turn = 0
        self._last_objective_change_turn = 0
        self._current_stalemate: Optional[StalemateType] = None
        self._stalemate_events: list[StalemateEvent] = []
        self._event_counter = 0
        self._stalemate_intensity = 0  # 0-10

    def record_combat(self, turn: int):
        """Record that combat occurred"""
        self._last_combat_turn = turn
        self._inactive_turns = 0

    def record_movement(self, turn: int):
        """Record that significant movement occurred"""
        self._last_movement_turn = turn
        self._inactive_turns = 0

    def record_objective_change(self, turn: int):
        """Record that objectives changed"""
        self._last_objective_change_turn = turn
        self._inactive_turns = 0

    def check_stalemate(self, current_turn: int) -> Optional[StalemateType]:
        """
        Check if game is in stalemate

        Returns:
            StalemateType if stalemate detected, None otherwise
        """
        # Calculate turns since last significant action
        turns_since_combat = current_turn - self._last_combat_turn
        turns_since_movement = current_turn - self._last_movement_turn
        turns_since_objective = current_turn - self._last_objective_change_turn

        # Check if in inactive state
        if (turns_since_combat >= self.INACTIVE_TURN_THRESHOLD and
            turns_since_movement >= self.INACTIVE_TURN_THRESHOLD):
            self._inactive_turns += 1

            # Determine stalemate type
            if turns_since_objective >= self.INACTIVE_TURN_THRESHOLD * 2:
                self._current_stalemate = StalemateType.COMMAND_STALEMATE
            elif turns_since_combat >= self.INACTIVE_TURN_THRESHOLD * 2:
                self._current_stalemate = StalemateType.MUTUAL_PARALYSIS
            else:
                self._current_stalemate = StalemateType.TACTICAL

            self._stalemate_intensity = min(10, self._inactive_turns)
            return self._current_stalemate

        self._current_stalemate = None
        self._stalemate_intensity = 0
        return None

    def get_stalemate_event(
        self,
        current_turn: int,
        game_state: dict
    ) -> Optional[StalemateEvent]:
        """
        Generate a stalemate event to break the situation

        Returns:
            StalemateEvent if event should occur, None otherwise
        """
        if self._current_stalemate is None:
            return None

        self._event_counter += 1

        # Select event type based on stalemate type and intensity
        event_type = self._select_event_type()

        event = StalemateEvent(
            event_id=self._event_counter,
            stalemate_type=self._current_stalemate,
            turn=current_turn,
            description=event_type,
            response_required=True
        )

        self._stalemate_events.append(event)
        return event

    def _select_event_type(self) -> str:
        """Select a specific event type to break stalemate"""
        events = []

        if self._current_stalemate == StalemateType.TACTICAL:
            events = [
                "敵主力部队の側面攻撃を開始",
                "炮兵火力集中による攻撃準備",
                "偵察部队の前方展開",
                "側面迂回を開始",
                "偽退却による誘き出し"
            ]
        elif self._current_stalemate == StalemateType.LOGISTICAL:
            events = [
                "補給船団が接近中",
                "敵補給線を遮断する机会",
                "弾薬不足による戦力低下",
                "就地調達を開始"
            ]
        elif self._current_stalemate == StalemateType.MUTUAL_PARALYSIS:
            events = [
                "夜間戦闘開始",
                "奇襲攻撃を準備中",
                "敵の意図が不明",
                "上官から早期決着を要求"
            ]
        else:  # COMMAND_STALEMATE
            events = [
                "上官から新しい任務目標が発令",
                "戦況評価のため報告要求",
                "新たな脅威の出現",
                "戦術的機会の発生"
            ]

        # Add pressure events based on intensity
        if self._stalemate_intensity >= 5:
            events.append("上官の忍耐が限界に接近")
        if self._stalemate_intensity >= 8:
            events.append("指揮官更迭の噂")

        return self._random.choice(events)

    def apply_commander_pressure(
        self,
        stalemate_intensity: int
    ) -> tuple[str, int]:
        """
        Generate commander pressure based on stalemate

        Returns:
            (pressure_message, distrust_increase)
        """
        messages = []

        if stalemate_intensity >= 8:
            messages = [
                "状況は一向に进展しません。貴官の指揮能力に疑問を呈します。",
                "上官からの圧力が強まっています。尽快な行動を求む。"
            ]
            return self._random.choice(messages), 15
        elif stalemate_intensity >= 5:
            messages = [
                "戦況の打開を求む。",
                "これ以上の遅延は許されない。",
                "報告では进展が見られない。"
            ]
            return self._random.choice(messages), 8
        else:
            messages = [
                "任務の進捗情况は？",
                "敌の意図は把握したか？"
            ]
            return self._random.choice(messages), 3

    def apply_external_event(
        self,
        game_state: dict
    ) -> Optional[dict]:
        """
        Apply external event to break stalemate

        Returns:
            Event dict if event occurs, None otherwise
        """
        if self._current_stalemate is None or self._stalemate_intensity < 6:
            return None

        events = [
            {
                "type": "reinforcements",
                "description": "敵の増援部队が接近中",
                "effect": "enemy_strength_increase"
            },
            {
                "type": "weather_change",
                "description": "天候が急激に悪化",
                "effect": "visibility_reduced"
            },
            {
                "type": "supply_crisis",
                "description": "味方補給線が途絶危机",
                "effect": "logistics_pressure"
            },
            {
                "type": "intelligence",
                "description": "新たな敵情報が舞い込んだ",
                "effect": "new_objective"
            }
        ]

        return self._random.choice(events)

    def resolve_stalemate(self):
        """Mark stalemate as resolved"""
        self._current_stalemate = None
        self._inactive_turns = 0
        self._stalemate_intensity = 0

    def get_stalemate_status(self) -> dict:
        """Get current stalemate status"""
        return {
            "is_stalemate": self._current_stalemate is not None,
            "stalemate_type": self._current_stalemate.value if self._current_stalemate else None,
            "intensity": self._stalemate_intensity,
            "inactive_turns": self._inactive_turns,
            "events": [
                {
                    "id": e.event_id,
                    "description": e.description,
                    "resolved": e.resolved
                }
                for e in self._stalemate_events[-5:]
            ]
        }

    def get_stalemate_description(self) -> str:
        """Get human-readable stalemate description"""
        if self._current_stalemate is None:
            return "膠着状態ではない"

        descriptions = {
            StalemateType.TACTICAL: "戦術的膠着 - 両軍が進撃できない状態",
            StalemateType.LOGISTICAL: "補給膠着 - 両軍とも補給が尽きた状態",
            StalemateType.MUTUAL_PARALYSIS: "相互硬直 - 両軍とも動くことができない状態",
            StalemateType.COMMAND_STALEMATE: "指揮膠着 - 明確な目標がない状態"
        }

        base_desc = descriptions.get(self._current_stalemate, "不明")

        if self._stalemate_intensity >= 8:
            return f"{base_desc}（緊急）"
        elif self._stalemate_intensity >= 5:
            return f"{base_desc}（深刻）"

        return base_desc


# Global instance
_stalemate_system = StalemateSystem()


def get_stalemate_system() -> StalemateSystem:
    """Get the global stalemate system"""
    return _stalemate_system
