# Game State Service - Handles game state retrieval with Fog of War
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session


class GameStateService:
    """Service for building game state responses with Fog of War applied"""

    def __init__(self, db: Session):
        self.db = db

    def get_player_knowledge(self, game_id: int) -> Dict[int, Dict[str, Any]]:
        """Get player knowledge map for Fog of War filtering"""
        from app.models import PlayerKnowledge

        player_knowledge = self.db.query(PlayerKnowledge).filter(
            PlayerKnowledge.game_id == game_id
        ).all()

        known_enemies = {}
        for pk in player_knowledge:
            if pk.unit_id:
                known_enemies[pk.unit_id] = {
                    "x": pk.x,
                    "y": pk.y,
                    "confidence": pk.confidence,
                    "confidence_score": pk.confidence_score,
                    "last_observed_turn": pk.last_observed_turn,
                    "interpreted_type": pk.interpreted_type,
                    "position_accuracy": pk.position_accuracy
                }

        return known_enemies

    def apply_fog_of_war(self, units: List[Dict[str, Any]], known_enemies: Dict[int, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply Fog of War filtering to units - player units fully visible, enemy units filtered"""
        filtered_units = []

        for unit in units:
            if unit["side"] == "player":
                # Player units are fully visible
                filtered_units.append({
                    **unit,
                    "is_observed": True,
                    "observation_confidence": "confirmed"
                })
            else:
                # Enemy units - check if observed
                known = known_enemies.get(unit["id"])
                if known:
                    # Enemy is observed - return with observed knowledge only
                    filtered_units.append({
                        "id": unit["id"],
                        "name": f"敵{unit['id']}",  # Generic name, not actual type
                        "type": known.get("interpreted_type", "unknown"),  # Use observed type
                        "side": "enemy",
                        "x": known["x"],  # Use observed position
                        "y": known["y"],
                        "status": unit.get("status"),  # Status might be observable
                        "ammo": None,  # Never expose ammo for enemies
                        "fuel": None,  # Never expose fuel for enemies
                        "readiness": None,  # Never expose readiness for enemies
                        "strength": None,  # Never expose strength for enemies
                        "is_observed": True,
                        "observation_confidence": known["confidence"],
                        "confidence_score": known["confidence_score"],
                        "last_observed_turn": known["last_observed_turn"],
                        "last_known_type": known.get("interpreted_type"),
                        "position_accuracy": known.get("position_accuracy", 0)
                    })
                else:
                    # Enemy not observed - hide ALL sensitive information
                    filtered_units.append({
                        "id": unit["id"],
                        "name": "未確認",
                        "type": "unknown",
                        "side": "enemy",
                        "x": None,
                        "y": None,
                        "status": "unknown",
                        "ammo": None,
                        "fuel": None,
                        "readiness": None,
                        "strength": None,
                        "is_observed": False,
                        "observation_confidence": "unknown",
                        "confidence_score": 0,
                        "last_observed_turn": None,
                        "position_accuracy": 0
                    })

        return filtered_units

    def build_response(self, state: Dict[str, Any], filtered_units: List[Dict[str, Any]], game: Any, known_enemies: Dict[int, Dict[str, Any]]) -> Dict[str, Any]:
        """Build final response with filtered units and game metadata"""
        state["units"] = filtered_units
        state["terrain_data"] = game.terrain_data
        state["map_width"] = game.map_width
        state["map_height"] = game.map_height

        # Include player knowledge for frontend UI (last known enemy positions, etc.)
        state["player_knowledge"] = known_enemies

        # Include CPX-CYCLES: Planning/Air/Logistics cycle status
        state["cycles"] = {
            "planning": game.planning_cycle,
            "air_tasking": game.air_tasking_cycle,
            "logistics": game.logistics_cycle,
        }

        return state


def get_game_state_with_fow(db: Session, game_id: int, engine_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Helper function to apply Fog of War to engine state and build response.
    This separates the internal engine state from the external API response.
    """
    from app.models import Game

    # Get game for metadata
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        return {"error": "Game not found"}

    # Get player knowledge for FoW
    service = GameStateService(db)
    known_enemies = service.get_player_knowledge(game_id)

    # Apply FoW filtering
    filtered_units = service.apply_fog_of_war(engine_state.get("units", []), known_enemies)

    # Build response (now includes player_knowledge for frontend)
    return service.build_response(engine_state, filtered_units, game, known_enemies)
