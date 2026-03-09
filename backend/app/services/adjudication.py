# Rule Engine for Operational CPX
from sqlalchemy.orm import Session
from app.models import Unit, Turn, Order, Game, OrderType, UnitStatus, SupplyLevel, EnemyKnowledge, PlayerKnowledge, CommanderOrder
from datetime import datetime
from typing import Optional
import random
import math
import logging

# Configure logging for development
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("cpx")

# Import unit profiles for behavior and compatibility
from app.data.unit_profiles import (
    get_unit_profile,
    get_compatibility_bonus,
    UNIT_BEHAVIOR_PROFILES,
)

# Import terrain services for movement cost calculation
from app.services.terrain import TerrainType, TerrainEffects

# Import commander order and reporting services
from app.services.commander_order_service import CommanderOrderService
from app.services.reporting import ReportingSystem
from app.data.scenarios import get_scenario


# Adjudication condition types
class AdjudicationCondition:
    """Represents a condition for structured adjudication"""

    def __init__(self, name: str, weight: float, description: str):
        self.name = name
        self.weight = weight
        self.description = description
        self.met = False

    def evaluate(self, context: dict) -> bool:
        """Evaluate if condition is met given the context"""
        raise NotImplementedError


class AdjudicationCriteria:
    """
    Structured adjudication criteria based on 9 major conditions

    The system evaluates orders against these conditions to determine:
    - Perfect Success: Superior position + 5+ conditions met
    - Success: Superior position + 4 conditions met
    - Partial: Superior position + 3 conditions met
    - Failed: Inferior position + 3 conditions met
    - Major Failure: Inferior position + 2 or fewer conditions met

    Attack outcome levels:
    1. perfect_success: Attacker wins decisively, defender takes heavy damage
    2. success: Attacker wins, defender takes moderate damage
    3. partial: Both sides take light damage
    4. failed: Defender counter-attacks successfully, attacker takes light damage
    5. major_failed: Defender counter-attacks decisively, attacker takes moderate damage
    """

    # Default conditions and their weights
    CONDITIONS = {
        "superior_firepower": {
            "weight": 1.5,
            "description": "味方が敵戦力を上回っている"
        },
        "position_advantage": {
            "weight": 1.2,
            "description": "有利な地形を占領している"
        },
        "mobility": {
            "weight": 1.0,
            "description": "機動力が確保されている"
        },
        "supply_status": {
            "weight": 1.0,
            "description": "補給体制が確保されている"
        },
        "reconnaissance": {
            "weight": 0.8,
            "description": "偵察が完了している"
        },
        "weather_advantage": {
            "weight": 0.7,
            "description": "天候が有利に作用している"
        },
        "surprise": {
            "weight": 0.8,
            "description": "奇襲要素がある"
        },
        "unit_type_bonus": {
            "weight": 0.6,
            "description": "ユニット種別の相性が有利"
        },
        "readiness_bonus": {
            "weight": 0.5,
            "description": "整備状態が良い"
        }
    }

    # Combat bonuses for unit type matchups
    # Now using the full rock-paper-scissors matrix from unit_profiles
    UNIT_TYPE_BONUSES = {
        "atgm_vs_armor": 0.4,  # ATGM infantry vs armor (from matrix)
        "sniper_vs_inf": 0.3,  # Sniper vs infantry (from matrix)
        "armor_vs_inf": 0.3,   # Armor vs infantry (from matrix)
        "artillery_vs_inf": 0.2,  # Artillery vs infantry (from matrix)
        "air_defense_vs_air": 0.4,  # SAM vs aircraft (from matrix)
        "air_defense_vs_helo": 0.4,  # SAM vs helicopter
    }

    @classmethod
    def evaluate_order(
        cls,
        order: Order,
        unit: Unit,
        target_units: list[Unit],
        game_state: dict,
        weather: str = "clear",
        time: str = "06:00"
    ) -> tuple[str, dict]:
        """
        Evaluate an order using structured criteria

        Returns:
            (outcome, criteria_results)
            outcome: "perfect_success" | "success" | "partial" | "failed" | "major_failed"
            criteria_results: dict of condition -> {met: bool, score: float}
        """

        # Calculate individual condition scores
        results = {}

        # 1. Superior firepower
        unit_strength = unit.strength / 100.0
        target_strength = sum(t.strength for t in target_units) / 100.0 / max(1, len(target_units))
        results["superior_firepower"] = {
            "met": unit_strength > target_strength * 1.2,
            "score": unit_strength / max(0.1, target_strength),
            "description": cls.CONDITIONS["superior_firepower"]["description"]
        }

        # 2. Position advantage - check if unit is on favorable terrain
        # Defensive terrain types: forest, mountain, urban
        favorable_terrain = ["forest", "mountain", "urban", "hill"]
        unit_terrain = getattr(unit, 'terrain', None) or "plain"
        has_position_advantage = unit_terrain in favorable_terrain
        results["position_advantage"] = {
            "met": has_position_advantage,
            "score": 1.0 if has_position_advantage else 0.3,
            "description": f"Position: {unit_terrain} - {'advantage' if has_position_advantage else 'no advantage'}"
        }

        # 3. Mobility
        can_move = unit.fuel != SupplyLevel.EXHAUSTED
        results["mobility"] = {
            "met": can_move,
            "score": 1.0 if can_move else 0.0,
            "description": cls.CONDITIONS["mobility"]["description"]
        }

        # 4. Supply status
        has_supplies = unit.ammo != SupplyLevel.EXHAUSTED
        results["supply_status"] = {
            "met": has_supplies,
            "score": 1.0 if has_supplies else 0.0,
            "description": cls.CONDITIONS["supply_status"]["description"]
        }

        # 5. Reconnaissance (order type based)
        has_recon = order.order_type in [OrderType.RECON, OrderType.MOVE]
        results["reconnaissance"] = {
            "met": has_recon,
            "score": 1.0 if has_recon else 0.5,
            "description": cls.CONDITIONS["reconnaissance"]["description"]
        }

        # 6. Weather advantage
        is_weather_favorable = weather in ["clear", "cloudy"]
        is_night = int(time.split(":")[0]) < 6 or int(time.split(":")[0]) >= 20
        results["weather_advantage"] = {
            "met": is_weather_favorable and not is_night,
            "score": 1.0 if (is_weather_favorable and not is_night) else 0.5,
            "description": cls.CONDITIONS["weather_advantage"]["description"]
        }

        # 7. Surprise (simplified - would need detection system)
        results["surprise"] = {
            "met": False,  # Would check in full implementation
            "score": 0.3,
            "description": cls.CONDITIONS["surprise"]["description"]
        }

        # 8. Unit type bonus - check for favorable matchups
        unit_type_bonus = cls._calculate_unit_type_bonus(unit, target_units)
        results["unit_type_bonus"] = {
            "met": unit_type_bonus > 0,
            "score": 1.0 + unit_type_bonus,
            "description": cls.CONDITIONS["unit_type_bonus"]["description"]
        }

        # 9. Readiness bonus
        has_good_readiness = unit.readiness in [SupplyLevel.FULL, SupplyLevel.DEPLETED]
        readiness_score = 1.0 if unit.readiness == SupplyLevel.FULL else 0.6 if unit.readiness == SupplyLevel.DEPLETED else 0.2
        results["readiness_bonus"] = {
            "met": has_good_readiness,
            "score": readiness_score,
            "description": cls.CONDITIONS["readiness_bonus"]["description"]
        }

        # Calculate weighted score with caps to prevent extreme values
        total_weight = sum(c["weight"] for c in cls.CONDITIONS.values())
        # Cap individual scores at 1.0 to prevent overweighting
        capped_scores = {cond: min(results[cond]["score"], 1.0) for cond in results}
        weighted_score = sum(
            capped_scores[cond] * cls.CONDITIONS[cond]["weight"]
            for cond in results
        ) / total_weight

        # Determine outcome based on score and conditions met
        conditions_met = sum(1 for r in results.values() if r["met"])
        total_conditions = len(results)

        # Determine if attacker has superior position - adjust thresholds for more balanced outcomes
        is_superior = weighted_score >= 0.5 and conditions_met >= 4
        is_inferior = weighted_score < 0.35 or conditions_met < 3

        # 5-stage outcome determination with more balanced thresholds
        if is_superior and conditions_met >= 6:
            outcome = "perfect_success"
        elif is_superior and conditions_met >= 5:
            outcome = "success"
        elif weighted_score >= 0.4:
            outcome = "partial"
        elif is_inferior or weighted_score < 0.25:
            outcome = "major_failed"
        else:
            outcome = "failed"

        return outcome, results

    @classmethod
    def _calculate_unit_type_bonus(cls, attacker: Unit, defenders: list[Unit]) -> float:
        """Calculate combat bonus based on unit type matchups using the full compatibility matrix"""
        attacker_type = attacker.unit_type.lower() if attacker.unit_type else ""

        # Get infantry subtype if applicable
        infantry_subtype = getattr(attacker, 'infantry_subtype', None)
        if infantry_subtype:
            # Append subtype to type for more precise matching
            attacker_type = f"{attacker_type}_{infantry_subtype}"

        bonus = 0.0

        # Use the full compatibility matrix from unit_profiles
        for defender in defenders:
            defender_type = defender.unit_type.lower() if defender.unit_type else ""
            defender_subtype = getattr(defender, 'infantry_subtype', None)
            if defender_subtype:
                defender_type = f"{defender_type}_{defender_subtype}"

            # Get bonus from compatibility matrix
            matrix_bonus = get_compatibility_bonus(attacker_type, defender_type)
            bonus = max(bonus, matrix_bonus)

        # Also check legacy bonuses for backward compatibility
        if "infantry" in attacker_type or "atgm" in attacker_type:
            if infantry_subtype == "atgm":
                for defender in defenders:
                    if "armor" in defender.unit_type.lower():
                        bonus = max(bonus, cls.UNIT_TYPE_BONUSES["atgm_vs_armor"])
            elif infantry_subtype == "sniper":
                bonus = max(bonus, cls.UNIT_TYPE_BONUSES["sniper_vs_inf"])
            elif infantry_subtype == "scout":
                bonus = max(bonus, 0.1)
        elif "armor" in attacker_type:
            for defender in defenders:
                if "infantry" in defender.unit_type.lower():
                    bonus = max(bonus, cls.UNIT_TYPE_BONUSES["armor_vs_inf"])
        elif "artillery" in attacker_type:
            bonus = max(bonus, cls.UNIT_TYPE_BONUSES.get("artillery_vs_all", 0.15))
        elif "air_defense" in attacker_type:
            for defender in defenders:
                if "air" in defender.unit_type.lower() or "helo" in defender.unit_type.lower():
                    bonus = max(bonus, cls.UNIT_TYPE_BONUSES["air_defense_vs_air"])

        return bonus


