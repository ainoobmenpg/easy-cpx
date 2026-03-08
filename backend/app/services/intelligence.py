# Intelligence Service
# Handles reconnaissance, information accuracy, and fog of war
import random
from typing import Optional
from datetime import datetime, timedelta
from enum import Enum


class IntelligenceSource(Enum):
    DIRECT_CONTACT = "direct_contact"  # 直接接触・交戦
    RECON_REPORT = "recon_report"  # 偵察部隊報告
    AERIAL_RECON = "aerial_recon"  # 航空偵察
    SIGNALS_INTEL = "signals_intel"  # 通信傍受
    COMMAND_INTEL = "command_intel"  # 上官情報


class ConfidenceLevel(Enum):
    CONFIRMED = "confirmed"  # 確認済み
    ESTIMATED = "推定"  # 推定
    UNKNOWN = "不明"  # 不明


class IntelligenceService:
    """Service for managing reconnaissance and intelligence accuracy"""

    # Base accuracy by source (percentage)
    SOURCE_ACCURACY = {
        IntelligenceSource.DIRECT_CONTACT: 85,  # High but may have confusion
        IntelligenceSource.RECON_REPORT: 60,   # Medium with delay
        IntelligenceSource.AERIAL_RECON: 70,    # Point info with freshness degradation
        IntelligenceSource.SIGNALS_INTEL: 40,   # Fragmented, hard to interpret
        IntelligenceSource.COMMAND_INTEL: 30,   # High delay, aggregated
    }

    # Delay by source (turns)
    SOURCE_DELAY = {
        IntelligenceSource.DIRECT_CONTACT: 0,
        IntelligenceSource.RECON_REPORT: 1,
        IntelligenceSource.AERIAL_RECON: 0,
        IntelligenceSource.SIGNALS_INTEL: 2,
        IntelligenceSource.COMMAND_INTEL: 3,
    }

    def __init__(self, random_seed: Optional[int] = None):
        if random_seed is not None:
            random.seed(random_seed)
        self.intel_cache = {}  # Cache for delayed intel

    def assess_enemy_unit(
        self,
        unit_id: str,
        source: IntelligenceSource,
        conditions: dict = None
    ) -> dict:
        """Assess enemy unit based on intelligence source"""
        base_accuracy = self.SOURCE_ACCURACY.get(source, 50)

        # Modify accuracy based on conditions
        if conditions:
            if conditions.get("night"):
                base_accuracy -= 20
            if conditions.get("bad_weather"):
                base_accuracy -= 15
            if conditions.get("has_nvg"):  # Night vision goggles
                base_accuracy += 10
            if conditions.get("electronic_warfare"):
                base_accuracy -= 25
            if conditions.get("urban_terrain"):
                base_accuracy -= 10
            if conditions.get("enemy_disguised"):
                base_accuracy -= 20

        # Clamp accuracy
        base_accuracy = max(10, min(95, base_accuracy))

        # Determine if this intel is successful
        is_successful = random.random() * 100 < base_accuracy

        if not is_successful:
            return {
                "unit_id": unit_id,
                "confidence": ConfidenceLevel.UNKNOWN,
                "source": source.value,
                "detected": False,
                "accuracy": base_accuracy,
            }

        # Generate assessment with some uncertainty
        confidence = self._determine_confidence(base_accuracy, conditions)

        return {
            "unit_id": unit_id,
            "confidence": confidence,
            "source": source.value,
            "detected": True,
            "accuracy": base_accuracy,
            "position_known": random.random() * 100 < base_accuracy,
            "strength_estimated": random.random() * 100 < (base_accuracy - 20),
            "type_estimated": random.random() * 100 < (base_accuracy - 10),
        }

    def _determine_confidence(
        self,
        accuracy: float,
        conditions: dict = None
    ) -> str:
        """Determine confidence level based on accuracy"""
        # Direct contact has higher confidence
        if conditions and conditions.get("direct_contact"):
            if accuracy >= 80:
                return ConfidenceLevel.CONFIRMED.value
            elif accuracy >= 60:
                return ConfidenceLevel.ESTIMATED.value
            else:
                return ConfidenceLevel.UNKNOWN.value

        # Other sources have lower confidence
        if accuracy >= 70:
            return ConfidenceLevel.ESTIMATED.value
        elif accuracy >= 40:
            return ConfidenceLevel.UNKNOWN.value
        else:
            return ConfidenceLevel.UNKNOWN.value

    def generate_recon_report(
        self,
        game_state: dict,
        recon_units: list,
        enemy_units: list
    ) -> dict:
        """Generate reconnaissance report from recon units"""
        report = {
            "turn": game_state.get("current_turn", 1),
            "timestamp": datetime.utcnow().isoformat(),
            "contacts": [],
            "estimated_positions": [],
            "uncertain_targets": [],
        }

        for recon_unit in recon_units:
            # Each recon unit can detect enemies in range
            recon_range = recon_unit.get("recon_range", 3)
            recon_x = recon_unit.get("x", 0)
            recon_y = recon_unit.get("y", 0)

            for enemy in enemy_units:
                distance = ((enemy.get("x", 0) - recon_x) ** 2 + (enemy.get("y", 0) - recon_y) ** 2) ** 0.5

                if distance <= recon_range:
                    # Direct contact
                    assessment = self.assess_enemy_unit(
                        enemy["id"],
                        IntelligenceSource.DIRECT_CONTACT,
                        {"direct_contact": True, "has_nvg": recon_unit.get("has_nvg", False)}
                    )
                    report["contacts"].append(assessment)
                elif distance <= recon_range * 2:
                    # Recon report (delayed)
                    assessment = self.assess_enemy_unit(
                        enemy["id"],
                        IntelligenceSource.RECON_REPORT,
                        {"night": game_state.get("is_night", False)}
                    )
                    report["estimated_positions"].append(assessment)

        return report

    def generate_aerial_recon_report(
        self,
        game_state: dict,
        aerial_units: list,
        enemy_units: list,
        target_areas: list = None
    ) -> dict:
        """Generate aerial reconnaissance report"""
        report = {
            "turn": game_state.get("current_turn", 1),
            "timestamp": datetime.utcnow().isoformat(),
            "aerial_observations": [],
            "freshness": "current",  # or "stale"
        }

        for aerial_unit in aerial_units:
            # Aerial recon has wider range but point coverage
            coverage_area = aerial_unit.get("coverage_area", 5)

            for enemy in enemy_units:
                # Check if enemy is in target area or general coverage
                if target_areas:
                    in_target = any(
                        self._is_in_area(enemy.get("x"), enemy.get("y"), area)
                        for area in target_areas
                    )
                else:
                    in_target = True

                if in_target:
                    # Random chance of detection (aerial is not guaranteed)
                    if random.random() < 0.7:
                        assessment = self.assess_enemy_unit(
                            enemy["id"],
                            IntelligenceSource.AERIAL_RECON,
                            {
                                "bad_weather": game_state.get("weather") in ["rain", "fog", "snow"],
                                "enemy_disguised": enemy.get("is_concealed", False),
                            }
                        )
                        # Aerial recon has fresh position but limited strength info
                        assessment["position_known"] = True
                        assessment["strength_estimated"] = False
                        report["aerial_observations"].append(assessment)

        # Check for freshness degradation
        if game_state.get("turn", 1) > 1 and random.random() < 0.3:
            report["freshness"] = "stale"

        return report

    def _is_in_area(self, x: float, y: float, area: dict) -> bool:
        """Check if position is within target area"""
        if "center" in area and "radius" in area:
            cx, cy = area["center"]
            radius = area["radius"]
            return ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5 <= radius
        return False

    def process_signals_intel(
        self,
        game_state: dict,
        enemy_communications: list
    ) -> dict:
        """Process signals intelligence from intercepted communications"""
        report = {
            "turn": game_state.get("current_turn", 1),
            "timestamp": datetime.utcnow().isoformat(),
            "fragmentary_intel": [],
            "interpretation_confidence": "low",
        }

        for comm in enemy_communications:
            # Signals intel is always fragmentary
            intel = {
                "type": "fragmentary",
                "content": comm.get("content", ""),
                "reliability": random.randint(1, 5) / 10,  # Low reliability
                "source": IntelligenceSource.SIGNALS_INTEL.value,
            }
            report["fragmentary_intel"].append(intel)

        return report

    def get_player_visible_enemies(
        self,
        game_state: dict,
        player_units: list,
        enemy_units: list
    ) -> list:
        """Get list of enemies visible to player based on all intel sources"""
        visible_enemies = []

        # Collect all intel
        all_assessments = []

        # Direct contact from combat
        for player_unit in player_units:
            for enemy in enemy_units:
                if self._is_adjacent(player_unit, enemy):
                    assessment = self.assess_enemy_unit(
                        enemy["id"],
                        IntelligenceSource.DIRECT_CONTACT,
                        {"direct_contact": True}
                    )
                    all_assessments.append(assessment)

        # Merge assessments for same enemy (take highest confidence)
        enemy_assessments = {}
        for assessment in all_assessments:
            unit_id = assessment["unit_id"]
            if unit_id not in enemy_assessments:
                enemy_assessments[unit_id] = assessment
            else:
                # Keep higher confidence
                current = enemy_assessments[unit_id]
                confidence_order = [ConfidenceLevel.CONFIRMED.value, ConfidenceLevel.ESTIMATED.value, ConfidenceLevel.UNKNOWN.value]
                if confidence_order.index(assessment["confidence"]) < confidence_order.index(current["confidence"]):
                    enemy_assessments[unit_id] = assessment

        return list(enemy_assessments.values())

    def _is_adjacent(self, unit1: dict, unit2: dict, threshold: float = 1.5) -> bool:
        """Check if two units are adjacent"""
        distance = ((unit1.get("x", 0) - unit2.get("x", 0)) ** 2 + (unit1.get("y", 0) - unit2.get("y", 0)) ** 2) ** 0.5
        return distance <= threshold


# Service instance factory
def create_intelligence_service(seed: Optional[int] = None) -> IntelligenceService:
    return IntelligenceService(random_seed=seed)
