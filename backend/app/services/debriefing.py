# Debriefing Generator Service
# Generates post-game evaluation reports (AAR - After Action Report)
import random
from typing import Dict, Any, List, Optional
from app.services.ai_client import AIClient


class AARSection:
    """AAR report section identifiers"""
    EXECUTIVE_SUMMARY = "executive_summary"
    TURN_SUMMARIES = "turn_summaries"
    COMBAT_ANALYSIS = "combat_analysis"
    RESOURCE_ANALYSIS = "resource_analysis"
    TACTICAL_ANALYSIS = "tactical_analysis"
    STRATEGIC_INSIGHTS = "strategic_insights"
    LESSONS_LEARNED = "lessons_learned"
    MOP_MOE = "mop_moe"  # New section for Measures of Performance/Effectiveness


class MOPIndicator:
    """Measures of Performance - quantitative metrics"""

    @staticmethod
    def calculate_player_efficiency(stats: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate player operational efficiency"""
        player = stats["player"]
        enemy = stats["enemy"]

        # Kill ratio (MOP: how efficiently we destroyed enemy)
        killed = enemy["destroyed"]
        lost = player["destroyed"]
        kill_ratio = killed / max(lost, 1)

        # Damage efficiency (MOP: damage dealt vs damage taken)
        total_damage_dealt = (enemy["destroyed"] * 3 + enemy["damaged"] * 2 + enemy["light_damage"] * 1)
        total_damage_taken = (player["destroyed"] * 3 + player["damaged"] * 2 + player["light_damage"] * 1)
        damage_ratio = total_damage_dealt / max(total_damage_taken, 1)

        # Turn efficiency
        total_turns = stats["operations"]["total_turns"]
        destruction_per_turn = killed / max(total_turns, 1)

        return {
            "kill_ratio": round(kill_ratio, 2),
            "damage_ratio": round(damage_ratio, 2),
            "destruction_per_turn": round(destruction_per_turn, 2),
            "rating": "excellent" if kill_ratio >= 3 else "good" if kill_ratio >= 2 else "adequate" if kill_ratio >= 1 else "poor"
        }

    @staticmethod
    def calculate_resource_efficiency(stats: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate resource management efficiency"""
        resources = stats["resources"]

        total_units = stats["player"]["initial_count"]
        if total_units == 0:
            return {"rating": "N/A", "score": 0}

        # Depletion rate
        ammo_depletion = (resources["ammo_depleted_units"] + resources["ammo_low_units"]) / total_units
        fuel_depletion = (resources["fuel_depleted_units"] + resources["fuel_low_units"]) / total_units

        # Score (lower depletion = higher score)
        score = max(0, 10 - (ammo_depletion * 5 + fuel_depletion * 5))

        rating = "excellent" if score >= 8 else "good" if score >= 6 else "adequate" if score >= 4 else "poor"

        return {
            "ammo_depletion_rate": round(ammo_depletion * 100, 1),
            "fuel_depletion_rate": round(fuel_depletion * 100, 1),
            "score": score,
            "rating": rating
        }


class MOEIndicator:
    """Measures of Effectiveness - mission outcome metrics"""

    @staticmethod
    def calculate_mission_effectiveness(stats: Dict[str, Any], mission_result: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate mission effectiveness"""
        player = stats["player"]
        enemy = stats["enemy"]

        # MOE 1: Enemy neutralization rate
        neutralization = enemy["destruction_rate"]

        # MOE 2: Force preservation rate
        preservation = 100 - player["casualty_rate"]

        # MOE 3: Objective completion (from mission_result)
        if mission_result["status"] == "success":
            objective_completion = 100
        elif mission_result["status"] == "partial":
            objective_completion = 50
        else:
            objective_completion = 0

        # Combined effectiveness score
        effectiveness = (neutralization * 0.4 + preservation * 0.3 + objective_completion * 0.3)

        return {
            "enemy_neutralization": round(neutralization, 1),
            "force_preservation": round(preservation, 1),
            "objective_completion": objective_completion,
            "overall_effectiveness": round(effectiveness, 1),
            "rating": "excellent" if effectiveness >= 80 else "good" if effectiveness >= 60 else "adequate" if effectiveness >= 40 else "poor"
        }

    @staticmethod
    def calculate_tactical_effectiveness(stats: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate tactical effectiveness metrics"""
        player = stats["player"]

        # Defensive effectiveness
        casualty_rate = player["casualty_rate"]
        if casualty_rate <= 10:
            defensive_rating = "excellent"
        elif casualty_rate <= 25:
            defensive_rating = "good"
        elif casualty_rate <= 50:
            defensive_rating = "adequate"
        else:
            defensive_rating = "poor"

        # Offensive effectiveness
        enemy = stats["enemy"]
        destruction_rate = enemy["destruction_rate"]
        if destruction_rate >= 50:
            offensive_rating = "excellent"
        elif destruction_rate >= 30:
            offensive_rating = "good"
        elif destruction_rate >= 15:
            offensive_rating = "adequate"
        else:
            offensive_rating = "poor"

        return {
            "defensive_effectiveness": {
                "rating": defensive_rating,
                "casualty_rate": round(casualty_rate, 1),
            },
            "offensive_effectiveness": {
                "rating": offensive_rating,
                "destruction_rate": round(destruction_rate, 1),
            },
            "combined_rating": "excellent" if defensive_rating == "excellent" and offensive_rating == "excellent" else \
                              "good" if defensive_rating in ["excellent", "good"] and offensive_rating in ["excellent", "good"] else \
                              "adequate"
        }


# Backward compatibility - keep original AARSection
class AARSectionOld:
    """AAR report section identifiers"""
    EXECUTIVE_SUMMARY = "executive_summary"
    TURN_SUMMARIES = "turn_summaries"
    COMBAT_ANALYSIS = "combat_analysis"
    RESOURCE_ANALYSIS = "resource_analysis"
    TACTICAL_ANALYSIS = "tactical_analysis"
    STRATEGIC_INSIGHTS = "strategic_insights"
    LESSONS_LEARNED = "lessons_learned"


class DebriefingGenerator:
    """Service for generating After Action Reports (AAR)"""

    def __init__(self):
        self.ai = AIClient()

    async def generate_debriefing(
        self,
        game_id: int,
        db: Any
    ) -> Dict[str, Any]:
        """Generate comprehensive AAR debriefing report"""
        from app.models import Game, Unit, Turn, Order

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

        # Generate AAR-specific sections
        turn_summaries = self._generate_turn_summaries(db, game)
        combat_analysis = self._generate_combat_analysis(db, game)
        tactical_analysis = self._generate_tactical_analysis(stats, game)
        lessons_learned = self._generate_lessons_learned(stats, mission_result)

        # Calculate MOP/MOE indicators (Measures of Performance/Effectiveness)
        mop_indicators = {
            "operational_efficiency": MOPIndicator.calculate_player_efficiency(stats),
            "resource_efficiency": MOPIndicator.calculate_resource_efficiency(stats),
        }
        moe_indicators = {
            "mission_effectiveness": MOEIndicator.calculate_mission_effectiveness(stats, mission_result),
            "tactical_effectiveness": MOEIndicator.calculate_tactical_effectiveness(stats),
        }

        # Generate improvement suggestions
        improvement_suggestions = self._generate_improvement_suggestions(stats, mission_result, mop_indicators, moe_indicators)

        # Build structured AAR response
        return {
            "aar_format": "1.0",
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
            # Main sections
            "executive_summary": {
                "grade": grade,
                "mission_result": mission_result,
                "overview": commentary,
                "key_metrics": self._extract_key_metrics(stats)
            },
            "turn_summaries": turn_summaries,
            "combat_analysis": combat_analysis,
            "resource_analysis": self._generate_resource_analysis(stats),
            "tactical_analysis": tactical_analysis,
            "lessons_learned": lessons_learned,
            "mop_moe": {
                "performance": mop_indicators,
                "effectiveness": moe_indicators,
            },
            "improvement_suggestions": improvement_suggestions,
            "recommendations": self._generate_recommendations(stats, mission_result),
            # Legacy compatibility - keep top-level keys for backward compatibility
            "mission_result": mission_result,
            "grade": grade,
            "statistics": stats,
            "commentary": commentary
        }

    def _extract_key_metrics(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key metrics for executive summary"""
        return {
            "player_casualty_rate": stats["player"]["casualty_rate"],
            "enemy_destruction_rate": stats["enemy"]["destruction_rate"],
            "player_units_remaining": stats["player"]["intact"],
            "enemy_units_destroyed": stats["enemy"]["destroyed"],
            "resource_crisis_count": (
                stats["resources"]["ammo_depleted_units"] +
                stats["resources"]["fuel_depleted_units"]
            )
        }

    def _generate_turn_summaries(self, db: Any, game: Any) -> List[Dict[str, Any]]:
        """Generate summary for each turn"""
        from app.models import Turn, Order

        turns = db.query(Turn).filter(Turn.game_id == game.id).order_by(Turn.turn_number).all()
        summaries = []

        for turn in turns:
            orders = db.query(Order).filter(Order.turn_id == turn.id).all() if turn.id else []

            # Categorize orders
            move_count = sum(1 for o in orders if o.order_type.value == "move")
            attack_count = sum(1 for o in orders if o.order_type.value == "attack")
            defend_count = sum(1 for o in orders if o.order_type.value == "defend")
            support_count = sum(1 for o in orders if o.order_type.value == "support")

            summaries.append({
                "turn_number": turn.turn_number,
                "time": turn.time,
                "phase": turn.phase,
                "weather": turn.weather,
                "orders_issued": len(orders),
                "orders_breakdown": {
                    "move": move_count,
                    "attack": attack_count,
                    "defend": defend_count,
                    "support": support_count
                },
                "sitrep_summary": turn.sitrep_summary if hasattr(turn, 'sitrep_summary') else None
            })

        return summaries

    def _generate_combat_analysis(self, db: Any, game: Any) -> Dict[str, Any]:
        """Generate detailed combat analysis"""
        from app.models import Unit, Turn, Order, UnitStatus

        units = db.query(Unit).filter(Unit.game_id == game.id).all()
        player_units = [u for u in units if u.side == "player"]
        enemy_units = [u for u in units if u.side == "enemy"]

        # Calculate combat effectiveness
        player_combat_power = sum(u.strength for u in player_units if u.status != UnitStatus.DESTROYED)
        enemy_combat_power = sum(u.strength for u in enemy_units if u.status != UnitStatus.DESTROYED)

        # Analyze damage distribution
        player_heavy_damage = len([u for u in player_units if u.status == UnitStatus.HEAVY_DAMAGE])
        player_medium_damage = len([u for u in player_units if u.status == UnitStatus.MEDIUM_DAMAGE])
        player_light_damage = len([u for u in player_units if u.status == UnitStatus.LIGHT_DAMAGE])

        enemy_heavy_damage = len([u for u in enemy_units if u.status == UnitStatus.HEAVY_DAMAGE])
        enemy_medium_damage = len([u for u in enemy_units if u.status == UnitStatus.MEDIUM_DAMAGE])
        enemy_light_damage = len([u for u in enemy_units if u.status == UnitStatus.LIGHT_DAMAGE])

        return {
            "combat_power_ratio": round(player_combat_power / enemy_combat_power, 2) if enemy_combat_power > 0 else 0,
            "player_damage_distribution": {
                "heavy": player_heavy_damage,
                "medium": player_medium_damage,
                "light": player_light_damage,
                "intact": len([u for u in player_units if u.status == UnitStatus.INTACT]),
                "destroyed": len([u for u in player_units if u.status == UnitStatus.DESTROYED])
            },
            "enemy_damage_distribution": {
                "heavy": enemy_heavy_damage,
                "medium": enemy_medium_damage,
                "light": enemy_light_damage,
                "intact": len([u for u in enemy_units if u.status == UnitStatus.INTACT]),
                "destroyed": len([u for u in enemy_units if u.status == UnitStatus.DESTROYED])
            },
            "combat_effectiveness": self._calculate_combat_effectiveness(
                player_units, enemy_units
            )
        }

    def _calculate_combat_effectiveness(
        self,
        player_units: List[Any],
        enemy_units: List[Any]
    ) -> Dict[str, Any]:
        """Calculate combat effectiveness metrics"""
        from app.models import UnitStatus

        # Player effectiveness
        player_destroys = len([u for u in enemy_units if u.status == UnitStatus.DESTROYED])
        player_losses = len([u for u in player_units if u.status == UnitStatus.DESTROYED])

        kill_ratio = player_destroys / player_losses if player_losses > 0 else player_destroys

        # Determine effectiveness rating
        if kill_ratio >= 3.0:
            rating = "excellent"
        elif kill_ratio >= 2.0:
            rating = "good"
        elif kill_ratio >= 1.0:
            rating = "adequate"
        else:
            rating = "poor"

        return {
            "kill_ratio": round(kill_ratio, 2),
            "rating": rating,
            "player_units_destroyed": player_losses,
            "enemy_units_destroyed": player_destroys
        }

    def _generate_resource_analysis(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """Generate resource analysis section"""
        resources = stats["resources"]

        # Determine resource crisis severity
        total_crises = (
            resources["ammo_depleted_units"] +
            resources["fuel_depleted_units"] +
            resources["readiness_degraded"]
        )

        if total_crises == 0:
            severity = "optimal"
        elif total_crises <= 2:
            severity = "manageable"
        elif total_crises <= 5:
            severity = "concerning"
        else:
            severity = "critical"

        return {
            "ammo_status": {
                "depleted": resources["ammo_depleted_units"],
                "low": resources["ammo_low_units"],
                "severity": "critical" if resources["ammo_depleted_units"] > 0 else "warning" if resources["ammo_low_units"] > 0 else "normal"
            },
            "fuel_status": {
                "depleted": resources["fuel_depleted_units"],
                "low": resources["fuel_low_units"],
                "severity": "critical" if resources["fuel_depleted_units"] > 0 else "warning" if resources["fuel_low_units"] > 0 else "normal"
            },
            "readiness_status": {
                "degraded": resources["readiness_degraded"],
                "severity": "critical" if resources["readiness_degraded"] > 3 else "warning" if resources["readiness_degraded"] > 0 else "normal"
            },
            "overall_severity": severity
        }

    def _generate_tactical_analysis(
        self,
        stats: Dict[str, Any],
        game: Any
    ) -> Dict[str, Any]:
        """Generate tactical analysis section"""
        # Analyze based on available stats
        player_casualty_rate = stats["player"]["casualty_rate"]
        enemy_destruction_rate = stats["enemy"]["destruction_rate"]

        # Determine tactical approach
        if enemy_destruction_rate >= 50:
            approach = "aggressive"
        elif enemy_destruction_rate >= 30:
            approach = "balanced"
        else:
            approach = "defensive"

        # Determine defensive performance
        if player_casualty_rate <= 15:
            defensive_rating = "excellent"
        elif player_casualty_rate <= 30:
            defensive_rating = "good"
        elif player_casualty_rate <= 50:
            defensive_rating = "adequate"
        else:
            defensive_rating = "poor"

        return {
            "offensive_approach": approach,
            "defensive_rating": defensive_rating,
            "efficiency_score": round(
                (enemy_destruction_rate / max(player_casualty_rate, 1)) * 10, 1
            ),
            "tactical_recommendations": self._generate_tactical_recommendations(
                stats, approach, defensive_rating
            )
        }

    def _generate_tactical_recommendations(
        self,
        stats: Dict[str, Any],
        approach: str,
        defensive_rating: str
    ) -> List[str]:
        """Generate tactical recommendations"""
        recommendations = []

        if defensive_rating == "poor":
            recommendations.append("Improve defensive positioning and cover utilization")
        elif defensive_rating == "adequate":
            recommendations.append("Consider more conservative engagement distances")

        if approach == "aggressive":
            recommendations.append("Maintain aggressive pressure but watch for overextension")

        resources = stats["resources"]
        if resources["ammo_depleted_units"] > 0:
            recommendations.append("Establish forward ammo depots for sustained operations")

        if resources["fuel_depleted_units"] > 0:
            recommendations.append("Plan fuel resupply points along advance routes")

        return recommendations

    def _generate_lessons_learned(
        self,
        stats: Dict[str, Any],
        mission_result: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate structured lessons learned"""
        lessons = []

        # Analyze each aspect and create lesson entries
        player_casualty_rate = stats["player"]["casualty_rate"]
        enemy_destruction_rate = stats["enemy"]["destruction_rate"]
        resources = stats["resources"]

        # Casualty lesson
        if player_casualty_rate > 30:
            lessons.append({
                "category": "force_protection",
                "observation": f"Friendly casualty rate of {player_casualty_rate}% exceeds acceptable threshold",
                "lesson": "Review tactical dispersion and fire support coordination",
                "impact": "high"
            })
        elif player_casualty_rate < 15:
            lessons.append({
                "category": "force_protection",
                "observation": f"Friendly casualty rate of {player_casualty_rate}% is excellent",
                "lesson": "Continue current force protection procedures",
                "impact": "positive"
            })

        # Enemy destruction lesson
        if enemy_destruction_rate > 50:
            lessons.append({
                "category": "offensive_operations",
                "observation": f"Destroyed {enemy_destruction_rate}% of enemy force",
                "lesson": "Effective concentration of force achieved",
                "impact": "positive"
            })

        # Resource lessons
        if resources["ammo_depleted_units"] > 0:
            lessons.append({
                "category": "logistics",
                "observation": f"{resources['ammo_depleted_units']} units depleted ammunition",
                "lesson": "Supply chain requires improvement",
                "impact": "medium"
            })

        if resources["fuel_depleted_units"] > 0:
            lessons.append({
                "category": "logistics",
                "observation": f"{resources['fuel_depleted_units']} units depleted fuel",
                "lesson": "Fuel resupply operations need better planning",
                "impact": "medium"
            })

        return lessons

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

    def _generate_improvement_suggestions(
        self,
        stats: Dict[str, Any],
        mission_result: Dict[str, Any],
        mop_indicators: Dict[str, Any],
        moe_indicators: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate specific improvement suggestions based on MOP/MOE analysis"""
        suggestions = []

        # Analyze operational efficiency (MOP)
        op_eff = mop_indicators.get("operational_efficiency", {})
        if op_eff.get("rating") == "poor":
            suggestions.append({
                "area": "operational_efficiency",
                "priority": "high",
                "issue": "Kill ratio indicates inefficient combat operations",
                "suggestion": "Concentrate fire on isolated enemy units. Avoid prolonged engagements.",
                "metric": f"Kill ratio: {op_eff.get('kill_ratio', 0)}"
            })

        # Analyze resource efficiency (MOP)
        res_eff = mop_indicators.get("resource_efficiency", {})
        if res_eff.get("rating") in ["poor", "adequate"]:
            suggestions.append({
                "area": "resource_management",
                "priority": "medium" if res_eff.get("rating") == "adequate" else "high",
                "issue": f"Resource depletion: Ammo {res_eff.get('ammo_depletion_rate', 0)}%, Fuel {res_eff.get('fuel_depletion_rate', 0)}%",
                "suggestion": "Establish forward supply points. Prioritize ammunition conservation.",
                "metric": f"Resource score: {res_eff.get('score', 0)}/10"
            })

        # Analyze mission effectiveness (MOE)
        mission_eff = moe_indicators.get("mission_effectiveness", {})
        if mission_eff.get("rating") == "poor":
            suggestions.append({
                "area": "mission_effectiveness",
                "priority": "critical",
                "issue": "Mission objectives not achieved",
                "suggestion": "Review commander's intent. Reassess tactical approach.",
                "metric": f"Effectiveness: {mission_eff.get('overall_effectiveness', 0)}%"
            })

        # Analyze tactical effectiveness (MOE)
        tact_eff = moe_indicators.get("tactical_effectiveness", {})
        defensive = tact_eff.get("defensive_effectiveness", {})
        if defensive.get("rating") == "poor":
            suggestions.append({
                "area": "force_protection",
                "priority": "high",
                "issue": f"High casualty rate: {defensive.get('casualty_rate', 0)}%",
                "suggestion": "Use terrain for cover. Increase recon before engagement.",
                "metric": f"Defensive rating: {defensive.get('rating')}"
            })

        offensive = tact_eff.get("offensive_effectiveness", {})
        if offensive.get("rating") == "poor":
            suggestions.append({
                "area": "offensive_operations",
                "priority": "high",
                "issue": f"Low enemy destruction: {offensive.get('destruction_rate', 0)}%",
                "suggestion": "Focus fire on vulnerable targets. Maintain initiative.",
                "metric": f"Offensive rating: {offensive.get('rating')}"
            })

        # Add positive feedback for excellent performance
        if mission_eff.get("rating") == "excellent":
            suggestions.append({
                "area": "overall_performance",
                "priority": "info",
                "issue": "Excellent mission execution",
                "suggestion": "Maintain current operational tempo and tactics.",
                "metric": f"Overall effectiveness: {mission_eff.get('overall_effectiveness', 0)}%"
            })

        return suggestions

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
