# Structured Logging Service for Operational CPX
# Provides JSON-structured logging for adjudication results
import json
import logging
import sys
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum
import threading

# Custom log levels for structured logging
ADJUDICATION_LOG_LEVEL = 25  # Between INFO(20) and WARNING(30)
INJECT_LOG_LEVEL = 26


class LogCategory(Enum):
    """Log category identifiers"""
    ADJUDICATION = "adjudication"
    INJECT = "inject"
    COMBAT = "combat"
    MOVEMENT = "movement"
    SUPPLY = "supply"
    REcon = "recon"


class StructuredLogger:
    """
    Structured logging for CPX adjudication.

    Features:
    - JSON output format
    - Context preservation across operations
    - Adjudication log with roll values and modifiers
    - Inject log for events and decisions
    """

    def __init__(self, name: str = "cpx.structured"):
        self.logger = logging.getLogger(name)
        self._context: Dict[str, Any] = {}
        self._lock = threading.Lock()

        # Ensure level is set
        if self.logger.level == 0:
            self.logger.setLevel(logging.DEBUG)

        # Add handler if not present
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(logging.Formatter('%(message)s'))
            self.logger.addHandler(handler)

    def set_context(self, **kwargs) -> None:
        """Set context for subsequent log entries"""
        with self._lock:
            self._context.update(kwargs)

    def clear_context(self) -> None:
        """Clear context"""
        with self._lock:
            self._context = {}

    def _build_log_entry(
        self,
        category: str,
        event: str,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Build structured log entry"""
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "category": category,
            "event": event,
        }

        # Add context
        with self._lock:
            entry["context"] = self._context.copy()

        # Add data
        if data:
            entry["data"] = data

        # Add extra kwargs
        if kwargs:
            entry["extra"] = kwargs

        return entry

    def log_adjudication(
        self,
        unit_id: str,
        action: str,
        preconditions: Dict[str, Any],
        roll_result: Optional[Dict[str, Any]] = None,
        modifiers: Optional[Dict[str, Any]] = None,
        result: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> None:
        """
        Log adjudication decision.

        Args:
            unit_id: Unit identifier
            action: Action type (attack, move, etc.)
            preconditions: Precondition check results
            roll_result: Dice roll results (die1, die2, total)
            modifiers: Modifier breakdown
            result: Final result
        """
        data = {
            "unit_id": unit_id,
            "action": action,
            "preconditions": preconditions,
        }

        if roll_result:
            data["roll"] = roll_result

        if modifiers:
            data["modifiers"] = modifiers

        if result:
            data["result"] = result

        entry = self._build_log_entry(
            category=LogCategory.ADJUDICATION.value,
            event="adjudication",
            data=data,
            **kwargs
        )

        self.logger.log(ADJUDICATION_LOG_LEVEL, json.dumps(entry))

    def log_combat(
        self,
        attacker_id: str,
        defender_id: str,
        terrain: str,
        attack_roll: int,
        defense_roll: int,
        net_modifier: int,
        outcome: str,
        damage: Dict[str, Any],
        **kwargs
    ) -> None:
        """Log combat adjudication"""
        data = {
            "attacker": attacker_id,
            "defender": defender_id,
            "terrain": terrain,
            "attack_roll": attack_roll,
            "defense_roll": defense_roll,
            "net_modifier": net_modifier,
            "outcome": outcome,
            "damage": damage,
        }

        entry = self._build_log_entry(
            category=LogCategory.COMBAT.value,
            event="combat",
            data=data,
            **kwargs
        )

        self.logger.log(ADJUDICATION_LOG_LEVEL, json.dumps(entry))

    def log_movement(
        self,
        unit_id: str,
        from_pos: Tuple[int, int],
        to_pos: Tuple[int, int],
        terrain: str,
        cost: float,
        success: bool,
        **kwargs
    ) -> None:
        """Log movement result"""
        data = {
            "unit_id": unit_id,
            "from": {"x": from_pos[0], "y": from_pos[1]},
            "to": {"x": to_pos[0], "y": to_pos[1]},
            "terrain": terrain,
            "cost": cost,
            "success": success,
        }

        entry = self._build_log_entry(
            category=LogCategory.MOVEMENT.value,
            event="movement",
            data=data,
            **kwargs
        )

        self.logger.log(ADJUDICATION_LOG_LEVEL, json.dumps(entry))

    def log_inject(
        self,
        inject_type: str,
        trigger: str,
        details: Dict[str, Any],
        affected_units: Optional[List[str]] = None,
        **kwargs
    ) -> None:
        """
        Log inject/event decision.

        Args:
            inject_type: Type of inject
            trigger: What triggered the inject
            details: Event details
            affected_units: List of affected unit IDs
        """
        data = {
            "type": inject_type,
            "trigger": trigger,
            "details": details,
        }

        if affected_units:
            data["affected_units"] = affected_units

        entry = self._build_log_entry(
            category=LogCategory.INJECT.value,
            event="inject",
            data=data,
            **kwargs
        )

        self.logger.log(INJECT_LOG_LEVEL, json.dumps(entry))

    def log_turn_summary(
        self,
        turn_number: int,
        seed: int,
        events: List[Dict[str, Any]],
        outcomes: Dict[str, Any],
        **kwargs
    ) -> None:
        """Log turn summary"""
        data = {
            "turn": turn_number,
            "seed": seed,
            "events": events,
            "outcomes": outcomes,
        }

        entry = self._build_log_entry(
            category="turn",
            event="summary",
            data=data,
            **kwargs
        )

        self.logger.info(json.dumps(entry))

    def log_debug(self, message: str, **kwargs) -> None:
        """Log debug message"""
        entry = self._build_log_entry(
            category="debug",
            event="debug",
            **kwargs
        )
        entry["message"] = message
        self.logger.debug(json.dumps(entry))


# Global structured logger instance
_structured_logger: Optional[StructuredLogger] = None


def get_structured_logger(name: str = "cpx.structured") -> StructuredLogger:
    """Get or create global structured logger"""
    global _structured_logger
    if _structured_logger is None:
        _structured_logger = StructuredLogger(name)
    return _structured_logger
