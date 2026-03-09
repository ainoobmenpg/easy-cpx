# Debriefing Generator Service
# Generates post-game evaluation reports
import random
from typing import Dict, Any, List, Optional
from app.services.ai_client import AIClient


class DebriefingGenerator:
    """Service for generating game debriefing reports"""

    def __init__(self):
        self.ai = AIClient()

    async def generate_debriefing(
        self,
        game_id: int,
        db: Any
    ) -> Dict[str, Any]:
        """Generate comprehensive debriefing report"""
        from app.models import Game, Unit, Turn

        game = db.query(Game).filter(Game.id == game_id).first()
        if not game:
            raise ValueError(f"Game {game_id} not found")

        # Gather game statistics
        stats = self._calculate_statistics(db, game)

        # Determine mission success
        mission_result = self._evaluate_mission(stats, game)

        # Calculate grade
        grade = self._calculate_grade(stats, mission_result)

        # Generate AI commentary
        commentary = await self._generate_commentary(stats, mission_result, game)

        return {
            "game_id": game_id,
            "game_name": game.name,
            "scenario_id": game.scenario_id,
            "total_turns": game.current_turn - 1,
            "duration": {
                "start_date": game.current_date,
                "start_time": game.current_time,
                "end_date": game.current_date,
                "end_turn": game.current_turn - 1
            },
            "statistics": stats,
            "mission_result": mission_result,
            "grade": grade,
            "commentary": commentary,
            "recommendations": self._generate_recommendations(stats, mission_result)
        }

    def _calculate_statistics(self, db: Any, game: Any) -> Dict[str, Any]:
        """Calculate game statistics"""
        from app.models import Unit, Turn, UnitStatus

        # Get all units
        units = db.query(Unit).filter(Unit.game_id == game.id).all()

        player_units = [u for u in units if u.side == "player"]
        enemy_units = [u for u in units if u.side == "enemy"]

        # Player losses
        player_destroyed = len([u for u in player_units if u.status == UnitStatus.DESTROYED])
        player_damaged = len([u for u in player_units if u.status in [UnitStatus.HEAVY_DAMAGE, UnitStatus.MEDIUM_DAMAGE]])
        player_light_damage = len([u for u in player_units if u.status == UnitStatus.LIGHT_DAMAGE])
        player_intact = len([u for u in player_units if u.status == UnitStatus.INTACT])

        # Enemy losses
        enemy_destroyed = len([u for u in enemy_units if u.status == UnitStatus.DESTROYED])
        enemy_damaged = len([u for u in enemy_units if u.status in [UnitStatus.HEAVY_DAMAGE, UnitStatus.MEDIUM_DAMAGE]])
        enemy_light_damage = len([u for u in enemy_units if u.status == UnitStatus.LIGHT_DAMAGE])

        # Resource consumption
        ammo_consumed = self._calculate_resource_consumption(units, "ammo")
        fuel_consumed = self._calculate_resource_consumption(units, "fuel")
        readiness_impact = self._calculate_readiness_impact(player_units)

        # Get turn logs
        turns = db.query(Turn).filter(Turn.game_id == game.id).all()
        total_orders = sum(len(t.orders) for t in turns if t.orders)

        # Calculate average strength
        avg_player_strength = sum(u.strength for u in player_units) / len(player_units) if player_units else 0

        return {
            "player": {
                "initial_count": len(player_units),
                "destroyed": player_destroyed,
                "damaged": player_damaged,
                "light_damage": player_light_damage,
                "intact": player_intact,
                "casualty_rate": round(player_destroyed / len(player_units) * 100, 1) if player_units else 0,
                "average_strength": round(avg_player_strength, 1)
            },
            "enemy": {
                "initial_count": len(enemy_units),
                "destroyed": enemy_destroyed,
                "damaged": enemy_damaged,
                "light_damage": enemy_light_damage,
                "destruction_rate": round(enemy_destroyed / len(enemy_units) * 100, 1) if enemy_units else 0
            },
            "resources": {
                "ammo_depleted_units": ammo_consumed["depleted"],
                "ammo_low_units": ammo_consumed["low"],
                "fuel_depleted_units": fuel_consumed["depleted"],
                "fuel_low_units": fuel_consumed["low"],
                "readiness_degraded": readiness_impact
            },
            "operations": {
                "total_turns": game.current_turn - 1,
                "total_orders": total_orders
            }
        }

    def _calculate_resource_consumption(
        self,
        units: List[Any],
        resource: str
    ) -> Dict[str, int]:
        """Calculate resource consumption"""
        from app.models import SupplyLevel

        depleted = 0
        low = 0

        for unit in units:
            resource_value = getattr(unit, resource, None)
            if resource_value == SupplyLevel.EXHAUSTED:
                depleted += 1
            elif resource_value == SupplyLevel.DEPLETED:
                low += 1

        return {"depleted": depleted, "low": low}

    def _calculate_readiness_impact(self, units: List[Any]) -> int:
        """Calculate readiness degradation"""
        from app.models import SupplyLevel

        return len([u for u in units if u.readiness in [SupplyLevel.DEPLETED, SupplyLevel.EXHAUSTED]])

    def _evaluate_mission(self, stats: Dict[str, Any], game: Any) -> Dict[str, Any]:
        """Evaluate mission completion"""
        # This is a simplified evaluation - in a full implementation,
        # objectives would be tracked throughout the game
        player_casualty_rate = stats["player"]["casualty_rate"]
        enemy_destruction_rate = stats["enemy"]["destruction_rate"]

        # Simple evaluation logic
        if enemy_destruction_rate >= 50 and player_casualty_rate <= 30:
            status = "success"
            description = "Mission accomplished. Objectives achieved with acceptable losses."
        elif enemy_destruction_rate >= 30 and player_casualty_rate <= 50:
            status = "partial"
            description = "Mission partially accomplished. Some objectives achieved."
        else:
            status = "failed"
            description = "Mission failed. Objectives not achieved."

        return {
            "status": status,
            "description": description,
            "player_casualty_rate": player_casualty_rate,
            "enemy_destruction_rate": enemy_destruction_rate
        }

    def _calculate_grade(
        self,
        stats: Dict[str, Any],
        mission_result: Dict[str, Any]
    ) -> str:
        """Calculate final grade"""
        player_casualty_rate = stats["player"]["casualty_rate"]
        enemy_destruction_rate = stats["enemy"]["destruction_rate"]
        resource_score = self._calculate_resource_score(stats["resources"])

        # Weighted score
        mission_score = 50 if mission_result["status"] == "success" else 25 if mission_result["status"] == "partial" else 0
        casualty_score = max(0, 30 - player_casualty_rate)  # Lower casualties = higher score
        enemy_score = min(20, enemy_destruction_rate / 5)  # Higher enemy destruction = higher score
        resource_score = resource_score  # Resource management score

        total_score = mission_score + casualty_score + enemy_score + resource_score

        if total_score >= 80:
            return "S"
        elif total_score >= 70:
            return "A"
        elif total_score >= 55:
            return "B"
        elif total_score >= 40:
            return "C"
        else:
            return "D"

    def _calculate_resource_score(self, resources: Dict[str, int]) -> int:
        """Calculate resource management score"""
        total_units = resources.get("ammo_depleted_units", 0) + resources.get("fuel_depleted_units", 0)
        if total_units == 0:
            return 10
        elif total_units <= 2:
            return 7
        elif total_units <= 5:
            return 4
        else:
            return 1

    async def _generate_commentary(
        self,
        stats: Dict[str, Any],
        mission_result: Dict[str, Any],
        game: Any
    ) -> str:
        """Generate AI commentary for the debriefing"""
        # Create a summary for AI to generate commentary
        summary = {
            "total_turns": stats["operations"]["total_turns"],
            "player_casualty_rate": stats["player"]["casualty_rate"],
            "enemy_destruction_rate": stats["enemy"]["destruction_rate"],
            "mission_status": mission_result["status"],
            "resource_issues": stats["resources"]["ammo_depleted_units"] + stats["resources"]["fuel_depleted_units"]
        }

        # Use AI to generate commentary
        try:
            commentary = await self.ai.generate_debriefing_comment(summary)
            return commentary
        except Exception as e:
            # Fallback commentary
            return self._fallback_commentary(summary)

    def _fallback_commentary(self, summary: Dict[str, Any]) -> str:
        """Generate fallback commentary when AI is unavailable"""
        if summary["mission_status"] == "success":
            return "Excellent operation. Your forces performed with high efficiency. Command is pleased with the results."
        elif summary["mission_status"] == "partial":
            return "Operation completed with mixed results. Some objectives were achieved while others remain outstanding. Further analysis required."
        else:
            return "Operation did not achieve intended objectives. Command will review the planning and execution. Lessons will be incorporated into future operations."

    def _generate_recommendations(
        self,
        stats: Dict[str, Any],
        mission_result: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on performance"""
        recommendations = []

        # Casualty-based recommendations
        if stats["player"]["casualty_rate"] > 30:
            recommendations.append("Consider more conservative tactics to reduce friendly casualties.")

        # Resource recommendations
        if stats["resources"]["ammo_depleted_units"] > 0:
            recommendations.append("Improve supply chain management to maintain ammunition levels.")

        if stats["resources"]["fuel_depleted_units"] > 0:
            recommendations.append("Plan fuel resupply operations more carefully.")

        # Aggressive recommendations
        if mission_result["status"] == "failed" and stats["enemy"]["destruction_rate"] < 20:
            recommendations.append("Consider more aggressive engagement strategies.")

        if not recommendations:
            recommendations.append("Continue current operational tempo. Performance is satisfactory.")

        return recommendations
