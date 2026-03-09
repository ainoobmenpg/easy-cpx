# ExCon (Enemy Commander) AI for Operational CPX
# Provides proactive enemy AI with tactical decision-making
import logging
from typing import Optional
from enum import Enum
import random

# Import unit profiles for behavior and compatibility
from app.data.unit_profiles import get_unit_profile, get_compatibility_bonus
from app.models import UnitStatus

# Configure logger for enemy AI
ai_logger = logging.getLogger("cpx.ai")


class EnemyTactic(Enum):
    """Enemy tactical options"""
    AGGRESSIVE = "aggressive"  # Direct attack
    COUNTERATTACK = "counterattack"  # Respond to player moves
    FLANKING = "flanking"  # Side attack
    RECONNAISSANCE = "reconnaissance"  # Gather intel
    DEFENSIVE = "defensive"  # Consolidate positions
    RETREAT = "retreat"  # Fall back
    RESERVE_DEPLOYMENT = "reserve_deployment"  # Bring in reinforcements
    FEINT = "feint"  # Deception maneuver
    FIRE_CONCENTRATION = "fire_concentration"  # Artillery/coordinate fire
    SUPPLY_INTERDICTION = "supply_interdiction"  # Cut supply lines


class EnemyIntent(Enum):
    """High-level enemy objectives"""
    SEIZE_INITIATIVE = "seize_initiative"
    DEFEND_TERRITORY = "defend_territory"
    attrITIONAL = "attritional"
    ENCIRCLEMENT = "encirclement"
    BREAKTHROUGH = "breakthrough"
    HOLD = "hold"


