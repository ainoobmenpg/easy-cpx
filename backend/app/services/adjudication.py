# Rule Engine for Operational CPX
from sqlalchemy.orm import Session
from app.models import Unit, Turn, Order, Game, OrderType, UnitStatus, SupplyLevel
from datetime import datetime
import random
import math


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
            # Simple combat resolution
            outcome = self._resolve_combat(unit)
            changes.append({
                "type": "combat",
                "target": unit.id,
                "field": "status",
                "old_value": unit.status,
                "new_value": unit.status
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