class RuleEngine:
    def __init__(self, db: Session):
        self.db = db
        self.commander_order_service = CommanderOrderService()
        self.reporting_system = ReportingSystem()

    def adjudicate_turn(self, game_id: int) -> dict:
        """Execute one turn of adjudication"""
        game = self.db.query(Game).filter(Game.id == game_id).first()
        if not game:
            return {"error": "Game not found"}

        # Load CommanderOrder from DB and configure reporting system
        commander_order = self.db.query(CommanderOrder).filter(
            CommanderOrder.game_id == game_id,
            CommanderOrder.status == "active"
        ).first()

        if commander_order and commander_order.reporting_requirements:
            self.reporting_system.set_reporting_requirements(commander_order.reporting_requirements)
            logger.info(f"[REPORTING] Configured with {len(commander_order.reporting_requirements)} requirements")

        # Record current turn for reporting system
        current_turn = game.current_turn

        turn = self.db.query(Turn).filter(
            Turn.game_id == game_id,
            Turn.turn_number == game.current_turn
        ).first()

        if not turn:
            turn = Turn(
                game_id=game_id,
                turn_number=game.current_turn,
                time=game.current_time,
                weather=game.weather,
                phase="adjudication"
            )
            self.db.add(turn)
            self.db.commit()
            self.db.refresh(turn)

        # Get all player orders for this turn
        orders = self.db.query(Order).filter(
            Order.game_id == game_id,
            Order.turn_id == turn.id
        ).all()

        results = []

        # Process orders in sequence
        for order in orders:
            result = self._adjudicate_order(order)
            results.append(result)

        # Process enemy AI (simple random movement for now)
        enemy_events = self._process_enemy_activities(game_id)

        # Process reconnaissance - player units observe enemy positions
        recon_events = self._process_reconnaissance(game_id)

        # Process enemy reconnaissance - what enemy knows about player units
        enemy_recon_events = self._process_enemy_reconnaissance(game_id)

        # Check game end conditions
        game_end = self._check_game_end_conditions(game_id)

        # Check reporting compliance and get commander inquiries
        inquiries = self.reporting_system.check_reporting_compliance(current_turn)
        reporting_summary = self.reporting_system.get_reporting_summary()

        # Update turn phase
        turn.phase = "complete"
        game.current_turn += 1
        game.current_time = self._advance_time(game.current_time)

        # If game ended, update game status
        if game_end["ended"]:
            game.is_active = False

        self.db.commit()

        return {
            "turn": turn.turn_number,
            "results": results,
            "events": enemy_events,
            "recon_events": recon_events,
            "enemy_recon_events": enemy_recon_events,
            "next_time": game.current_time,
            "game_ended": game_end["ended"],
            "game_end_reason": game_end["reason"],
            "commander_inquiries": [
                {
                    "id": i.inquiry_id,
                    "subject": i.subject,
                    "question": i.question,
                    "urgency": i.urgency
                }
                for i in inquiries
            ],
            "reporting_summary": reporting_summary
        }

    def _check_game_end_conditions(self, game_id: int) -> dict:
        """Check if game end conditions are met"""
        game = self.db.query(Game).filter(Game.id == game_id).first()
        if not game:
            return {"ended": False, "reason": None}

        # Check turn limit (50 turns)
        if game.current_turn >= 50:
            logger.info(f"[GAME END] Turn limit reached: {game.current_turn}")
            return {"ended": True, "reason": "turn_limit"}

        # Get all units
        units = self.db.query(Unit).filter(Unit.game_id == game_id).all()

        # Count player and enemy units that are not destroyed
        player_units = [u for u in units if u.side == "player" and u.status != UnitStatus.DESTROYED]
        enemy_units = [u for u in units if u.side == "enemy" and u.status != UnitStatus.DESTROYED]

        # Check for annihilation
        if not player_units:
            logger.info("[GAME END] Player forces annihilated")
            return {"ended": True, "reason": "player_annihilated"}
        if not enemy_units:
            logger.info("[GAME END] Enemy forces annihilated")
            return {"ended": True, "reason": "enemy_annihilated"}

        return {"ended": False, "reason": None}

    def _calculate_max_movement(self, unit: Unit) -> float:
        """Calculate maximum movement points for a unit based on type and supply status.

        Base movement by unit type:
        - infantry: 3.0 cells
        - armor: 4.0 cells
        - artillery: 2.5 cells
        - air_defense: 2.5 cells
        - reconnaissance: 4.5 cells
        - support: 3.0 cells
        - default: 3.0 cells

        Supply modifiers:
        - FULL: 100%
        - DEPLETED: 50%
        - EXHAUSTED: 0% (cannot move)
        """
        # Base movement by unit type
        unit_type_movement = {
            "infantry": 3.0,
            "armor": 4.0,
            "artillery": 2.5,
            "air_defense": 2.5,
            "reconnaissance": 4.5,
            "recon": 4.5,
            "atgm": 2.5,
            "scout": 3.5,
            "sniper": 2.5,
            "support": 3.0,
            "transport_helo": 5.0,
            "attack_helo": 4.0,
            "aircraft": 8.0,
            "uav": 6.0,
        }

        # Get base movement for unit type
        normalized_type = unit.unit_type.lower() if unit.unit_type else "default"
        base_movement = unit_type_movement.get(normalized_type, 3.0)

        # Apply fuel modifier
        fuel_modifier = {
            SupplyLevel.FULL: 1.0,
            SupplyLevel.DEPLETED: 0.5,
            SupplyLevel.EXHAUSTED: 0.0,
        }.get(unit.fuel, 1.0)

        # Apply readiness modifier
        readiness_modifier = {
            SupplyLevel.FULL: 1.0,
            SupplyLevel.DEPLETED: 0.7,
            SupplyLevel.EXHAUSTED: 0.0,
        }.get(unit.readiness, 1.0)

        max_movement = base_movement * fuel_modifier * readiness_modifier

        logger.debug(f"[MOVE] {unit.name}: base={base_movement}, fuel={unit.fuel.value}, readiness={unit.readiness.value} -> max={max_movement:.2f}")

        return max_movement

    def _get_advance_direction(self, game: Game, side: str) -> dict:
        """Get advance direction for a side from scenario configuration.

        Returns:
            dict: Direction vector with 'x' and 'y' keys (e.g., {"x": 1, "y": 0})
                  Defaults to {"x": 1, "y": 0} for player, {"x": -1, "y": 0} for enemy
                  if scenario does not have advance_directions configured.
        """
        if not game or not game.scenario_id:
            # Fallback to default directions
            return {"x": 1, "y": 0} if side == "player" else {"x": -1, "y": 0}

        scenario = get_scenario(game.scenario_id)
        if not scenario:
            # Fallback to default directions
            return {"x": 1, "y": 0} if side == "player" else {"x": -1, "y": 0}

        advance_directions = scenario.get("advance_directions", {})
        direction = advance_directions.get(side)

        if direction:
            return direction

        # Fallback to default directions
        return {"x": 1, "y": 0} if side == "player" else {"x": -1, "y": 0}

    def _get_terrain_cost(self, game: Game, x: int, y: int) -> float:
        """Get terrain movement cost at a position."""
        if not game.terrain_data:
            return 1.0  # Default plain terrain cost

        terrain_map = game.terrain_data.get("map", {})
        terrain_key = f"{x},{y}"

        if terrain_key not in terrain_map:
            return 1.0  # Default plain terrain cost

        terrain_str = terrain_map[terrain_key]
        try:
            terrain = TerrainType(terrain_str)
        except ValueError:
            return 1.0

        # Get movement cost from TerrainEffects
        effects = TerrainEffects()
        terrain_effect = effects.TERRAIN_EFFECTS.get(terrain)
        if terrain_effect:
            return terrain_effect.movement_cost

        return 1.0

    def _calculate_path_cost(self, game: Game, from_x: float, from_y: float, to_x: float, to_y: float) -> float:
        """Calculate movement cost from current position to target considering terrain.

        Uses Manhattan distance with terrain cost averaging.
        """
        # Simple distance calculation (Manhattan)
        dx = abs(to_x - from_x)
        dy = abs(to_y - from_y)
        base_distance = dx + dy

        if base_distance == 0:
            return 0.0

        # If no terrain data, return base distance
        if not game.terrain_data:
            return base_distance

        # Calculate average terrain cost along path
        terrain_effects = TerrainEffects()
        terrain_map = game.terrain_data.get("map", {})
        total_cost = 0.0
        steps = max(int(base_distance), 1)

        for i in range(steps):
            # Interpolate position along path
            ratio = (i + 1) / steps
            check_x = int(from_x + (to_x - from_x) * ratio)
            check_y = int(from_y + (to_y - from_y) * ratio)

            # Clamp to map bounds
            check_x = max(0, min(game.map_width - 1, check_x))
            check_y = max(0, min(game.map_height - 1, check_y))

            # Get terrain cost at this position
            terrain = terrain_map.get(f"{check_x},{check_y}", "plain")
            try:
                terrain_type = TerrainType(terrain)
            except ValueError:
                terrain_type = TerrainType.PLAIN

            cost = terrain_effects.TERRAIN_EFFECTS.get(terrain_type, terrain_effects.TERRAIN_EFFECTS[TerrainType.PLAIN]).movement_cost

            # If water (impassable), return infinity
            if cost >= 999.0:
                return 999.0

            total_cost += cost

        avg_cost = total_cost / steps
        path_cost = base_distance * avg_cost

        logger.debug(f"[MOVE] Path cost: ({from_x:.1f},{from_y:.1f}) -> ({to_x:.1f},{to_y:.1f}): distance={base_distance}, avg_terrain={avg_cost:.2f}, total_cost={path_cost:.2f}")

        return path_cost

    def _find_reachable_position(self, game: Game, unit: Unit, target_x: float, target_y: float, max_movement: float) -> tuple[float, float]:
        """Find the furthest reachable position towards target within movement limit.

        Returns:
            Tuple of (reachable_x, reachable_y)
        """
        old_x, old_y = unit.x, unit.y

        # Check if target is already reachable directly
        direct_cost = self._calculate_path_cost(game, old_x, old_y, target_x, target_y)

        if direct_cost <= max_movement:
            # Target is directly reachable
            logger.debug(f"[MOVE] {unit.name}: Target directly reachable (cost={direct_cost:.2f} <= max={max_movement:.2f})")
            return target_x, target_y

        # Need to find furthest reachable point along the path
        # Binary search for max distance
        low, high = 0.0, 1.0

        for _ in range(10):  # 10 iterations for precision
            mid = (low + high) / 2
            intermediate_x = old_x + (target_x - old_x) * mid
            intermediate_y = old_y + (target_y - old_y) * mid

            cost = self._calculate_path_cost(game, old_x, old_y, intermediate_x, intermediate_y)

            if cost <= max_movement:
                low = mid
            else:
                high = mid

        # Calculate final position
        final_x = old_x + (target_x - old_x) * low
        final_y = old_y + (target_y - old_y) * low

        final_cost = self._calculate_path_cost(game, old_x, old_y, final_x, final_y)

        logger.debug(f"[MOVE] {unit.name}: Partial movement to ({final_x:.1f},{final_y:.1f}), cost={final_cost:.2f}, ratio={low:.2f}")

        return final_x, final_y

    def _adjudicate_order(self, order: Order) -> dict:
        # Fetch unit for this order
        unit = self.db.query(Unit).filter(Unit.id == order.unit_id).first()
        if not unit:
            logger.warning(f"[ORDER] Order {order.id}: Unit not found")
            return {"order_id": order.id, "outcome": "failed", "reason": "Unit not found"}

        # Fetch game for terrain access
        game = self.db.query(Game).filter(Game.id == order.game_id).first()

        changes = []
        outcome = "success"  # Default outcome

        # Process based on order type
        if order.order_type == OrderType.MOVE:
            # Check if unit can move (fuel not exhausted)
            can_move = unit.fuel != SupplyLevel.EXHAUSTED

            if not can_move:
                logger.warning(f"[MOVE] {unit.name}: Cannot move - fuel exhausted")
                outcome = "failed"
                changes.append({
                    "type": "move_blocked",
                    "target": unit.id,
                    "reason": "fuel_exhausted",
                    "message": "燃料が枯渇しているため移動できません"
                })
            elif order.location_x is not None and order.location_y is not None:
                # Target location specified - calculate reachable position
                old_x, old_y = unit.x, unit.y
                target_x, target_y = order.location_x, order.location_y

                # Calculate max movement points
                max_movement = self._calculate_max_movement(unit)

                if max_movement <= 0:
                    logger.warning(f"[MOVE] {unit.name}: Cannot move - no movement points")
                    outcome = "failed"
                    changes.append({
                        "type": "move_blocked",
                        "target": unit.id,
                        "reason": "no_movement_points",
                        "message": "移動力がありません"
                    })
                else:
                    # Find reachable position considering terrain
                    new_x, new_y = self._find_reachable_position(
                        game, unit, target_x, target_y, max_movement
                    )

                    # Check if reached target or partial movement
                    distance_to_target = abs(target_x - old_x) + abs(target_y - old_y)
                    actual_distance = abs(new_x - old_x) + abs(new_y - old_y)

                    unit.x = new_x
                    unit.y = new_y

                    # Determine outcome based on whether target was reached
                    if actual_distance >= distance_to_target - 0.01:
                        outcome = "success"
                        logger.info(f"[MOVE] {unit.name}: ({old_x:.1f},{old_y:.1f}) -> ({unit.x:.1f},{unit.y:.1f}) [target reached]")
                    else:
                        outcome = "partial"
                        logger.info(f"[MOVE] {unit.name}: ({old_x:.1f},{old_y:.1f}) -> ({unit.x:.1f},{unit.y:.1f}) [partial: {actual_distance:.1f}/{distance_to_target:.1f}]")

                    changes.append({
                        "type": "move",
                        "target": unit.id,
                        "field": "position",
                        "old_value": {"x": old_x, "y": old_y},
                        "new_value": {"x": unit.x, "y": unit.y},
                        "outcome": outcome,
                        "target_requested": {"x": target_x, "y": target_y},
                        "movement_cost": actual_distance,
                        "max_movement": max_movement
                    })
            else:
                # No specific location - move forward by 1 cell towards enemy side
                # Default: move forward (direction defined by scenario)
                old_x, old_y = unit.x, unit.y

                # Calculate max movement points
                max_movement = self._calculate_max_movement(unit)

                if max_movement <= 0:
                    logger.warning(f"[MOVE] {unit.name}: Cannot move - no movement points")
                    outcome = "failed"
                    changes.append({
                        "type": "move_blocked",
                        "target": unit.id,
                        "reason": "no_movement_points",
                        "message": "移動力がありません"
                    })
                else:
                    # Default movement: move forward 1 cell
                    move_distance = min(1, max_movement)

                    # Get direction from scenario configuration
                    direction = self._get_advance_direction(game, unit.side)
                    dir_x = direction.get("x", 1)
                    dir_y = direction.get("y", 0)

                    new_x = unit.x + (move_distance * dir_x)
                    new_y = unit.y + (move_distance * dir_y)
                    new_x = max(0, min(game.map_width - 1, new_x))
                    new_y = max(0, min(game.map_height - 1, new_y))

                    unit.x = new_x
                    unit.y = new_y
                    outcome = "success"

                    changes.append({
                        "type": "move",
                        "target": unit.id,
                        "field": "position",
                        "old_value": {"x": old_x, "y": old_y},
                        "new_value": {"x": unit.x, "y": unit.y},
                        "outcome": outcome,
                        "movement_cost": move_distance,
                        "max_movement": max_movement
                    })
                    logger.info(f"[MOVE] {unit.name}: ({old_x:.1f},{old_y:.1f}) -> ({unit.x:.1f},{unit.y:.1f}) [default]")

        elif order.order_type == OrderType.ATTACK:
            # Get target units from order
            target_ids = order.target_units or []
            target_units = []
            invalid_target_ids = []
            out_of_range_targets = []

            # Validate target existence
            for tid in target_ids:
                target = self.db.query(Unit).filter(Unit.id == tid).first()
                if target:
                    target_units.append(target)
                else:
                    invalid_target_ids.append(tid)

            # Log warnings for invalid targets
            if invalid_target_ids:
                logger.warning(f"[COMBAT] {unit.name}: Invalid target IDs: {invalid_target_ids}")
                changes.append({
                    "type": "warning",
                    "target": unit.id,
                    "field": "target_validation",
                    "message": f"Invalid target IDs: {invalid_target_ids}",
                    "code": "INVALID_TARGET"
                })

            # If no valid targets, fail the attack
            if not target_units:
                logger.warning(f"[COMBAT] {unit.name}: No valid targets for attack")
                outcome = "failed"
                changes.append({
                    "type": "combat",
                    "target": unit.id,
                    "field": "status",
                    "old_value": unit.status,
                    "new_value": unit.status,
                    "message": "No valid targets - attack failed"
                })
                return {
                    "order_id": order.id,
                    "outcome": outcome,
                    "changes": changes
                }

            # Validate target range
            attacker_profile = get_unit_profile(unit.unit_type)
            max_attack_range = attacker_profile.max_range if attacker_profile else 10

            for target in target_units:
                distance = math.sqrt((unit.x - target.x)**2 + (unit.y - target.y)**2)
                if distance > max_attack_range:
                    out_of_range_targets.append({
                        "id": target.id,
                        "name": target.name,
                        "distance": round(distance, 1),
                        "max_range": max_attack_range
                    })

            if out_of_range_targets:
                logger.warning(f"[COMBAT] {unit.name}: Out of range targets: {out_of_range_targets}")
                changes.append({
                    "type": "warning",
                    "target": unit.id,
                    "field": "range_validation",
                    "message": f"Targets out of range: {[t['name'] for t in out_of_range_targets]}",
                    "code": "OUT_OF_RANGE",
                    "details": out_of_range_targets
                })

            target_names = [t.name for t in target_units]
            logger.info(f"[COMBAT] {unit.name} attacks {target_names} (targets: {len(target_units)})")

            # Get game state for criteria evaluation
            game = self.db.query(Game).filter(Game.id == order.game_id).first()
            game_state = {
                "turn": game.current_turn if game else 1,
                "weather": game.weather if game else "clear"
            }

            # Use structured adjudication criteria
            outcome, criteria_results = AdjudicationCriteria.evaluate_order(
                order, unit, target_units, game_state,
                weather=game.weather if game else "clear",
                time=game.current_time if game else "06:00"
            )

            logger.info(f"[COMBAT] Result: {outcome}")

            # Apply combat effects based on 5-stage outcome
            # 1. perfect_success: Defender takes heavy damage, attacker takes no damage
            # 2. success: Defender takes moderate damage
            # 3. partial: Both sides take light damage
            # 4. failed: Attacker takes light damage (counter-attack)
            # 5. major_failed: Attacker takes moderate damage (heavy counter-attack)

            if outcome == "perfect_success":
                # Attacker wins decisively: defender takes severe damage
                for target in target_units:
                    old_status = target.status
                    if target.status == UnitStatus.INTACT:
                        target.status = UnitStatus.MEDIUM_DAMAGE
                    elif target.status == UnitStatus.LIGHT_DAMAGE:
                        target.status = UnitStatus.HEAVY_DAMAGE
                    elif target.status == UnitStatus.MEDIUM_DAMAGE:
                        target.status = UnitStatus.DESTROYED
                        # Report unit destroyed
                        if target.side == "player":
                            self.reporting_system.add_event("unit_destroyed", {
                                "unit_id": target.id,
                                "unit_name": target.name,
                                "unit_type": target.unit_type,
                                "priority": "high"
                            })
                            logger.info(f"[REPORTING] Player unit destroyed: {target.name}")
                    logger.info(f"[COMBAT] {target.name}: {old_status.value} -> {target.status.value}")
                # Attacker takes no damage
            elif outcome == "success":
                # Attacker wins: defender takes moderate damage
                for target in target_units:
                    old_status = target.status
                    if target.status == UnitStatus.INTACT:
                        target.status = UnitStatus.LIGHT_DAMAGE
                    elif target.status == UnitStatus.LIGHT_DAMAGE:
                        target.status = UnitStatus.MEDIUM_DAMAGE
                    elif target.status == UnitStatus.MEDIUM_DAMAGE:
                        target.status = UnitStatus.HEAVY_DAMAGE
                    logger.info(f"[COMBAT] {target.name}: {old_status.value} -> {target.status.value}")
            elif outcome == "partial":
                # Both sides take some damage
                for target in target_units:
                    old_status = target.status
                    if target.status == UnitStatus.INTACT:
                        target.status = UnitStatus.LIGHT_DAMAGE
                    logger.info(f"[COMBAT] {target.name}: {old_status.value} -> {target.status.value}")
                # Attacker also takes light damage from counter-attack
                if unit.status == UnitStatus.INTACT:
                    old_status = unit.status
                    unit.status = UnitStatus.LIGHT_DAMAGE
                    logger.info(f"[COMBAT] {unit.name} (attacker): {old_status.value} -> {unit.status.value}")
            elif outcome == "failed":
                # Defender counter-attacks successfully: attacker takes light damage
                if unit.status == UnitStatus.INTACT:
                    unit.status = UnitStatus.LIGHT_DAMAGE
                elif unit.status == UnitStatus.LIGHT_DAMAGE:
                    unit.status = UnitStatus.MEDIUM_DAMAGE
            elif outcome == "major_failed":
                # Defender counter-attacks decisively: attacker takes moderate damage
                if unit.status == UnitStatus.INTACT:
                    unit.status = UnitStatus.MEDIUM_DAMAGE
                elif unit.status == UnitStatus.LIGHT_DAMAGE:
                    unit.status = UnitStatus.HEAVY_DAMAGE
                elif unit.status == UnitStatus.MEDIUM_DAMAGE:
                    unit.status = UnitStatus.DESTROYED
                    # Report unit destroyed
                    if unit.side == "player":
                        self.reporting_system.add_event("unit_destroyed", {
                            "unit_id": unit.id,
                            "unit_name": unit.name,
                            "unit_type": unit.unit_type,
                            "priority": "high"
                        })
                        logger.info(f"[REPORTING] Player unit destroyed: {unit.name}")

            changes.append({
                "type": "combat",
                "target": unit.id,
                "field": "status",
                "old_value": unit.status,
                "new_value": unit.status,
                "target_statuses": [(t.id, t.status.value if t.status else None) for t in target_units],
                "criteria_results": criteria_results
            })

        elif order.order_type == OrderType.DEFEND:
            outcome = "success"
            # Defend order - no status change, no healing

        elif order.order_type == OrderType.RECON:
            outcome = "success"
            # Recon increases visibility

        elif order.order_type == OrderType.RETREAT:
            # Move backwards (opposite of advance direction) and reduce status
            old_x, old_y = unit.x, unit.y

            # Get direction from scenario configuration (retreat is opposite of advance)
            direction = self._get_advance_direction(game, unit.side)
            dir_x = direction.get("x", 1)
            dir_y = direction.get("y", 0)

            # Retreat is the opposite direction of advance
            retreat_distance = 2
            new_x = unit.x - (retreat_distance * dir_x)
            new_y = unit.y - (retreat_distance * dir_y)
            new_x = max(0, min(game.map_width - 1, new_x))
            new_y = max(0, min(game.map_height - 1, new_y))

            unit.x = new_x
            unit.y = new_y

            changes.append({
                "type": "retreat",
                "target": unit.id,
                "field": "position",
                "old_value": {"x": old_x, "y": old_y},
                "new_value": {"x": unit.x, "y": unit.y}
            })
            outcome = "success"

        else:
            outcome = "success"

        # Consume supplies based on order type
        if order.order_type == OrderType.ATTACK:
            self._consume_supplies(unit)
        elif order.order_type == OrderType.MOVE:
            # Reduced consumption for movement
            self._consume_supplies_minimal(unit)
        # DEFEND, RECON, RETREAT - no consumption

        return {
            "order_id": order.id,
            "outcome": outcome,
            "changes": changes
        }

    def _resolve_combat(self, unit: Unit) -> str:
        """Simple combat resolution"""
        if unit.ammo == SupplyLevel.EXHAUSTED:
            return "failed"

        # Random outcome based on unit status
        if unit.status == UnitStatus.INTACT:
            outcome = random.choices(
                ["success", "partial", "failed"],
                weights=[0.6, 0.3, 0.1]
            )[0]
        elif unit.status == UnitStatus.LIGHT_DAMAGE:
            outcome = random.choices(
                ["success", "partial", "failed"],
                weights=[0.4, 0.4, 0.2]
            )[0]
        else:
            outcome = "failed"

        # Apply damage
        if outcome in ["partial", "failed"]:
            status_order = [UnitStatus.LIGHT_DAMAGE, UnitStatus.MEDIUM_DAMAGE, UnitStatus.HEAVY_DAMAGE, UnitStatus.DESTROYED]
            current_idx = status_order.index(unit.status) if unit.status in status_order else 0
            if current_idx < len(status_order) - 1:
                unit.status = status_order[current_idx + 1]

        return outcome

    def _consume_supplies(self, unit: Unit):
        """Consume ammo, fuel, readiness"""
        if unit.ammo == SupplyLevel.FULL:
            unit.ammo = SupplyLevel.DEPLETED
        elif unit.ammo == SupplyLevel.DEPLETED:
            unit.ammo = SupplyLevel.EXHAUSTED

        if unit.fuel == SupplyLevel.FULL:
            unit.fuel = SupplyLevel.DEPLETED
        elif unit.fuel == SupplyLevel.DEPLETED:
            unit.fuel = SupplyLevel.EXHAUSTED

        if unit.readiness == SupplyLevel.FULL:
            unit.readiness = SupplyLevel.DEPLETED
        elif unit.readiness == SupplyLevel.DEPLETED:
            unit.readiness = SupplyLevel.EXHAUSTED

    def _consume_supplies_minimal(self, unit: Unit):
        """Minimal supply consumption for movement (reduced from full combat consumption)"""
        # Only fuel consumed for movement
        if unit.fuel == SupplyLevel.FULL:
            unit.fuel = SupplyLevel.DEPLETED
        elif unit.fuel == SupplyLevel.DEPLETED:
            unit.fuel = SupplyLevel.EXHAUSTED

    def _process_enemy_activities(self, game_id: int) -> list:
        """Process enemy unit activities with tactical behavior using unit profiles"""
        import math

        enemy_units = self.db.query(Unit).filter(
            Unit.game_id == game_id,
            Unit.side == "enemy",
            Unit.status != UnitStatus.DESTROYED
        ).all()

        player_units = self.db.query(Unit).filter(
            Unit.game_id == game_id,
            Unit.side == "player",
            Unit.status != UnitStatus.DESTROYED
        ).all()

        logger.info(f"[ENEMY] Processing {len(enemy_units)} enemy units vs {len(player_units)} player units")

        # Get game state for weather/time penalties
        game = self.db.query(Game).filter(Game.id == game_id).first()
        weather = game.weather if game else "clear"
        time_str = game.current_time if game else "12:00"
        map_width = getattr(game, 'map_width', 50)
        map_height = getattr(game, 'map_height', 50)

        # Build occupancy grid to track occupied cells (for collision avoidance)
        occupied_cells = {}
        for unit in enemy_units:
            cell_key = (int(unit.x), int(unit.y))
            if cell_key not in occupied_cells:
                occupied_cells[cell_key] = []
            occupied_cells[cell_key].append(unit.id)
        for unit in player_units:
            cell_key = (int(unit.x), int(unit.y))
            if cell_key not in occupied_cells:
                occupied_cells[cell_key] = []
            occupied_cells[cell_key].append(unit.id)

        # Calculate numerical strength
        enemy_count = len(enemy_units)
        player_count = len(player_units)
        enemy_superior = enemy_count > player_count

        events = []

        for unit in enemy_units:
            # Skip destroyed units
            if unit.status == UnitStatus.DESTROYED:
                logger.debug(f"[ENEMY] Skipping destroyed unit: {unit.name}")
                continue

            # Get unit behavior profile
            profile = get_unit_profile(unit.unit_type)

            # Find nearest player unit
            nearest_player = None
            min_distance = float('inf')
            for p_unit in player_units:
                dist = math.sqrt((unit.x - p_unit.x)**2 + (unit.y - p_unit.y)**2)
                if dist < min_distance:
                    min_distance = dist
                    nearest_player = p_unit

            # Apply behavior profile logic
            dx, dy = 0, 0
            max_move = 3.0  # Maximum movement per turn (cells)

            # Check if unit should avoid combat (UAV, recon, transport)
            if profile.avoid_combat:
                # Move away from player or stay in place
                if nearest_player and min_distance < profile.preferred_range:
                    dx = -(nearest_player.x - unit.x) * 0.15
                    dy = -(nearest_player.y - unit.y) * 0.15
                else:
                    dx, dy = 0, 0

            # Check if unit is recon only
            elif profile.recon_only:
                # Move toward player but maintain distance
                if nearest_player and min_distance > profile.max_range:
                    dx = (nearest_player.x - unit.x) * 0.2
                    dy = (nearest_player.y - unit.y) * 0.2
                elif nearest_player and min_distance < profile.preferred_range:
                    dx = -(nearest_player.x - unit.x) * 0.1
                    dy = -(nearest_player.y - unit.y) * 0.1

            # Artillery should stay rear and maintain distance
            elif profile.stay_rear:
                if nearest_player and min_distance < profile.min_range:
                    # Too close - move away
                    dx = -(nearest_player.x - unit.x) * 0.15
                    dy = -(nearest_player.y - unit.y) * 0.15
                elif nearest_player and min_distance > profile.max_range:
                    # Too far - move closer
                    dx = (nearest_player.x - unit.x) * 0.15
                    dy = (nearest_player.y - unit.y) * 0.15
                else:
                    # Stay at current position
                    dx, dy = 0, 0

            # Air defense should prioritize staying at range
            elif profile.stay_at_range:
                if nearest_player and min_distance < profile.min_range:
                    # Too close - move away
                    dx = -(nearest_player.x - unit.x) * 0.2
                    dy = -(nearest_player.y - unit.y) * 0.2
                elif nearest_player and min_distance > profile.preferred_range:
                    # Move closer to preferred range
                    dx = (nearest_player.x - unit.x) * 0.15
                    dy = (nearest_player.y - unit.y) * 0.15
                elif nearest_player and min_distance <= profile.preferred_range:
                    # In range - can attack (will be handled by ExCon AI)
                    events.append({
                        "type": "enemy_attack_available",
                        "unit_id": unit.id,
                        "unit_name": unit.name,
                        "target_id": nearest_player.id,
                        "distance": min_distance,
                        "status": "in_range"
                    })
                    dx, dy = 0, 0

            # Default: ground units with should_advance logic
            else:
                # Check if unit should advance based on ammo status
                should_advance = profile.should_advance
                if profile.max_advance_when_low_ammo and unit.ammo == SupplyLevel.EXHAUSTED:
                    should_advance = False

                if nearest_player and min_distance <= 5:
                    # Player in range - create attack order
                    events.append({
                        "type": "enemy_attack_available",
                        "unit_id": unit.id,
                        "unit_name": unit.name,
                        "target_id": nearest_player.id,
                        "distance": min_distance,
                        "status": "will_attack_next_turn"
                    })
                    # Move slightly toward target
                    dx = (nearest_player.x - unit.x) * 0.15 if should_advance else 0
                    dy = (nearest_player.y - unit.y) * 0.15 if should_advance else 0
                elif nearest_player:
                    # Approach player unit with dispersion coefficient
                    base_dx = (nearest_player.x - unit.x) * 0.2 if should_advance else 0
                    base_dy = (nearest_player.y - unit.y) * 0.2 if should_advance else 0

                    # Apply dispersion - random offset based on unit ID for consistency
                    dispersion = 1.0  # Reduced dispersion radius
                    unit_dispersion = (unit.id % 10) / 10.0  # Unit-specific dispersion factor
                    dx = base_dx + random.uniform(-dispersion * unit_dispersion, dispersion * unit_dispersion) if should_advance else random.uniform(-0.3, 0.3)
                    dy = base_dy + random.uniform(-dispersion * unit_dispersion, dispersion * unit_dispersion) if should_advance else random.uniform(-0.3, 0.3)
                else:
                    # No player units - random movement toward center
                    dx = random.uniform(-1, 1)
                    dy = random.uniform(-1, 1)

            # Cap movement to max_move cells
            move_magnitude = math.sqrt(dx**2 + dy**2) if dx != 0 or dy != 0 else 0
            if move_magnitude > max_move:
                scale = max_move / move_magnitude
                dx *= scale
                dy *= scale

            # Apply movement with collision avoidance
            new_x = max(0, min(map_width, unit.x + dx))
            new_y = max(0, min(map_height, unit.y + dy))

            # Check if new position conflicts with other units
            # Try to find a nearby unoccupied cell
            best_x, best_y = new_x, new_y
            min_conflict_score = self._count_conflicts(new_x, new_y, occupied_cells, unit.id)

            # Try nearby cells if there's a conflict
            if min_conflict_score > 0:
                for offset_x in [-2, -1, 0, 1, 2]:
                    for offset_y in [-2, -1, 0, 1, 2]:
                        if offset_x == 0 and offset_y == 0:
                            continue
                        test_x = max(0, min(map_width, new_x + offset_x))
                        test_y = max(0, min(map_height, new_y + offset_y))
                        conflict_score = self._count_conflicts(test_x, test_y, occupied_cells, unit.id)
                        if conflict_score < min_conflict_score:
                            min_conflict_score = conflict_score
                            best_x, best_y = test_x, test_y
                            if conflict_score == 0:
                                break
                    if min_conflict_score == 0:
                        break

            new_x, new_y = best_x, best_y

            if new_x != unit.x or new_y != unit.y:
                # Update occupancy grid for this unit's movement
                old_cell = (int(unit.x), int(unit.y))
                new_cell = (int(new_x), int(new_y))
                if old_cell in occupied_cells and unit.id in occupied_cells[old_cell]:
                    occupied_cells[old_cell].remove(unit.id)
                if new_cell not in occupied_cells:
                    occupied_cells[new_cell] = []
                occupied_cells[new_cell].append(unit.id)

                old_x, old_y = unit.x, unit.y
                logger.info(f"[ENEMY] {unit.name} ({unit.unit_type}): ({old_x:.1f},{old_y:.1f}) -> ({new_x:.1f},{new_y:.1f})" +
                           (f" [target: {nearest_player.name}]" if nearest_player else ""))

                events.append({
                    "type": "enemy_move",
                    "unit_id": unit.id,
                    "unit_name": unit.name,
                    "old_position": {"x": old_x, "y": old_y},
                    "new_position": {"x": new_x, "y": new_y},
                    "target": nearest_player.name if nearest_player else None,
                    "behavior": unit.unit_type
                })
                unit.x = new_x
                unit.y = new_y

        self.db.commit()
        return events

    def _count_conflicts(self, x: float, y: float, occupied_cells: dict, unit_id: int) -> int:
        """Count how many units are at the EXACT same position (not adjacent)"""
        cell_x, cell_y = int(x), int(y)
        conflict_count = 0

        # Only check SAME cell - adjacent cells are fine
        if (cell_x, cell_y) in occupied_cells:
            for uid in occupied_cells[(cell_x, cell_y)]:
                if uid != unit_id:
                    conflict_count += 1

        return conflict_count

    def process_enemy_orders(self, game_id: int, excon_orders: dict) -> list:
        """
        Process enemy orders generated by AI (ExCon).

        Args:
            game_id: The game ID
            excon_orders: Dict with 'orders' key containing list of enemy orders

        Returns:
            List of processed order results
        """
        game = self.db.query(Game).filter(Game.id == game_id).first()
        if not game:
            return []

        # Get the turn that was just processed (current_turn - 1, since it was already incremented)
        turn = self.db.query(Turn).filter(
            Turn.game_id == game_id,
            Turn.turn_number == game.current_turn - 1
        ).first()

        if not turn:
            # Fallback: try current_turn if the above doesn't exist
            turn = self.db.query(Turn).filter(
                Turn.game_id == game_id,
                Turn.turn_number == game.current_turn
            ).first()

        if not turn:
            return []

        results = []
        orders_list = excon_orders.get("orders", [])

        for order_data in orders_list:
            try:
                unit_id = order_data.get("unit_id")
                if isinstance(unit_id, str):
                    # Try to find unit by name if ID is string
                    unit = self.db.query(Unit).filter(
                        Unit.game_id == game_id,
                        Unit.side == "enemy",
                        Unit.name.ilike(f"%{unit_id}%")
                    ).first()
                else:
                    unit = self.db.query(Unit).filter(Unit.id == unit_id).first()

                if not unit:
                    results.append({
                        "type": "enemy_order",
                        "outcome": "failed",
                        "reason": f"Unit not found: {unit_id}"
                    })
                    continue

                # Parse order type
                order_type_str = order_data.get("order_type", "move").lower()
                try:
                    order_type = OrderType[order_type_str.upper()]
                except KeyError:
                    order_type = OrderType.MOVE

                # Create Order record for enemy unit
                target = order_data.get("target", {})
                location_x = target.get("x")
                location_y = target.get("y")

                enemy_order = Order(
                    game_id=game_id,
                    unit_id=unit.id,
                    turn_id=turn.id,
                    order_type=order_type,
                    target_units=order_data.get("target_units", []),
                    intent=order_data.get("intent", f"AI generated {order_type_str} order"),
                    location_x=location_x,
                    location_y=location_y,
                    location_name=order_data.get("location_name"),
                    parameters=order_data.get("parameters", {})
                )
                self.db.add(enemy_order)
                self.db.commit()
                self.db.refresh(enemy_order)

                # Process the enemy order
                result = self._adjudicate_order(enemy_order)
                result["unit_id"] = unit.id
                result["unit_name"] = unit.name
                results.append(result)

            except Exception as e:
                results.append({
                    "type": "enemy_order",
                    "outcome": "error",
                    "reason": str(e)
                })

        return results

    def _advance_time(self, current_time: str) -> str:
        """Advance game time by 1 hour"""
        hour = int(current_time.split(":")[0])
        hour = (hour + 1) % 24
        return f"{hour:02d}:00"

    def get_game_state(self, game_id: int) -> dict:
        """Get current game state"""
        game = self.db.query(Game).filter(Game.id == game_id).first()
        if not game:
            return {"error": "Game not found"}

        units = self.db.query(Unit).filter(Unit.game_id == game_id).all()

        # Import terrain and weather services
        from app.services.terrain import generate_map_terrain, get_terrain_display_info
        from app.services.weather_effects import WeatherEffects

        # Use persisted terrain data if available, otherwise generate (for backward compatibility)
        if game.terrain_data:
            terrain_map = game.terrain_data.get("map", {})
            terrain_info = game.terrain_data.get("info", get_terrain_display_info())
        else:
            # Fallback: generate terrain (legacy behavior for games without persisted terrain)
            map_width = getattr(game, 'map_width', 50)
            map_height = getattr(game, 'map_height', 50)
            terrain_map = generate_map_terrain(map_width, map_height)
            terrain_info = get_terrain_display_info()

        # Get weather effects
        weather_service = WeatherEffects()
        weather_service.set_weather(game.weather or "clear")
        weather_service.set_time(game.current_time or "12:00")
        weather_data = weather_service.get_current_effects_summary()

        # Determine if it's night
        hour = int((game.current_time or "12:00").split(":")[0])
        is_night = hour < 6 or hour >= 18

        return {
            "game_id": game.id,
            "name": game.name,
            "turn": game.current_turn,
            "time": game.current_time,
            "date": getattr(game, 'current_date', '1985-11-22'),
            "weather": game.weather,
            "phase": game.phase,
            "is_night": is_night,
            "terrain": terrain_map,
            "terrain_info": terrain_info,
            "weather_effects": weather_data,
            "units": [
                {
                    "id": u.id,
                    "name": u.name,
                    "type": u.unit_type,
                    "side": u.side,
                    "x": u.x,
                    "y": u.y,
                    "status": u.status.value if u.status else None,
                    "ammo": u.ammo.value if u.ammo else None,
                    "fuel": u.fuel.value if u.fuel else None,
                    "readiness": u.readiness.value if u.readiness else None,
                    "strength": u.strength,
                    "infantry_subtype": getattr(u, 'infantry_subtype', None),
                    "recon_value": getattr(u, 'recon_value', 1.0),
                    "visibility_range": getattr(u, 'visibility_range', 3),
                    "observation_confidence": getattr(u, 'observation_confidence', None),
                    "last_observed_turn": getattr(u, 'last_observed_turn', None),
                    # Extended reconnaissance fields
                    "confidence_score": getattr(u, 'confidence_score', None),
                    "estimated_x": getattr(u, 'estimated_x', None),
                    "estimated_y": getattr(u, 'estimated_y', None),
                    "position_accuracy": getattr(u, 'position_accuracy', 0),
                    "last_known_type": getattr(u, 'last_known_type', None),
                    "observation_sources": getattr(u, 'observation_sources', None),
                }
                for u in units
            ]
        }

    def _save_player_knowledge(self, game_id: int, enemy_unit: Unit) -> None:
        """Save or update player knowledge about an enemy unit to PlayerKnowledge table.

        This method persists observation data to PlayerKnowledge table for use in
        the player view (Fog of War). It creates new entries or updates existing ones.
        """
        # Check if knowledge already exists for this unit
        existing_knowledge = self.db.query(PlayerKnowledge).filter(
            PlayerKnowledge.game_id == game_id,
            PlayerKnowledge.unit_id == enemy_unit.id
        ).first()

        # Get observation data from the enemy unit
        confidence = getattr(enemy_unit, 'observation_confidence', None)
        confidence_score = getattr(enemy_unit, 'confidence_score', 0)
        last_observed_turn = getattr(enemy_unit, 'last_observed_turn', None)
        position_accuracy = getattr(enemy_unit, 'position_accuracy', 0)
        last_known_type = getattr(enemy_unit, 'last_known_type', enemy_unit.unit_type)

        if existing_knowledge:
            # Update existing knowledge if we have a better observation
            if confidence_score > existing_knowledge.confidence_score:
                existing_knowledge.x = enemy_unit.x
                existing_knowledge.y = enemy_unit.y
                existing_knowledge.confidence = confidence
                existing_knowledge.confidence_score = confidence_score
                existing_knowledge.last_observed_turn = last_observed_turn
                existing_knowledge.position_accuracy = position_accuracy
                existing_knowledge.interpreted_type = last_known_type
                existing_knowledge.interpreted_side = enemy_unit.side
                logger.debug(f"[PlayerKnowledge] Updated knowledge for enemy unit {enemy_unit.id}: confidence={confidence}, score={confidence_score}")
            else:
                # Only update position if the observation is more recent and has reasonable confidence
                if last_observed_turn and last_observed_turn > (existing_knowledge.last_observed_turn or 0):
                    existing_knowledge.x = enemy_unit.x
                    existing_knowledge.y = enemy_unit.y
                    existing_knowledge.last_observed_turn = last_observed_turn
        else:
            # Create new knowledge entry
            new_knowledge = PlayerKnowledge(
                game_id=game_id,
                unit_id=enemy_unit.id,
                x=enemy_unit.x,
                y=enemy_unit.y,
                confidence=confidence or "unknown",
                confidence_score=confidence_score or 0,
                last_observed_turn=last_observed_turn,
                position_accuracy=position_accuracy,
                interpreted_type=last_known_type,
                interpreted_side=enemy_unit.side
            )
            self.db.add(new_knowledge)
            logger.debug(f"[PlayerKnowledge] Created new knowledge for enemy unit {enemy_unit.id}: confidence={confidence}, score={confidence_score}")

    def _process_reconnaissance(self, game_id: int) -> list:
        """Process reconnaissance - player units observe enemy positions

        Extended reconnaissance system:
        - Player recon units have a recon_value and visibility_range
        - Units within visibility_range are "observed"
        - Weather and time affect visibility (fog, rain, night, twilight)
        - Terrain affects recon (forests, mountains provide cover)
        - Extended confidence levels: confirmed (90-100%), estimated (50-89%), unknown (0-49%)
        - Tracks observation sources and position accuracy
        """
        import math

        # Get player units with reconnaissance capability (exclude destroyed)
        player_units = self.db.query(Unit).filter(
            Unit.game_id == game_id,
            Unit.side == "player",
            Unit.status != UnitStatus.DESTROYED
        ).all()

        # Get enemy units (exclude destroyed)
        enemy_units = self.db.query(Unit).filter(
            Unit.game_id == game_id,
            Unit.side == "enemy",
            Unit.status != UnitStatus.DESTROYED
        ).all()

        logger.info(f"[RECON] Player units: {len(player_units)}, Enemy units: {len(enemy_units)}")

        # Get weather for visibility penalties
        game = self.db.query(Game).filter(Game.id == game_id).first()
        weather = game.weather if game else "clear"
        time_str = game.current_time if game else "12:00"

        # Apply extended weather penalties
        weather_penalty = 1.0
        weather_description = ""
        if weather in ["fog", "heavy_rain"]:
            weather_penalty = 0.5
            weather_description = "fog_heavy_rain"
        elif weather == "light_rain":
            weather_penalty = 0.7
            weather_description = "light_rain"
        elif weather == "cloudy":
            weather_penalty = 0.9
            weather_description = "cloudy"

        # Apply extended time penalties
        hour = int(time_str.split(":")[0])
        is_dawn = 5 <= hour < 7
        is_dusk = 17 <= hour < 19
        is_night = hour < 5 or hour >= 20
        is_twilight = is_dawn or is_dusk

        time_description = "clear"
        if is_night:
            weather_penalty *= 0.5
            time_description = "night"
        elif is_twilight:
            weather_penalty *= 0.8
            time_description = "twilight"

        events = []
        observed_enemies = {}

        # Each player unit observes enemies within its range
        for p_unit in player_units:
            # Get unit's recon value (default 1.0, scout +0.2, UAV +0.5)
            recon_value = getattr(p_unit, 'recon_value', 1.0)
            visibility_range = getattr(p_unit, 'visibility_range', 3)

            # Infantry subtype bonuses
            infantry_subtype = getattr(p_unit, 'infantry_subtype', None)
            if infantry_subtype == "scout":
                recon_value += 0.2
                visibility_range += 1
            elif infantry_subtype == "sniper":
                recon_value += 0.1

            # Apply weather penalty to visibility
            effective_range = int(visibility_range * weather_penalty)
            effective_recon = recon_value * weather_penalty

            # Calculate confidence score (0-100)
            # Base confidence from recon value, modified by distance
            base_confidence = min(100, int(effective_recon * 60))

            # Check each enemy unit
            for e_unit in enemy_units:
                distance = math.sqrt((p_unit.x - e_unit.x)**2 + (p_unit.y - e_unit.y)**2)

                if distance <= effective_range:
                    # Enemy is observed
                    if e_unit.id not in observed_enemies:
                        observed_enemies[e_unit.id] = {
                            "enemy_unit": e_unit,
                            "best_confidence": 0,
                            "sources": [],
                            "positions": []
                        }

                    # Distance penalty: closer = more accurate
                    distance_factor = max(0.5, 1.0 - (distance / effective_range) * 0.5)

                    # Calculate confidence score
                    confidence_score = int(base_confidence * distance_factor)
                    confidence_score = min(100, confidence_score)

                    # Determine confidence level
                    if confidence_score >= 70:
                        confidence = "confirmed"
                    elif confidence_score >= 30:
                        confidence = "estimated"
                    else:
                        confidence = "unknown"

                    # Update best observation if this is better
                    if confidence_score > observed_enemies[e_unit.id]["best_confidence"]:
                        observed_enemies[e_unit.id]["best_confidence"] = confidence_score
                        observed_enemies[e_unit.id]["best_confidence_level"] = confidence

                    # Track observation source
                    observed_enemies[e_unit.id]["sources"].append({
                        "observer_id": p_unit.id,
                        "observer_name": p_unit.name,
                        "confidence_score": confidence_score,
                        "distance": distance,
                    })

                    # Track position
                    observed_enemies[e_unit.id]["positions"].append({
                        "x": e_unit.x,
                        "y": e_unit.y,
                        "observer_id": p_unit.id
                    })

                    # Calculate position accuracy (cells of error)
                    position_accuracy = max(0, 5 - int(confidence_score / 20))

                    logger.info(f"[RECON] {p_unit.name} observed {e_unit.name}: {confidence} ({confidence_score}%) at distance {distance:.1f}")

                    # Add event to reporting system
                    if distance <= 2.0:
                        # Enemy in contact range - trigger reporting requirement
                        self.reporting_system.add_event("enemy_contact", {
                            "enemy_unit_id": e_unit.id,
                            "enemy_name": e_unit.name,
                            "observer_unit_id": p_unit.id,
                            "distance": distance,
                            "priority": "high" if distance <= 1.0 else "normal"
                        })
                        logger.info(f"[REPORTING] Enemy contact detected: {e_unit.name} at distance {distance:.1f}")

                    events.append({
                        "type": "enemy_observed",
                        "enemy_unit_id": e_unit.id,
                        "enemy_name": e_unit.name,
                        "observer_unit_id": p_unit.id,
                        "observer_name": p_unit.name,
                        "position": {"x": e_unit.x, "y": e_unit.y},
                        "confidence": confidence,
                        "confidence_score": confidence_score,
                        "distance": distance,
                        "recon_value": recon_value,
                        "effective_recon": effective_recon,
                        "weather_penalty": weather_penalty,
                        "weather": weather_description,
                        "time": time_description,
                        "position_accuracy": position_accuracy,
                    })

        # Update enemy unit observation status with extended info
        for e_unit in enemy_units:
            if e_unit.id in observed_enemies:
                obs_data = observed_enemies[e_unit.id]
                best_conf = obs_data["best_confidence"]

                # Store extended observation info
                setattr(e_unit, 'last_observed_turn', game.current_turn if game else 1)
                setattr(e_unit, 'observation_confidence', obs_data.get("best_confidence_level", "confirmed"))
                setattr(e_unit, 'confidence_score', best_conf)

                # Calculate position accuracy
                position_accuracy = max(0, 5 - int(best_conf / 20))
                setattr(e_unit, 'position_accuracy', position_accuracy)

                # Store last known type
                setattr(e_unit, 'last_known_type', e_unit.unit_type)

                # Store observation sources
                sources_json = [{"observer_id": s["observer_id"], "confidence": s["confidence_score"]}
                               for s in obs_data["sources"]]
                setattr(e_unit, 'observation_sources', sources_json)
            else:
                # Enemy not observed this turn - keep previous confidence if any
                prev_confidence = getattr(e_unit, 'observation_confidence', None)
                if prev_confidence is None:
                    setattr(e_unit, 'observation_confidence', 'unknown')
                    setattr(e_unit, 'confidence_score', 0)

                # Reduce confidence for previously known but now unobserved units
                if prev_confidence in ["confirmed", "estimated"]:
                    current_score = getattr(e_unit, 'confidence_score', 50) or 50
                    # Decay confidence over turns not observed
                    turns_since = (game.current_turn if game else 1) - (getattr(e_unit, 'last_observed_turn', 0) or 0)
                    decayed_score = max(10, current_score - turns_since * 15)
                    setattr(e_unit, 'confidence_score', decayed_score)

                    # Downgrade confidence level
                    if decayed_score < 30:
                        setattr(e_unit, 'observation_confidence', 'unknown')

                # Save to PlayerKnowledge table for player view
                self._save_player_knowledge(game_id, e_unit)

        self.db.commit()

        return events

    def _process_enemy_reconnaissance(self, game_id: int) -> list:
        """Process enemy reconnaissance - what the enemy knows about player units

        This implements the concealment system where:
        - Enemy recon units observe player positions
        - Player units not observed retain true positions
        - Player units observed by enemy have their positions tracked
        - This knowledge affects what the player sees (Fog of War)
        """
        import math

        # Get enemy units with reconnaissance capability (exclude destroyed)
        enemy_units = self.db.query(Unit).filter(
            Unit.game_id == game_id,
            Unit.side == "enemy",
            Unit.status != UnitStatus.DESTROYED
        ).all()

        # Get player units (exclude destroyed)
        player_units = self.db.query(Unit).filter(
            Unit.game_id == game_id,
            Unit.side == "player",
            Unit.status != UnitStatus.DESTROYED
        ).all()

        # Get game state
        game = self.db.query(Game).filter(Game.id == game_id).first()
        if not game:
            return []

        weather = game.weather if game else "clear"
        time_str = game.current_time if game else "12:00"

        # Apply weather penalties (same as player recon)
        weather_penalty = 1.0
        if weather in ["fog", "heavy_rain"]:
            weather_penalty = 0.5
        elif weather == "light_rain":
            weather_penalty = 0.7

        hour = int(time_str.split(":")[0])
        is_night = hour < 5 or hour >= 20
        if is_night:
            weather_penalty *= 0.5

        events = []
        known_player_units = {}

        # Each enemy unit observes players within range
        for e_unit in enemy_units:
            # Get enemy's recon capability
            recon_value = getattr(e_unit, 'recon_value', 0.8)  # Enemy slightly lower default
            visibility_range = getattr(e_unit, 'visibility_range', 2)

            # UAV and recon units have better recon
            if "uav" in e_unit.unit_type.lower() or "recon" in e_unit.unit_type.lower():
                recon_value += 0.3
                visibility_range += 2

            # Apply weather penalty
            effective_range = int(visibility_range * weather_penalty)
            effective_recon = recon_value * weather_penalty

            # Check each player unit
            for p_unit in player_units:
                distance = math.sqrt((e_unit.x - p_unit.x)**2 + (e_unit.y - p_unit.y)**2)

                if distance <= effective_range:
                    if p_unit.id not in known_player_units:
                        known_player_units[p_unit.id] = {
                            "player_unit": p_unit,
                            "best_confidence": 0,
                            "sources": []
                        }

                    # Calculate confidence
                    confidence_score = min(100, int(effective_recon * 60 * (1.0 - distance / effective_range)))

                    if confidence_score > known_player_units[p_unit.id]["best_confidence"]:
                        known_player_units[p_unit.id]["best_confidence"] = confidence_score
                        known_player_units[p_unit.id]["best_confidence_level"] = "confirmed" if confidence_score >= 70 else "estimated"

                    known_player_units[p_unit.id]["sources"].append({
                        "observer_id": e_unit.id,
                        "observer_name": e_unit.name,
                        "confidence_score": confidence_score
                    })

        # Update EnemyKnowledge for tracked player units
        for p_unit_id, data in known_player_units.items():
            # Find or create EnemyKnowledge record
            knowledge = self.db.query(EnemyKnowledge).filter(
                EnemyKnowledge.game_id == game_id,
                EnemyKnowledge.player_unit_id == p_unit_id
            ).first()

            if not knowledge:
                knowledge = EnemyKnowledge(
                    game_id=game_id,
                    player_unit_id=p_unit_id
                )
                self.db.add(knowledge)

            # Update knowledge
            p_unit = data["player_unit"]
            knowledge.known_x = p_unit.x
            knowledge.known_y = p_unit.y
            knowledge.confidence = data.get("best_confidence_level", "estimated")
            knowledge.confidence_score = data["best_confidence"]
            knowledge.last_observed_turn = game.current_turn if game else 1
            knowledge.interpreted_type = p_unit.unit_type
            knowledge.position_accuracy = max(0, 5 - int(data["best_confidence"] / 20))

            events.append({
                "type": "enemy_observed_player",
                "player_unit_id": p_unit_id,
                "player_unit_name": p_unit.name,
                "enemy_known_position": {"x": p_unit.x, "y": p_unit.y},
                "confidence": knowledge.confidence,
                "confidence_score": data["best_confidence"],
                "sources": len(data["sources"])
            })

        # Mark unobserved player units as unknown to enemy
        for p_unit in player_units:
            if p_unit.id not in known_player_units:
                # Check if we have previous knowledge
                knowledge = self.db.query(EnemyKnowledge).filter(
                    EnemyKnowledge.game_id == game_id,
                    EnemyKnowledge.player_unit_id == p_unit.id
                ).first()

                if knowledge:
                    # Enemy previously knew but lost track
                    knowledge.confidence = "unknown"
                    knowledge.confidence_score = max(0, (knowledge.confidence_score or 50) - 20)
                # If no knowledge record, enemy simply doesn't know

        self.db.commit()
        return events
