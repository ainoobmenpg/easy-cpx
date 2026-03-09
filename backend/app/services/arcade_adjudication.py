# Arcade CPX - Simplified 2D6 Rule Engine
import random
from typing import Optional
from sqlalchemy.orm import Session
from app.models import Game, GameMode, ArcadeUnit, OrderType
from app.services.event_deck import EventDeckService
from app.services.rng_service import RNGService
from app.services.structured_logging import get_structured_logger


# VP (Victory Point) values for destroying enemy units
VP_VALUES = {
    "armor": 3,
    "infantry": 2,
    "artillery": 4,
    "air_defense": 3,
    "recon": 2,
    "support": 1,
}


# Arcade unit stats table
ARCADE_UNIT_STATS = {
    "infantry": {"attack": 3, "defense": 3, "move": 2, "hp": 3},
    "armor": {"attack": 4, "defense": 4, "move": 3, "hp": 4},
    "artillery": {"attack": 5, "defense": 2, "move": 2, "hp": 2},
    "air_defense": {"attack": 2, "defense": 4, "move": 2, "hp": 3},
    "recon": {"attack": 2, "defense": 2, "move": 4, "hp": 2},
    "support": {"attack": 1, "defense": 3, "move": 3, "hp": 4},
}

# Terrain movement costs
TERRAIN_MOVE_COSTS = {
    "plain": 1,
    "forest": 2,
    "urban": 2,
    "mountain": 4,
    "water": 999,  # Impassable
}


# CCIR (Commander's Critical Information Requirements) default checklist
DEFAULT_CCIS_CHECKLIST = {
    "isr": [
        {"id": "isr_1", "description": "Enemy disposition confirmed", "required": True},
        {"id": "isr_2", "description": "Terrain recon completed", "required": False},
    ],
    "fires": [
        {"id": "fires_1", "description": "Fire support available", "required": True},
        {"id": "fires_2", "description": "SEAD coverage confirmed", "required": False},
    ],
    "sustainment": [
        {"id": "sus_1", "description": "Ammo status adequate", "required": True},
        {"id": "sus_2", "description": "Fuel status adequate", "required": True},
    ],
    "c2": [
        {"id": "c2_1", "description": "Communications operational", "required": True},
        {"id": "c2_2", "description": "Command authority confirmed", "required": True},
    ],
}


