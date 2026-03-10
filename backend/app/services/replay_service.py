# Replay Service - Reconstruct game state from structured logs
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from enum import Enum

logger = logging.getLogger("cpx")


class ReplayEventType(Enum):
    """Types of events in replay data"""
    TURN_START = "turn_start"
    TURN_END = "turn_end"
    MOVEMENT = "movement"
    COMBAT = "combat"
    INJECT = "inject"
    ADJUDICATION = "adjudication"
    SUPPLY = "supply"
    RECON = "recon"
    FRICTION = "friction"


class ReplayState:
    """Reconstructed game state at a point in time"""

    def __init__(self):
        self.turn_number: int = 0
        self.time: str = "05:40"
        self.weather: str = "clear"
        self.units: Dict[int, Dict[str, Any]] = {}
        self.events: List[Dict[str, Any]] = []
        self.sitrep: Optional[Dict[str, Any]] = None
        self.seed: int = 0
        self.turn_seed: int = 0


class ReplayService:
    """
    Service for replaying games from structured logs.

    Features:
    - Load game logs from database or file
    - Reconstruct state at any turn
    - Provide event timeline for UI playback
    - Support seeking to specific turns/events
    """

    def __init__(self, game_id: Optional[int] = None):
        self.game_id = game_id
        self._logs: List[Dict[str, Any]] = []
        self._seed: Optional[int] = None
        self._turn_seeds: Dict[int, int] = {}
        self._initial_state: Optional[Dict[str, Any]] = None
        self._current: int = 0

    def load_from_db(self, db: "Session", game_id: int) -> bool:
        """Load replay data from database"""
        from app.models import Game, Turn, Event

        # Get game info
        game = db.query(Game).filter(Game.id == game_id).first()
        if not game:
            logger.error(f"Game {game_id} not found")
            return False

        # Load all turns
        turns = db.query(Turn).filter(
            Turn.game_id == game_id
        ).order_by(Turn.turn_number).all()

        if not turns:
            logger.error(f"No turns found for game {game_id}")
            return False

        # Build initial state from game
        self._initial_state = {
            "game_id": game_id,
            "name": game.name,
            "scenario_id": game.scenario_id,
            "map_width": game.map_width,
            "map_height": game.map_height,
            "terrain_data": game.terrain_data,
            "game_mode": game.game_mode.value if hasattr(game.game_mode, 'value') else game.game_mode,
        }

        # Process each turn
        for turn in turns:
            self._process_turn(turn)

        # Extract seed info from game
        self._seed = self._extract_seed(game)

        logger.info(f"Loaded replay data: {len(self._logs)} events, seed={self._seed}")
        return True

    def load_from_logs(self, log_data: List[Dict[str, Any]]) -> bool:
        """Load replay data from structured log entries"""
        if not log_data:
            logger.error("No log data provided")
            return False

        self._logs = log_data
        self._extract_seed_info()
        logger.info(f"Loaded {len(self._logs)} log entries")
        return True

    def _process_turn(self, turn: "Turn") -> None:
        """Process a turn and add events to log"""
        # Add turn start event
        self._logs.append({
            "event_type": ReplayEventType.TURN_START.value,
            "turn": turn.turn_number,
            "time": turn.time,
            "weather": turn.weather,
            "phase": turn.phase,
            "seed": self._turn_seeds.get(turn.turn_number, 0),
        })

        # Add turn events
        if turn.events:
            for event in turn.events:
                self._logs.append({
                    "event_type": event.event_type,
                    "turn": turn.turn_number,
                    "data": event.data,
                    "description": event.description,
                })

        # Add sitrep if available
        if turn.sitrep:
            self._logs.append({
                "event_type": "sitrep",
                "turn": turn.turn_number,
                "data": turn.sitrep,
            })

        # Add turn end event
        self._logs.append({
            "event_type": ReplayEventType.TURN_END.value,
            "turn": turn.turn_number,
        })

    def _extract_seed(self, game: "Game") -> int:
        """Extract seed from game metadata"""
        # Try to get from environment or generate from game_id
        import os
        env_seed = os.environ.get("CPX_RNG_SEED")
        if env_seed:
            return int(env_seed)

        # Generate deterministic seed from game_id
        import hashlib
        game_id = game.id
        hash_input = f"cpx_game_{game_id}_{os.environ.get('CPX_SEED_SALT', 'default')}"
        return int(hashlib.md5(hash_input.encode()).hexdigest()[:8], 16)

    def _extract_seed_info(self) -> None:
        """Extract seed information from loaded logs"""
        for log in self._logs:
            # Extract turn seed
            if log.get("event_type") == ReplayEventType.TURN_START.value:
                turn = log.get("turn", 0)
                seed = log.get("seed", 0)
                if seed:
                    self._turn_seeds[turn] = seed
            # Extract base seed from any log entry with seed
            if "seed" in log and not self._seed:
                self._seed = log["seed"]

    def get_state_at_turn(self, turn_number: int) -> ReplayState:
        """Get reconstructed state at specific turn"""
        state = ReplayState()
        state.turn_number = turn_number
        state.seed = self._seed
        state.turn_seed = self._turn_seeds.get(turn_number, 0)

        # Collect all events up to and including this turn
        relevant_events = []
        for log in self._logs:
            if log.get("turn", 0) <= turn_number:
                relevant_events.append(log)

                # Update state based on event type
                event_type = log.get("event_type", "")
                if event_type == ReplayEventType.TURN_START.value:
                    state.time = log.get("time", state.time)
                    state.weather = log.get("weather", state.weather)

        state.events = relevant_events
        return state

    def get_event_timeline(self) -> List[Dict[str, Any]]:
        """Get simplified event timeline for UI"""
        timeline = []
        for log in self._logs:
            event_type = log.get("event_type", "")
            turn = log.get("turn", 0)

            # Skip internal events
            if event_type in [ReplayEventType.TURN_START.value, ReplayEventType.TURN_END.value]:
                timeline.append({
                    "turn": turn,
                    "type": event_type,
                    "time": log.get("time"),
                    "weather": log.get("weather"),
                })
            elif event_type == "combat":
                timeline.append({
                    "turn": turn,
                    "type": "combat",
                    "attacker": log.get("data", {}).get("attacker"),
                    "defender": log.get("data", {}).get("defender"),
                    "outcome": log.get("data", {}).get("outcome"),
                })
            elif event_type == "movement":
                timeline.append({
                    "turn": turn,
                    "type": "movement",
                    "unit_id": log.get("data", {}).get("unit_id"),
                    "from": log.get("data", {}).get("from"),
                    "to": log.get("data", {}).get("to"),
                })
            elif event_type == "inject":
                timeline.append({
                    "turn": turn,
                    "type": "inject",
                    "inject_type": log.get("data", {}).get("type"),
                    "trigger": log.get("data", {}).get("trigger"),
                })
            elif event_type == "sitrep":
                timeline.append({
                    "turn": turn,
                    "type": "sitrep",
                    "summary": log.get("data", {}).get("summary", "")[:100],
                })

        return timeline

    def get_turn_summary(self, turn_number: int) -> Optional[Dict[str, Any]]:
        """Get summary of a specific turn"""
        events = [log for log in self._logs if log.get("turn") == turn_number]

        if not events:
            return None

        combat_events = [e for e in events if e.get("event_type") == "combat"]
        movement_events = [e for e in events if e.get("event_type") == "movement"]
        inject_events = [e for e in events if e.get("event_type") == "inject"]
        sitrep = next((e for e in events if e.get("event_type") == "sitrep"), None)

        return {
            "turn": turn_number,
            "seed": self._turn_seeds.get(turn_number, self._seed),
            "combat_count": len(combat_events),
            "movement_count": len(movement_events),
            "inject_count": len(inject_events),
            "sitrep": sitrep.get("data") if sitrep else None,
        }

    def get_total_turns(self) -> int:
        """Get total number of turns in replay"""
        turns = set()
        for log in self._logs:
            turn = log.get("turn")
            if turn:
                turns.add(turn)
        return max(turns) if turns else 0

    @property
    def seed(self) -> int:
        """Get the base seed for this replay"""
        return self._seed or 0

    def get_turn_seeds(self) -> Dict[int, int]:
        """Get all turn seeds"""
        return self._turn_seeds.copy()


# Helper function for dependency injection
def create_replay_service(game_id: Optional[int] = None) -> ReplayService:
    """Create a new ReplayService instance"""
    return ReplayService(game_id=game_id)
