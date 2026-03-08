# Rule Engine for Operational CPX
from sqlalchemy.orm import Session
from app.models import Unit, Turn, Order, Game, OrderType, UnitStatus, SupplyLevel
from datetime import datetime
from typing import Optional
import random
import math


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
    Structured adjudication criteria based on 7 major conditions

    The system evaluates orders against these conditions to determine:
    - Success: Most conditions met
    - Partial: Some conditions met
    - Failed: Few conditions met
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
        }
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
            outcome: "success" | "partial" | "failed"
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

        # 2. Position advantage (simplified - would need terrain system)
        results["position_advantage"] = {
            "met": True,  # Would check terrain in full implementation
            "score": 1.0,
            "description": cls.CONDITIONS["position_advantage"]["description"]
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

        # Calculate weighted score
        total_weight = sum(c["weight"] for c in cls.CONDITIONS.values())
        weighted_score = sum(
            results[cond]["score"] * cls.CONDITIONS[cond]["weight"]
            for cond in results
        ) / total_weight

        # Determine outcome based on score
        conditions_met = sum(1 for r in results.values() if r["met"])
        total_conditions = len(results)

        if weighted_score >= 0.7 and conditions_met >= 5:
            outcome = "success"
        elif weighted_score >= 0.4 and conditions_met >= 3:
            outcome = "partial"
        else:
            outcome = "failed"

        return outcome, results


class RuleEngine:
    def __init__(self, db: Session):
        self.db = db

    def adjudicate_turn(self, game_id: int) -> dict:
        """Execute one turn of adjudication"""
        game = self.db.query(Game).filter(Game.id == game_id).first()
        if not game:
            return {"error": "Game not found"}

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

        # Update turn phase
        turn.phase = "complete"
        game.current_turn += 1
        game.current_time = self._advance_time(game.current_time)
        self.db.commit()

        return {
            "turn": turn.turn_number,
            "results": results,
            "events": enemy_events,
            "next_time": game.current_time
        }

    def _adjudicate_order(self, order: Order) -> dict:
        """Adjudicate a single order"""
        unit = self.db.query(Unit).filter(Unit.id == order.unit_id).first()
        if not unit:
            return {"order_id": order.id, "outcome": "failed", "reason": "Unit not found"}

        changes = []
        outcome = "success"  # Default outcome

        # Process based on order type
        if order.order_type == OrderType.MOVE:
            if order.location_x is not None and order.location_y is not None:
                old_x, old_y = unit.x, unit.y
                unit.x = order.location_x
                unit.y = order.location_y
                changes.append({
                    "type": "move",
                    "target": unit.id,
                    "field": "position",
                    "old_value": {"x": old_x, "y": old_y},
                    "new_value": {"x": unit.x, "y": unit.y}
                })
                outcome = "success"

        elif order.order_type == OrderType.ATTACK:
            # Get target units from order
            target_ids = order.target_units or []
            target_units = []
            for tid in target_ids:
                target = self.db.query(Unit).filter(Unit.id == tid).first()
                if target:
                    target_units.append(target)

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

            # Apply combat effects based on outcome
            if outcome == "failed":
                # Take damage when failed
                if unit.status == UnitStatus.INTACT:
                    unit.status = UnitStatus.LIGHT_DAMAGE
                elif unit.status == UnitStatus.LIGHT_DAMAGE:
                    unit.status = UnitStatus.MEDIUM_DAMAGE

            changes.append({
                "type": "combat",
                "target": unit.id,
                "field": "status",
                "old_value": unit.status,
                "new_value": unit.status,
                "criteria_results": criteria_results
            })

        elif order.order_type == OrderType.DEFEND:
            outcome = "success"
            unit.status = UnitStatus.INTACT  # Defending units recover slightly

        elif order.order_type == OrderType.RECON:
            outcome = "success"
            # Recon increases visibility

        elif order.order_type == OrderType.RETREAT:
            # Move backwards and reduce status
            unit.x = max(0, unit.x - 2)
            changes.append({
                "type": "retreat",
                "target": unit.id,
                "field": "position",
                "old_value": "previous",
                "new_value": {"x": unit.x, "y": unit.y}
            })
            outcome = "success"

        else:
            outcome = "success"

        # Consume supplies
        self._consume_supplies(unit)
        self.db.commit()

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

    def _process_enemy_activities(self, game_id: int) -> list:
        """Process enemy unit activities"""
        enemy_units = self.db.query(Unit).filter(
            Unit.game_id == game_id,
            Unit.side == "enemy"
        ).all()

        events = []
        for unit in enemy_units:
            # Simple AI: random movement
            dx = random.uniform(-3, 3)
            dy = random.uniform(-3, 3)
            unit.x = max(0, min(50, unit.x + dx))
            unit.y = max(0, min(50, unit.y + dy))
            events.append({
                "type": "enemy_move",
                "unit_id": unit.id,
                "new_position": {"x": unit.x, "y": unit.y}
            })

        self.db.commit()
        return events

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

        return {
            "game_id": game.id,
            "name": game.name,
            "turn": game.current_turn,
            "time": game.current_time,
            "weather": game.weather,
            "phase": game.phase,
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
                    "strength": u.strength
                }
                for u in units
            ]
        }