class ArcadeAdjudication:
    """Simplified 2D6 rule engine for Arcade mode"""

    # Event deck draw chance per turn (20%)
    EVENT_DRAW_CHANCE = 0.2

    def __init__(self, db_session: Session, seed: Optional[int] = None, game_id: Optional[int] = None):
        self.db = db_session
        # Initialize RNG service for reproducibility
        self.rng = RNGService(game_id=game_id, initial_seed=seed)
        # Initialize event deck service
        self.event_deck = EventDeckService(random_seed=seed)
        # Structured logger
        self.logger = get_structured_logger()

    def roll_2d6(self, context: Optional[str] = None) -> int:
        """Roll 2 six-sided dice"""
        die1, die2, total = self.rng.roll_2d6(context=context)
        return total

    def get_modifiers(self, unit: ArcadeUnit, game: Game) -> int:
        """Calculate all modifiers for a unit"""
        mod = 0

        # Strength modifier
        if unit.strength >= 8:
            mod += 1
        elif unit.strength <= 4:
            mod -= 1

        # Supply check (simplified)
        if not unit.can_attack:
            mod -= 1

        return mod

    def get_ccir_checklist(self, game: Game) -> dict:
        """Get or initialize CCIR checklist for a game.

        Returns:
            dict with keys: isr, fires, sustainment, c2 (each a list of CCIR items)
        """
        # Try to get from game ccir_data, or initialize default
        if game.ccir_data and 'ccir_checklist' in game.ccir_data:
            return game.ccir_data['ccir_checklist']

        # Initialize with defaults
        checklist = {}
        for category, items in DEFAULT_CCIS_CHECKLIST.items():
            checklist[category] = [
                {
                    "id": item["id"],
                    "description": item["description"],
                    "required": item["required"],
                    "satisfied": False,
                }
                for item in items
            ]

        # Save to game.ccir_data
        if not game.ccir_data:
            game.ccir_data = {}
        game.ccir_data['ccir_checklist'] = checklist
        self.db.commit()

        return checklist

    def update_ccir_status(self, game: Game, unit: ArcadeUnit) -> None:
        """Update CCIR checklist based on unit actions this turn."""
        checklist = self.get_ccir_checklist(game)

        # ISR checks - satisfied if player has units (basic ISR capability)
        for item in checklist["isr"]:
            if not item["satisfied"]:
                item["satisfied"] = True

        # Fires checks - satisfied if unit can attack (has ammo)
        for item in checklist["fires"]:
            if item["id"] == "fires_1" and not item["satisfied"]:
                item["satisfied"] = unit.can_attack

        # Sustainment checks - satisfied if unit has supplies
        for item in checklist["sustainment"]:
            if item["id"] == "sus_1" and not item["satisfied"]:
                item["satisfied"] = unit.can_attack
            elif item["id"] == "sus_2" and not item["satisfied"]:
                item["satisfied"] = unit.can_move

        # C2 checks - always satisfied in Arcade mode
        for item in checklist["c2"]:
            if not item["satisfied"]:
                item["satisfied"] = True

        # Save back to game ccir_data
        if not game.ccir_data:
            game.ccir_data = {}
        game.ccir_data['ccir_checklist'] = checklist
        self.db.commit()
        self.db.commit()

    def evaluate_ccir_compliance(self, game: Game) -> dict:
        """Evaluate CCIR compliance and return combat modifier.

        Rules:
        - 100% compliance: +2 attack modifier (well-prepared)
        - 75-99% compliance: +1 attack modifier
        - 50-74% compliance: 0 modifier (neutral)
        - 25-49% compliance: -1 attack modifier
        - 0-24% compliance: -2 attack modifier (poor preparation)

        Returns:
            dict with compliance percentage, category results, and combat modifier
        """
        checklist = self.get_ccir_checklist(game)

        category_results = {}
        total_passed = 0
        total_required = 0

        for category, items in checklist.items():
            passed = sum(1 for item in items if item["satisfied"])
            required = sum(1 for item in items if item.get("required", False))
            total_passed += passed
            total_required += max(required, 1)  # Avoid division by zero

            category_results[category] = {
                "passed": passed,
                "total": len(items)
            }

        # Calculate overall compliance percentage
        total_items = sum(len(items) for items in checklist.values())
        compliance = (total_passed / total_items * 100) if total_items > 0 else 0

        # Determine combat modifier based on compliance
        if compliance >= 100:
            combat_modifier = 2
        elif compliance >= 75:
            combat_modifier = 1
        elif compliance >= 50:
            combat_modifier = 0
        elif compliance >= 25:
            combat_modifier = -1
        else:
            combat_modifier = -2

        # Collect failed required checks
        failed_checks = []
        for category, items in checklist.items():
            for item in items:
                if item.get("required", False) and not item["satisfied"]:
                    failed_checks.append(f"{category}: {item['description']}")

        return {
            "overall_compliance": round(compliance, 1),
            "category_results": category_results,
            "combat_modifier": combat_modifier,
            "failed_checks": failed_checks
        }

    def resolve_attack(
        self, attacker: ArcadeUnit, defender: ArcadeUnit, game: Game
    ) -> dict:
        """Resolve combat between two units using 2D6"""
        attacker_stats = ARCADE_UNIT_STATS.get(attacker.unit_type, ARCADE_UNIT_STATS["infantry"])
        defender_stats = ARCADE_UNIT_STATS.get(defender.unit_type, ARCADE_UNIT_STATS["infantry"])

        # Calculate attack and defense totals
        attack_mod = self.get_modifiers(attacker, game)
        defense_mod = self.get_modifiers(defender, game)

        # Apply STRIKE bonus if attacker used STRIKE this turn
        strike_bonus = 0
        if attacker.strike_used_this_turn:
            strike_bonus = 2
            attack_mod += strike_bonus

        # Apply CCIR compliance modifier
        ccir_evaluation = self.evaluate_ccir_compliance(game)
        ccir_modifier = ccir_evaluation.get("combat_modifier", 0)
        attack_mod += ccir_modifier

        # Roll dice with context for logging
        attack_die1, attack_die2, _ = self.rng.roll_2d6(context=f"attack_{attacker.id}")
        defense_die1, defense_die2, _ = self.rng.roll_2d6(context=f"defense_{defender.id}")

        attack_roll = attack_die1 + attack_die2 + attacker_stats["attack"] + attack_mod
        defense_roll = defense_die1 + defense_die2 + defender_stats["defense"] + defense_mod

        # Determine result
        diff = attack_roll - defense_roll

        if diff <= -3:
            result = "CRITICAL_FAIL"
            damage_to_attacker = 1
            damage_to_defender = 0
        elif diff == -2:
            result = "FAIL"
            damage_to_attacker = 0
            damage_to_defender = 0
        elif diff == -1:
            result = "PARTIAL"
            damage_to_attacker = 0
            damage_to_defender = 1
        elif diff == 0:
            result = "PARTIAL"
            damage_to_attacker = 0
            damage_to_defender = 1
        elif diff == 1:
            result = "SUCCESS"
            damage_to_attacker = 0
            damage_to_defender = 2
        elif diff == 2:
            result = "GREAT"
            damage_to_attacker = 0
            damage_to_defender = 3
        else:
            result = "CRITICAL"
            damage_to_attacker = 0
            damage_to_defender = 4

        # Log structured combat data
        self.logger.log_combat(
            attacker_id=attacker.id,
            defender_id=defender.id,
            terrain="plain",  # Simplified - could get from game map
            attack_roll=attack_roll,
            defense_roll=defense_roll,
            net_modifier=diff,
            outcome=result,
            damage={
                "to_attacker": damage_to_attacker,
                "to_defender": damage_to_defender,
            },
            modifiers={
                "attack_mod": attack_mod,
                "defense_mod": defense_mod,
                "strike_bonus": strike_bonus,
                "ccir_modifier": ccir_modifier,
            },
            roll_details={
                "attack_dice": [attack_die1, attack_die2],
                "defense_dice": [defense_die1, defense_die2],
            },
            seed=self.rng.current_seed,
        )

        return {
            "result": result,
            "attack_roll": attack_roll,
            "defense_roll": defense_roll,
            "damage_to_attacker": damage_to_attacker,
            "damage_to_defender": damage_to_defender,
            "strike_bonus": strike_bonus,
            "ccir_modifier": ccir_modifier,
            "ccir_compliance": ccir_evaluation.get("overall_compliance", 0),
        }

    def resolve_move(
        self, unit: ArcadeUnit, target_x: int, target_y: int, terrain: dict
    ) -> dict:
        """Calculate movement using 2D6"""
        unit_stats = ARCADE_UNIT_STATS.get(unit.unit_type, ARCADE_UNIT_STATS["infantry"])
        max_cells = unit_stats["move"]

        # Calculate distance
        dx = abs(target_x - unit.x)
        dy = abs(target_y - unit.y)
        distance = dx + dy

        # Check terrain costs
        terrain_type = terrain.get(f"{target_x},{target_y}", "plain")
        terrain_cost = TERRAIN_MOVE_COSTS.get(terrain_type, 1)

        # Roll for movement
        move_roll = self.roll_2d6()

        # Calculate effective movement
        if move_roll >= 7:
            effective_move = max_cells
        elif move_roll >= 5:
            effective_move = max(1, max_cells - 1)
        elif move_roll >= 3:
            effective_move = max(1, max_cells - 2)
        else:
            effective_move = 0

        # Check if move is possible
        if distance > effective_move * terrain_cost:
            return {
                "result": "PARTIAL",
                "new_x": unit.x,
                "new_y": unit.y,
                "distance": distance,
                "effective_move": effective_move,
            }
        else:
            return {
                "result": "SUCCESS",
                "new_x": target_x,
                "new_y": target_y,
                "distance": distance,
                "effective_move": effective_move,
            }

    def resolve_defend(self, unit: ArcadeUnit, game: Game) -> dict:
        """Defense bonus for DEFEND command"""
        unit_stats = ARCADE_UNIT_STATS.get(unit.unit_type, ARCADE_UNIT_STATS["infantry"])
        defense_roll = self.roll_2d6()

        if defense_roll >= 8:
            defense_bonus = 2
        elif defense_roll >= 5:
            defense_bonus = 1
        else:
            defense_bonus = 0

        return {
            "result": "SUCCESS" if defense_bonus > 0 else "PARTIAL",
            "defense_bonus": defense_bonus,
            "total_defense": unit_stats["defense"] + defense_bonus,
        }

    def resolve_recon(self, unit: ArcadeUnit, game: Game) -> dict:
        """Reconnaissance action"""
        unit_stats = ARCADE_UNIT_STATS.get(unit.unit_type, ARCADE_UNIT_STATS["recon"])
        recon_roll = self.roll_2d6()

        # Recon reveals units in range
        recon_range = unit_stats["move"]
        if recon_roll >= 10:
            recon_range += 1

        return {
            "result": "SUCCESS" if recon_roll >= 7 else "PARTIAL",
            "recon_range": recon_range,
            "recon_roll": recon_roll,
        }

    def resolve_supply(self, unit: ArcadeUnit) -> dict:
        """Supply action"""
        supply_roll = self.roll_2d6()

        if supply_roll >= 8:
            unit.can_attack = True
            unit.can_move = True
            return {"result": "SUCCESS", "restored": "both"}
        elif supply_roll >= 5:
            unit.can_attack = True
            return {"result": "PARTIAL", "restored": "attack"}
        else:
            return {"result": "FAIL", "restored": "none"}

    def resolve_strike(self, unit: ArcadeUnit, all_units: list, game: Game) -> dict:
        """STRIKE special action - +2 attack modifier, consumes 1 strike token.

        Rules:
        - Effect: +2 attack modifier for next attack
        - Constraint: Cannot use consecutively (next turn attack blocked)
        - Remaining: Starts with 3, decreases with use
        - Condition: Must be adjacent to enemy to use
        """
        # Check if unit has strike tokens remaining
        if unit.strike_remaining is None or unit.strike_remaining <= 0:
            return {
                "result": "FAIL",
                "reason": "no_strikes_remaining",
                "message": f"{unit.name} has no STRIKE tokens remaining"
            }

        # Check if already used this turn (cannot use consecutively)
        if unit.strike_used_this_turn:
            return {
                "result": "FAIL",
                "reason": "already_used_this_turn",
                "message": f"{unit.name} already used STRIKE this turn"
            }

        # Check if next turn attack is blocked (consecutive use prevention)
        if unit.strike_next_attack_blocked:
            return {
                "result": "FAIL",
                "reason": "attack_blocked_next_turn",
                "message": f"{unit.name} cannot attack next turn due to previous STRIKE"
            }

        # Check if unit is adjacent to enemy (activation condition)
        enemy_units = [u for u in all_units if u.side != unit.side and u.side in ("player", "enemy")]
        is_adjacent = False
        for enemy in enemy_units:
            distance = abs(enemy.x - unit.x) + abs(enemy.y - unit.y)
            if distance <= 1:  # Adjacent means distance of 1 (orthogonal or diagonal)
                is_adjacent = True
                break

        if not is_adjacent:
            return {
                "result": "FAIL",
                "reason": "not_adjacent_to_enemy",
                "message": f"{unit.name} must be adjacent to enemy to use STRIKE"
            }

        # Apply STRIKE effect
        unit.strike_remaining = (unit.strike_remaining or 3) - 1
        unit.strike_used_this_turn = True
        unit.strike_next_attack_blocked = True  # Cannot attack next turn

        return {
            "result": "SUCCESS",
            "attack_modifier": 2,
            "strikes_remaining": unit.strike_remaining,
            "message": f"{unit.name} uses STRIKE! +2 attack modifier applied. Cannot attack next turn.",
            "effect": "next_attack_bonus"
        }

    def resolve_wait(self, unit: ArcadeUnit) -> dict:
        """WAIT command - no effect in Arcade mode.

        The unit simply passes its turn without any action.
        This is a valid command but provides no tactical benefit.
        """
        return {
            "result": "SUCCESS",
            "message": f"{unit.name} waits - no effect",
            "note": "WAIT has no tactical effect in Arcade mode"
        }

    def execute_enemy_turn(self, game_id: int, terrain_data: dict) -> list:
        """Execute enemy AI turn.

        Priority:
        1. Attack adjacent player units
        2. Advance toward closest player unit
        3. Defend if in unfavorable position
        """
        # Get all enemy and player units (ArcadeUnit uses strength > 0 to check if alive)
        enemy_units = self.db.query(ArcadeUnit).filter(
            ArcadeUnit.game_id == game_id,
            ArcadeUnit.side == "enemy",
            ArcadeUnit.strength > 0
        ).all()

        player_units = self.db.query(ArcadeUnit).filter(
            ArcadeUnit.game_id == game_id,
            ArcadeUnit.side == "player",
            ArcadeUnit.strength > 0
        ).all()

        if not enemy_units or not player_units:
            return []

        enemy_orders = []

        for enemy in enemy_units:
            # Check if enemy can act
            if not enemy.can_move and not enemy.can_attack:
                continue

            # Find closest player unit
            closest_player = None
            min_dist = float('inf')

            for player in player_units:
                dist = abs(enemy.x - player.x) + abs(enemy.y - player.y)
                if dist < min_dist:
                    min_dist = dist
                    closest_player = player

            if not closest_player:
                continue

            # Priority 1: Attack if adjacent and can attack
            if min_dist == 1 and enemy.can_attack:
                enemy_orders.append({
                    "unit_id": enemy.id,
                    "order_type": OrderType.ATTACK.value,
                    "target_id": closest_player.id,
                })
            # Priority 2: Advance or Defend based on position
            elif enemy.can_move:
                # Determine move direction toward player
                dx = 1 if closest_player.x > enemy.x else -1 if closest_player.x < enemy.x else 0
                dy = 1 if closest_player.y > enemy.y else -1 if closest_player.y < enemy.y else 0

                new_x = enemy.x + dx
                new_y = enemy.y + dy

                # Check if move is valid (within bounds)
                if 0 <= new_x < 12 and 0 <= new_y < 8:
                    enemy_orders.append({
                        "unit_id": enemy.id,
                        "order_type": OrderType.MOVE.value,
                        "location_x": new_x,
                        "location_y": new_y,
                    })
                else:
                    # Can't advance, defend instead
                    enemy_orders.append({
                        "unit_id": enemy.id,
                        "order_type": OrderType.DEFEND.value,
                    })

        return enemy_orders

    def get_game_state(self, game_id: int) -> dict:
        """Get current game state for Arcade mode"""
        game = self.db.query(Game).filter(Game.id == game_id).first()
        if not game:
            return {"error": "Game not found"}

        units = self.db.query(ArcadeUnit).filter(ArcadeUnit.game_id == game_id).all()

        return {
            "game_id": game.id,
            "turn": game.current_turn,
            "mode": "arcade",
            "score": {
                "player": game.player_score or 0,
                "enemy": game.enemy_score or 0,
            },
            "units": [
                {
                    "id": u.id,
                    "name": u.name,
                    "unit_type": u.unit_type,
                    "side": u.side,
                    "x": u.x,
                    "y": u.y,
                    "strength": u.strength,
                    "can_move": u.can_move,
                    "can_attack": u.can_attack,
                    "has_supplied": u.has_supplied,
                    "strike_remaining": u.strike_remaining,
                    "strike_used_this_turn": u.strike_used_this_turn,
                    "strike_next_attack_blocked": u.strike_next_attack_blocked,
                }
                for u in units
            ],
        }

    def get_reachable_positions(self, unit_id: int) -> dict:
        """Get all reachable positions for a unit (for movement preview).

        Returns:
            {
                "unit_id": int,
                "unit_name": str,
                "max_move": int,
                "reachable": [{"x": int, "y": int, "can_reach": bool, "terrain": str}, ...],
            }
        """
        unit = self.db.query(ArcadeUnit).filter(ArcadeUnit.id == unit_id).first()
        if not unit:
            return {"error": "Unit not found"}

        # Get game for terrain data
        game = self.db.query(Game).filter(Game.id == unit.game_id).first()
        if not game:
            return {"error": "Game not found"}

        unit_stats = ARCADE_UNIT_STATS.get(unit.unit_type, ARCADE_UNIT_STATS["infantry"])
        max_cells = unit_stats["move"]

        # For preview, use max movement as expected value
        expected_move = max_cells

        # Get terrain data
        terrain_data = game.terrain_data or {}

        # Calculate reachable positions on the grid (12x8)
        reachable = []
        for x in range(12):
            for y in range(8):
                dx = abs(x - unit.x)
                dy = abs(y - unit.y)
                distance = dx + dy

                # Skip current position
                if distance == 0:
                    continue

                terrain_type = terrain_data.get(f"{x},{y}", "plain")
                terrain_cost = TERRAIN_MOVE_COSTS.get(terrain_type, 1)
                total_cost = distance * terrain_cost

                can_reach = total_cost <= expected_move
                reachable.append({
                    "x": x,
                    "y": y,
                    "can_reach": can_reach,
                    "terrain": terrain_type,
                    "distance": distance,
                    "cost": total_cost
                })

        return {
            "unit_id": unit.id,
            "unit_name": unit.name,
            "unit_type": unit.unit_type,
            "current_x": unit.x,
            "current_y": unit.y,
            "max_move": max_cells,
            "expected_move": expected_move,
            "reachable": reachable,
        }

    def adjudicate_turn(self, game_id: int, orders: list) -> dict:
        """Main turn adjudication for Arcade mode"""
        game = self.db.query(Game).filter(Game.id == game_id).first()
        if not game or game.game_mode != GameMode.ARCADE:
            return {"error": "Game not found or not in Arcade mode"}

        units = self.db.query(ArcadeUnit).filter(ArcadeUnit.game_id == game_id).all()

        # Initialize CCIR checklist for new games
        self.get_ccir_checklist(game)
        self.db.commit()

        # Update CCIR status for player units
        player_units = [u for u in units if u.side == "player" and u.strength > 0]
        for unit in player_units:
            self.update_ccir_status(game, unit)

        # Evaluate CCIR compliance at start of turn
        ccir_evaluation = self.evaluate_ccir_compliance(game)

        results = {
            "turn": game.current_turn,
            "moves": [],
            "attacks": [],
            "defends": [],
            "recons": [],
            "supplies": [],
            "strikes": [],
            "waits": [],
            "destructions": [],
            "ccir": ccir_evaluation,
        }

        # Process orders
        for order in orders:
            unit = next((u for u in units if u.id == order["unit_id"]), None)
            if not unit or unit.side != "player":
                continue

            order_type = order.get("order_type")

            if order_type == OrderType.MOVE.value:
                move_result = self.resolve_move(
                    unit,
                    order.get("location_x", unit.x),
                    order.get("location_y", unit.y),
                    game.terrain_data or {},
                )
                if move_result["result"] == "SUCCESS":
                    unit.x = move_result["new_x"]
                    unit.y = move_result["new_y"]
                results["moves"].append({"unit": unit.name, **move_result})

            elif order_type == OrderType.ATTACK.value:
                # Check if unit is blocked from attacking (due to previous STRIKE)
                if unit.strike_next_attack_blocked:
                    results["attacks"].append({
                        "attacker": unit.name,
                        "result": "BLOCKED",
                        "reason": "blocked_by_strike",
                        "message": f"{unit.name} cannot attack this turn due to previous STRIKE use"
                    })
                    continue

                target = next(
                    (u for u in units if u.id == order.get("target_id")), None
                )
                if target:
                    attack_result = self.resolve_attack(unit, target, game)
                    target.strength -= attack_result["damage_to_defender"]
                    unit.strength -= attack_result["damage_to_attacker"]

                    if target.strength <= 0:
                        # Award VP for destroying enemy unit
                        vp_value = VP_VALUES.get(target.unit_type, 1)
                        if target.side == "enemy":
                            game.player_score = (game.player_score or 0) + vp_value
                            results["destructions"].append({
                                "unit": target.name,
                                "unit_type": target.unit_type,
                                "vp_awarded": vp_value,
                                "side": "enemy"
                            })
                        else:
                            # Enemy destroyed player unit
                            game.enemy_score = (game.enemy_score or 0) + vp_value
                            results["destructions"].append({
                                "unit": target.name,
                                "unit_type": target.unit_type,
                                "vp_awarded": vp_value,
                                "side": "player"
                            })
                        self.db.delete(target)

                    results["attacks"].append(
                        {
                            "attacker": unit.name,
                            "defender": target.name,
                            **attack_result,
                        }
                    )

            elif order_type == OrderType.DEFEND.value:
                defend_result = self.resolve_defend(unit, game)
                results["defends"].append({"unit": unit.name, **defend_result})

            elif order_type == OrderType.RECON.value:
                recon_result = self.resolve_recon(unit, game)
                results["recons"].append({"unit": unit.name, **recon_result})

            elif order_type == OrderType.SUPPLY.value:
                supply_result = self.resolve_supply(unit)
                results["supplies"].append({"unit": unit.name, **supply_result})

            elif order_type == OrderType.SPECIAL.value:
                # SPECIAL = STRIKE in Arcade mode
                strike_result = self.resolve_strike(unit, units, game)
                results["strikes"].append({"unit": unit.name, **strike_result})

            elif order_type == "wait":
                # WAIT command - no effect in Arcade
                wait_result = self.resolve_wait(unit)
                results["waits"].append({"unit": unit.name, **wait_result})

        self.db.commit()

        # Reset STRIKE flags for next turn
        # strike_used_this_turn: reset to False (can use again next turn)
        # strike_next_attack_blocked: keep True (prevents attack next turn)
        for unit in units:
            if unit.side == "player":
                unit.strike_used_this_turn = False

        # Event deck: 20% chance to draw event each turn
        if random.random() < self.EVENT_DRAW_CHANCE:
            context = {
                "turn_number": game.current_turn,
                "combat_occurred": len(results.get("attacks", [])) > 0,
            }
            drawn_event = self.event_deck.draw_event(game.current_turn, context)
            if drawn_event:
                results["event"] = drawn_event
                # Apply event effects to game state
                game_state = {
                    "event_combat_modifier": 0,
                    "event_defense_modifier": 0,
                    "event_attack_modifier": 0,
                    "event_movement_modifier": 0,
                    "event_artillery_modifier": 0,
                    "event_air_strike_modifier": 0,
                }
                modified_state = self.event_deck.apply_event_to_game_state(game_state, drawn_event)
                # Store active modifiers for this turn
                results["event_modifiers"] = self.event_deck.get_active_modifiers(modified_state)

        # Execute enemy AI turn
        enemy_orders = self.execute_enemy_turn(game_id, game.terrain_data or {})

        # Process enemy orders
        for order in enemy_orders:
            unit = next((u for u in units if u.id == order["unit_id"]), None)
            if not unit or unit.side != "enemy":
                continue

            order_type = order.get("order_type")

            if order_type == OrderType.MOVE.value:
                move_result = self.resolve_move(
                    unit,
                    order.get("location_x", unit.x),
                    order.get("location_y", unit.y),
                    game.terrain_data or {},
                )
                if move_result["result"] == "SUCCESS":
                    unit.x = move_result["new_x"]
                    unit.y = move_result["new_y"]
                results["moves"].append({"unit": unit.name, **move_result})

            elif order_type == OrderType.ATTACK.value:
                target_id = order.get("target_id") or (order.get("target_units", [])[0] if order.get("target_units") else None)
                if target_id is None:
                    continue
                target = next((u for u in units if u.id == target_id), None)
                if target:
                    attack_result = self.resolve_attack(unit, target, game)
                    target.strength -= attack_result["damage_to_defender"]
                    unit.strength -= attack_result["damage_to_attacker"]

                    if target.strength <= 0:
                        # Award VP for destroying enemy unit
                        vp_value = VP_VALUES.get(target.unit_type, 1)
                        if target.side == "enemy":
                            game.player_score = (game.player_score or 0) + vp_value
                            results["destructions"].append({
                                "unit": target.name,
                                "unit_type": target.unit_type,
                                "vp_awarded": vp_value,
                                "side": "enemy"
                            })
                        else:
                            game.enemy_score = (game.enemy_score or 0) + vp_value
                            results["destructions"].append({
                                "unit": target.name,
                                "unit_type": target.unit_type,
                                "vp_awarded": vp_value,
                                "side": "player"
                            })
                        self.db.delete(target)

                    results["attacks"].append({
                        "attacker": unit.name,
                        "defender": target.name,
                        **attack_result,
                    })

            elif order_type == OrderType.DEFEND.value:
                defend_result = self.resolve_defend(unit)
                results["defends"].append({"unit": unit.name, **defend_result})

        self.db.commit()

        # Refresh units after enemy turn for victory check
        units = self.db.query(ArcadeUnit).filter(ArcadeUnit.game_id == game_id).all()

        # Check victory conditions
        player_units = [u for u in units if u.side == "player" and u.strength > 0]
        enemy_units = [u for u in units if u.side == "enemy" and u.strength > 0]

        if not enemy_units:
            results["victory"] = "PLAYER_WINS"
        elif not player_units:
            results["victory"] = "ENEMY_WINS"
        else:
            results["victory"] = None

        # Add scoring info to results
        results["score"] = {
            "player": game.player_score or 0,
            "enemy": game.enemy_score or 0,
            "turn": game.current_turn,
        }

        # Generate SITREP text with score info
        sitrep_parts = []
        if results.get("destructions"):
            for dest in results["destructions"]:
                if dest["side"] == "enemy":
                    sitrep_parts.append(
                        f"{dest['unit']}({dest['unit_type']})を撃破! +{dest['vp_awarded']}VP"
                    )
                else:
                    sitrep_parts.append(
                        f"{dest['unit']}({dest['unit_type']})が敵に撃破された"
                    )
        if results.get("attacks"):
            sitrep_parts.append(f"{len(results['attacks'])}回の攻撃を実施")
        if results.get("moves"):
            sitrep_parts.append(f"{len(results['moves'])}個のユニットが移動")

        results["sitrep"] = " | ".join(sitrep_parts) if sitrep_parts else "問題は発生しませんでした"

        # Advance turn
        game.current_turn += 1

        return results


def create_arcade_game(db: Session, name: str) -> Game:
    """Create a new game in Arcade mode"""
    game = Game(
        name=name,
        game_mode=GameMode.ARCADE,
        map_width=12,
        map_height=8,
        terrain_data={
            f"{x},{y}": "plain"
            for x in range(12)
            for y in range(8)
        },
    )
    db.add(game)
    db.commit()
    db.refresh(game)
    return game
