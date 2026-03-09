# Arcade CPX - Simplified 2D6 Rule Engine
import random
from typing import Optional
from sqlalchemy.orm import Session
from app.models import Game, GameMode, ArcadeUnit, OrderType
from app.services.event_deck import EventDeckService


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


class ArcadeAdjudication:
    """Simplified 2D6 rule engine for Arcade mode"""

    # Event deck draw chance per turn (20%)
    EVENT_DRAW_CHANCE = 0.2

    def __init__(self, db_session: Session, seed: Optional[int] = None):
        self.db = db_session
        if seed is not None:
            random.seed(seed)
        # Initialize event deck service
        self.event_deck = EventDeckService(random_seed=seed)

    def roll_2d6(self) -> int:
        """Roll 2 six-sided dice"""
        return random.randint(1, 6) + random.randint(1, 6)

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

        attack_roll = self.roll_2d6() + attacker_stats["attack"] + attack_mod
        defense_roll = self.roll_2d6() + defender_stats["defense"] + defense_mod

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

        return {
            "result": result,
            "attack_roll": attack_roll,
            "defense_roll": defense_roll,
            "damage_to_attacker": damage_to_attacker,
            "damage_to_defender": damage_to_defender,
            "strike_bonus": strike_bonus,
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
                        results["destructions"].append(target.name)
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

        # Check victory conditions
        player_units = [u for u in units if u.side == "player"]
        enemy_units = [u for u in units if u.side == "enemy"]

        if not enemy_units:
            results["victory"] = "PLAYER_WINS"
        elif not player_units:
            results["victory"] = "ENEMY_WINS"
        else:
            results["victory"] = None

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