class ExConAI:
    """
    Enemy Commander AI with proactive tactical decision-making

    The enemy AI maintains its own objectives and can act independently
    of player actions, creating a dynamic and challenging opponent.
    """

    def __init__(self, seed: Optional[int] = None, scenario_config: Optional[dict] = None):
        self._random = random.Random(seed)
        self._current_intent: EnemyIntent = EnemyIntent.DEFEND_TERRITORY
        self._intent_duration = 0  # Turns remaining for current intent
        self._last_player_action: Optional[dict] = None
        self._tactical_situation = "normal"  # normal, pressure, critical
        self._aggression_level = 0.5  # 0.0 to 1.0
        self._known_player_positions: dict[int, tuple[int, int]] = {}
        self._map_width: float = 50.0
        self._map_height: float = 30.0

        # Scenario-driven configuration (can be passed from scenario settings)
        self._scenario_config = scenario_config or {}
        # Enemy retreat direction: dx/dy normalized vector (scenario-driven)
        # Default: retreat toward east edge (dx=1.0)
        retreat_dir = self._scenario_config.get("enemy_retreat_direction", {"dx": 1.0, "dy": 0.0})
        self._enemy_retreat_dx = retreat_dir.get("dx", 1.0)
        self._enemy_retreat_dy = retreat_dir.get("dy", 0.0)

    def update_intent(self, game_state: dict):
        """
        Update enemy commander's intent based on game state

        Called at the start of each enemy turn to determine
        the overall strategic objective.
        """
        # Analyze current situation
        player_units = [u for u in game_state.get("units", []) if u.get("side") == "player"]
        enemy_units = [u for u in game_state.get("units", []) if u.get("side") == "enemy"]

        # Count units by status
        player_strength = sum(u.get("strength", 0) for u in player_units)
        enemy_strength = sum(u.get("strength", 0) for u in enemy_units)

        # Update tactical situation
        if enemy_strength < player_strength * 0.5:
            self._tactical_situation = "critical"
        elif enemy_strength < player_strength * 0.8:
            self._tactical_situation = "pressure"
        else:
            self._tactical_situation = "normal"

        ai_logger.debug(f"[AI] Situation: player_strength={player_strength}, enemy_strength={enemy_strength}, situation={self._tactical_situation}")

        # Adjust aggression based on situation
        if self._tactical_situation == "critical":
            self._aggression_level = max(0.2, self._aggression_level - 0.1)
        elif self._tactical_situation == "pressure":
            self._aggression_level = max(0.3, self._aggression_level - 0.05)
        else:
            self._aggression_level = min(0.9, self._aggression_level + 0.05)

        ai_logger.debug(f"[AI] Aggression level: {self._aggression_level:.2f}, intent_duration: {self._intent_duration}")

        # Update intent every 2-3 turns
        self._intent_duration -= 1
        if self._intent_duration <= 0:
            self._choose_new_intent(game_state)

    def _choose_new_intent(self, game_state: dict):
        """Choose a new strategic intent based on game state"""
        intents = list(EnemyIntent)

        # Weight intents based on situation
        weights = {
            EnemyIntent.SEIZE_INITIATIVE: 0.2,
            EnemyIntent.DEFEND_TERRITORY: 0.3,
            EnemyIntent.ATTRITIONAL: 0.2,
            EnemyIntent.ENCIRCLEMENT: 0.1,
            EnemyIntent.BREAKTHROUGH: 0.1,
            EnemyIntent.HOLD: 0.1
        }

        # Adjust weights based on tactical situation
        if self._tactical_situation == "critical":
            weights[EnemyIntent.DEFEND_TERRITORY] = 0.4
            weights[EnemyIntent.HOLD] = 0.3
            weights[EnemyIntent.SEIZE_INITIATIVE] = 0.1
        elif self._tactical_situation == "pressure":
            weights[EnemyIntent.DEFEND_TERRITORY] = 0.3
            weights[EnemyIntent.ATTRITIONAL] = 0.3

        # Select weighted random intent
        intent_list = list(weights.keys())
        weight_list = list(weights.values())
        self._current_intent = self._random.choices(intent_list, weights=weight_list)[0]
        self._intent_duration = self._random.randint(2, 4)

        ai_logger.debug(f"[AI] New intent selected: {self._current_intent.value} for {self._intent_duration} turns")

    def generate_orders(self, game_state: dict) -> list[dict]:
        """
        Generate enemy unit orders based on current intent and situation

        Returns:
            List of order dicts with keys: unit_id, order_type, target, params
        """
        # Get map dimensions from game state (scenario-driven)
        self._map_width = game_state.get("map_width", 50.0)
        self._map_height = game_state.get("map_height", 30.0)

        self.update_intent(game_state)

        enemy_units = [u for u in game_state.get("units", []) if u.get("side") == "enemy"]
        player_units = [u for u in game_state.get("units", []) if u.get("side") == "player"]

        if not enemy_units:
            return []

        ai_logger.debug(f"[AI] Enemy intent: {self._current_intent.value} (aggression: {self._aggression_level:.1f})")
        ai_logger.debug(f"[AI] Processing {len(enemy_units)} enemy units vs {len(player_units)} player units")
        ai_logger.debug(f"[AI] Map dimensions: {self._map_width}x{self._map_height}")

        orders = []

        # Determine primary tactic for each enemy unit
        for unit in enemy_units:
            order = self._generate_unit_order(unit, player_units, game_state)
            if order:
                orders.append(order)
                ai_logger.debug(f"[AI] {unit.get('name', 'Unknown')} ({unit.get('type', 'unknown')}): {order.get('order_type', 'none')} -> {order.get('target', 'none')}")

        ai_logger.debug(f"[AI] Generated {len(orders)} orders total")
        return orders

    def _generate_unit_order(
        self,
        enemy_unit: dict,
        player_units: list[dict],
        game_state: dict
    ) -> Optional[dict]:
        """Generate an order for a single enemy unit using behavior profiles"""

        unit_type = enemy_unit.get("type", "")
        unit_name = enemy_unit.get("name", "Unknown")
        unit_x = enemy_unit.get("x", 0)
        unit_y = enemy_unit.get("y", 0)

        # Get unit behavior profile
        profile = get_unit_profile(unit_type)
        ai_logger.debug(f"[AI] {unit_name}: profile={unit_type}, pos=({unit_x:.1f},{unit_y:.1f})")

        # Find nearest player unit
        nearest_player = None
        min_dist = float("inf")
        for p_unit in player_units:
            dist = self._distance(unit_x, unit_y, p_unit.get("x", 0), p_unit.get("y", 0))
            if dist < min_dist:
                min_dist = dist
                nearest_player = p_unit

        ai_logger.debug(f"[AI] {unit_name}: nearest_player={nearest_player.get('name', 'None') if nearest_player else 'None'}, dist={min_dist:.1f}")

        # Use behavior profile to determine action
        # Recon-only units (UAV) should always use recon tactic
        if profile.recon_only:
            ai_logger.debug(f"[AI] {unit_name}: using RECON tactic (recon_only)")
            return self._recon_tactic(enemy_unit, player_units)

        # Artillery should use artillery tactic
        if profile.stay_rear:
            ai_logger.debug(f"[AI] {unit_name}: using ARTILLERY tactic (stay_rear)")
            return self._artillery_tactic(enemy_unit, player_units, min_dist)

        # Air defense should prioritize staying at range
        if profile.target_air:
            ai_logger.debug(f"[AI] {unit_name}: using AIR_DEFENSE tactic (target_air)")
            return self._air_defense_tactic(enemy_unit, player_units, min_dist)

        # Units that avoid combat (transport helicopters, support)
        if profile.avoid_combat:
            ai_logger.debug(f"[AI] {unit_name}: using AVOIDANCE tactic (avoid_combat)")
            return self._avoidance_tactic(enemy_unit, player_units, min_dist)

        # Default: ground units
        ai_logger.debug(f"[AI] {unit_name}: using GROUND tactic")
        return self._ground_tactic(enemy_unit, player_units, min_dist)

    def _ground_tactic(
        self,
        unit: dict,
        player_units: list[dict],
        distance_to_nearest: float
    ) -> dict:
        """Generate tactics for ground combat units"""

        unit_type = unit.get("type", "")

        # Decision tree based on intent and situation
        if self._tactical_situation == "critical":
            # Defensive tactics when under pressure
            if self._random.random() < 0.6:
                return {
                    "unit_id": unit.get("id"),
                    "order_type": "defend",
                    "target": {"x": unit.get("x"), "y": unit.get("y")},
                    "params": {"intent": "hold_position"}
                }
            else:
                return {
                    "unit_id": unit.get("id"),
                    "order_type": "retreat",
                    "target": self._get_retreat_position(unit),
                    "params": {"reason": "tactical_retreat"}
                }

        elif self._current_intent == EnemyIntent.ATTRITIONAL:
            # Hit-and-run tactics
            if distance_to_nearest < 5:
                return {
                    "unit_id": unit.get("id"),
                    "order_type": "attack",
                    "target": self._get_nearest_enemy_position(unit, player_units),
                    "params": {"tactic": "harassment"}
                }
            else:
                return {
                    "unit_id": unit.get("id"),
                    "order_type": "move",
                    "target": self._get_flanking_position(unit, player_units),
                    "params": {"tactic": "approach"}
                }

        elif self._current_intent == EnemyIntent.ENCIRCLEMENT:
            # Try to encircle player forces
            return {
                "unit_id": unit.get("id"),
                "order_type": "move",
                "target": self._get_encirclement_position(unit, player_units),
                "params": {"tactic": "encircle"}
            }

        elif self._current_intent == EnemyIntent.BREAKTHROUGH:
            # Aggressive push
            if distance_to_nearest < 3:
                return {
                    "unit_id": unit.get("id"),
                    "order_type": "attack",
                    "target": self._get_nearest_enemy_position(unit, player_units),
                    "params": {"tactic": "breakthrough"}
                }
            else:
                return {
                    "unit_id": unit.get("id"),
                    "order_type": "move",
                    "target": self._get_nearest_enemy_position(unit, player_units),
                    "params": {"tactic": "advance"}
                }

        else:
            # Default: tactical movement based on aggression
            if self._random.random() < self._aggression_level:
                if distance_to_nearest < 4:
                    return {
                        "unit_id": unit.get("id"),
                        "order_type": "attack",
                        "target": self._get_nearest_enemy_position(unit, player_units),
                        "params": {"tactic": "standard"}
                    }
                else:
                    return {
                        "unit_id": unit.get("id"),
                        "order_type": "move",
                        "target": self._get_advance_position(unit, player_units),
                        "params": {"tactic": "advance"}
                    }
            else:
                return {
                    "unit_id": unit.get("id"),
                    "order_type": "defend",
                    "target": {"x": unit.get("x"), "y": unit.get("y")},
                    "params": {"intent": "consolidate"}
                }

    def _artillery_tactic(
        self,
        unit: dict,
        player_units: list[dict],
        distance: float
    ) -> dict:
        """Generate tactics for artillery units"""
        if distance > 15:
            # Move closer to firing range
            return {
                "unit_id": unit.get("id"),
                "order_type": "move",
                "target": self._get_advance_position(unit, player_units),
                "params": {"tactic": "position_for_fire"}
            }
        elif distance > 5:
            # Fire from distance
            return {
                "unit_id": unit.get("id"),
                "order_type": "attack",
                "target": self._get_nearest_enemy_position(unit, player_units),
                "params": {"tactic": "indirect_fire"}
            }
        else:
            # Too close - defend or retreat
            return {
                "unit_id": unit.get("id"),
                "order_type": "defend",
                "target": {"x": unit.get("x"), "y": unit.get("y")},
                "params": {"intent": "defend_position"}
            }

    def _recon_tactic(self, unit: dict, player_units: list[dict]) -> dict:
        """Generate tactics for reconnaissance units"""
        # Always try to move toward player forces
        return {
            "unit_id": unit.get("id"),
            "order_type": "recon",
            "target": self._get_recon_position(unit, player_units),
            "params": {"tactic": "screen"}
        }

    def _air_tactic(self, unit: dict, player_units: list[dict]) -> dict:
        """Generate tactics for air units"""
        return {
            "unit_id": unit.get("id"),
            "order_type": "attack",
            "target": self._get_nearest_enemy_position(unit, player_units),
            "params": {"tactic": "air_strike"}
        }

    def _supply_tactic(self, unit: dict, game_state: dict) -> dict:
        """Generate tactics for supply units"""
        # Move toward friendly units or maintain position
        enemy_units = [u for u in game_state.get("units", []) if u.get("side") == "enemy"]
        if enemy_units:
            avg_x = sum(u.get("x", 0) for u in enemy_units) / len(enemy_units)
            avg_y = sum(u.get("y", 0) for u in enemy_units) / len(enemy_units)
        else:
            # Default to center of map (scenario-driven)
            avg_x, avg_y = self._map_width / 2, self._map_height / 2

        return {
            "unit_id": unit.get("id"),
            "order_type": "move",
            "target": {"x": avg_x, "y": avg_y},
            "params": {"tactic": "maintain_supply"}
        }

    def _air_defense_tactic(self, unit: dict, player_units: list[dict], distance: float) -> dict:
        """Generate tactics for air defense units - maintain distance from air threats"""
        # Get behavior profile
        profile = get_unit_profile(unit.get("type", ""))

        # Check for air threats (aircraft, helicopters)
        air_threats = [p for p in player_units if "air" in p.get("type", "").lower() or "helo" in p.get("type", "").lower()]

        if air_threats:
            # Engage air threats
            nearest_air = min(air_threats, key=lambda p: self._distance(unit.get("x", 0), unit.get("y", 0), p.get("x", 0), p.get("y", 0)))
            return {
                "unit_id": unit.get("id"),
                "order_type": "defend",
                "target": {"x": unit.get("x"), "y": unit.get("y")},
                "params": {"intent": "engage_air", "target": nearest_air.get("name")}
            }

        # No air threats - maintain defensive position
        if distance < profile.min_range:
            # Too close - move away
            return {
                "unit_id": unit.get("id"),
                "order_type": "move",
                "target": self._get_retreat_position(unit),
                "params": {"tactic": "maintain_range"}
            }
        elif distance > profile.preferred_range:
            # Too far - move closer
            return {
                "unit_id": unit.get("id"),
                "order_type": "move",
                "target": self._get_advance_position(unit, player_units),
                "params": {"tactic": "maintain_range"}
            }
        else:
            # In sweet spot - hold position
            return {
                "unit_id": unit.get("id"),
                "order_type": "defend",
                "target": {"x": unit.get("x"), "y": unit.get("y")},
                "params": {"intent": "defend_position"}
            }

    def _avoidance_tactic(self, unit: dict, player_units: list[dict], distance: float) -> dict:
        """Generate tactics for units that avoid combat (transport, support)"""
        # Get behavior profile
        profile = get_unit_profile(unit.get("type", ""))

        # If too close to enemy, retreat
        if distance < profile.preferred_range:
            return {
                "unit_id": unit.get("id"),
                "order_type": "move",
                "target": self._get_retreat_position(unit),
                "params": {"tactic": "avoid_combat"}
            }

        # Stay at safe distance or move toward friendly units
        enemy_units = [u for u in player_units]  # Actually this should be friendly units
        if enemy_units:
            avg_x = sum(u.get("x", 0) for u in enemy_units) / len(enemy_units)
            avg_y = sum(u.get("y", 0) for u in enemy_units) / len(enemy_units)
            return {
                "unit_id": unit.get("id"),
                "order_type": "move",
                "target": {"x": avg_x, "y": avg_y},
                "params": {"tactic": "rejoin_unit"}
            }

        return {
            "unit_id": unit.get("id"),
            "order_type": "defend",
            "target": {"x": unit.get("x"), "y": unit.get("y")},
            "params": {"intent": "hold_position"}
        }

    # Helper methods
    def _distance(self, x1: float, y1: float, x2: float, y2: float) -> float:
        """Calculate distance between two points"""
        return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5

    def _get_nearest_enemy_position(
        self,
        unit: dict,
        player_units: list[dict]
    ) -> dict:
        """Get position of nearest player unit (excluding destroyed units)"""
        # Filter out destroyed units
        alive_units = [
            p for p in player_units
            if p.get("status") != UnitStatus.DESTROYED.value
        ]
        if not alive_units:
            # Default to center of map (scenario-driven)
            return {"x": self._map_width / 2, "y": self._map_height / 2}

        unit_x, unit_y = unit.get("x", 0), unit.get("y", 0)
        nearest = min(
            alive_units,
            key=lambda p: self._distance(unit_x, unit_y, p.get("x", 0), p.get("y", 0)),
            default=None
        )
        if nearest:
            return {"x": nearest.get("x", 0), "y": nearest.get("y", 0)}
        return {"x": self._map_width / 2, "y": self._map_height / 2}

    def _get_retreat_position(self, unit: dict) -> dict:
        """Get retreat position (move away from player using scenario-driven direction)"""
        x, y = unit.get("x", self._map_width / 2), unit.get("y", self._map_height / 2)
        # Use scenario-driven retreat direction
        # Default: move toward opposite edge (east when player is west)
        retreat_x = x + self._enemy_retreat_dx * 10
        retreat_y = y + self._enemy_retreat_dy * 10
        return {
            "x": max(0, min(self._map_width, retreat_x)),
            "y": max(0, min(self._map_height, retreat_y))
        }

    def _get_flanking_position(
        self,
        unit: dict,
        player_units: list[dict]
    ) -> dict:
        """Get flanking position"""
        if not player_units:
            return {"x": unit.get("x", self._map_width / 2), "y": unit.get("y", self._map_height / 2)}

        # Find player's center
        player_x = sum(p.get("x", 0) for p in player_units) / len(player_units)
        player_y = sum(p.get("y", 0) for p in player_units) / len(player_units)

        unit_x, unit_y = unit.get("x", 0), unit.get("y", 0)

        # Move to side
        dx = player_x - unit_x
        dy = player_y - unit_y

        # Perpendicular direction
        target_x = unit_x - dy * 0.5
        target_y = unit_y + dx * 0.5

        return {
            "x": max(0, min(self._map_width, target_x)),
            "y": max(0, min(self._map_height, target_y))
        }

    def _get_encirclement_position(
        self,
        unit: dict,
        player_units: list[dict]
    ) -> dict:
        """Get position to encircle player forces"""
        if not player_units:
            return {"x": self._map_width / 2, "y": self._map_height / 2}

        # Target position behind player
        player_x = sum(p.get("x", 0) for p in player_units) / len(player_units)
        player_y = sum(p.get("y", 0) for p in player_units) / len(player_units)

        unit_x, unit_y = unit.get("x", 0), unit.get("y", 0)

        # Move behind player (opposite direction)
        dx = unit_x - player_x
        dy = unit_y - player_y
        dist = max(1, self._distance(unit_x, unit_y, player_x, player_y))

        # Move closer but from behind
        target_x = unit_x + dx * 0.3
        target_y = unit_y + dy * 0.3

        return {
            "x": max(0, min(self._map_width, target_x)),
            "y": max(0, min(self._map_height, target_y))
        }

    def _get_advance_position(
        self,
        unit: dict,
        player_units: list[dict]
    ) -> dict:
        """Get position to advance toward player"""
        target = self._get_nearest_enemy_position(unit, player_units)
        unit_x, unit_y = unit.get("x", 0), unit.get("y", 0)

        # Move 3/4 toward player
        new_x = unit_x + (target["x"] - unit_x) * 0.75
        new_y = unit_y + (target["y"] - unit_y) * 0.75

        return {"x": new_x, "y": new_y}

    def _get_recon_position(
        self,
        unit: dict,
        player_units: list[dict]
    ) -> dict:
        """Get position for reconnaissance"""
        if not player_units:
            return {"x": self._map_width / 2, "y": self._map_height / 2}

        # Move between enemy lines
        enemy_x = sum(u.get("x", 0) for u in player_units) / len(player_units)
        enemy_y = sum(u.get("y", 0) for u in player_units) / len(player_units)

        unit_x, unit_y = unit.get("x", 0), unit.get("y", 0)

        # Move toward player but stop short
        dx = enemy_x - unit_x
        dy = enemy_y - unit_y
        dist = max(1, self._distance(unit_x, unit_y, enemy_x, enemy_y))

        # Move 60% toward player (recon distance)
        target_x = unit_x + dx * 0.6
        target_y = unit_y + dy * 0.6

        return {"x": target_x, "y": target_y}

    def get_intent_description(self) -> str:
        """Get human-readable description of current enemy intent"""
        intent_descriptions = {
            EnemyIntent.SEIZE_INITIATIVE: "Initiative seizure - Enemy seeking to take action",
            EnemyIntent.DEFEND_TERRITORY: "Territorial defense - Enemy consolidating positions",
            EnemyIntent.ATTRITIONAL: "Attritional warfare - Enemy targeting our strengths",
            EnemyIntent.ENCIRClement: "Encirclement - Enemy attempting to flank and surround",
            EnemyIntent.BREAKTHROUGH: "Breakthrough - Enemy pushing for decisive action",
            EnemyIntent.HOLD: "Holding action - Enemy playing defensively"
        }
        return intent_descriptions.get(self._current_intent, "Unknown intent")

    def get_tactical_assessment(self) -> dict:
        """Get current tactical assessment"""
        return {
            "intent": self._current_intent.value,
            "aggression_level": self._aggression_level,
            "tactical_situation": self._tactical_situation,
            "intent_description": self.get_intent_description()
        }
