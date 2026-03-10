# Training Scoreboard Service
# Tracks real-time training metrics (CCIR/ROE/Casualty Efficiency/Time Performance)
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class CCIRPriority(Enum):
    """CCIR (Commander's Critical Information Requirements) priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ROECompliance(Enum):
    """ROE (Rules of Engagement) compliance levels"""
    COMPLIANT = "compliant"
    PARTIAL = "partial"
    NON_COMPLIANT = "non_compliant"


@dataclass
class CCIRTracker:
    """Track CCIR (Commander's Critical Information Requirements)"""
    ccirs: List[Dict[str, Any]] = field(default_factory=list)

    def add_ccir(self, ccir_id: str, description: str, priority: str, target: Any = None, target_value: float = 1.0):
        """Add a new CCIR to track"""
        self.ccirs.append({
            "id": ccir_id,
            "description": description,
            "priority": priority,
            "target": target,
            "achieved": False,
            "achieved_turn": None,
            "current_value": 0,
            "target_value": target_value
        })

    def update_progress(self, ccir_id: str, value: float, turn: int) -> bool:
        """Update CCIR progress and check if achieved"""
        for ccir in self.ccirs:
            if ccir["id"] == ccir_id:
                ccir["current_value"] = value
                was_achieved = ccir["achieved"]
                ccir["achieved"] = value >= ccir["target_value"]
                if ccir["achieved"] and not was_achieved:
                    ccir["achieved_turn"] = turn
                return ccir["achieved"]
        return False

    def get_achievement_rate(self) -> float:
        """Calculate CCIR achievement rate"""
        if not self.ccirs:
            return 100.0
        achieved = sum(1 for ccir in self.ccirs if ccir["achieved"])
        return round(achieved / len(self.ccirs) * 100, 1)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ccirs": self.ccirs,
            "achievement_rate": self.get_achievement_rate(),
            "total": len(self.ccirs),
            "achieved": sum(1 for ccir in self.ccirs if ccir["achieved"])
        }


@dataclass
class ROETracker:
    """Track ROE (Rules of Engagement) compliance"""
    roe_rules: List[Dict[str, Any]] = field(default_factory=list)
    violations: List[Dict[str, Any]] = field(default_factory=list)

    def add_roe_rule(self, rule_id: str, description: str, check_type: str):
        """Add a new ROE rule to track"""
        self.roe_rules.append({
            "id": rule_id,
            "description": description,
            "check_type": check_type,
            "violations_count": 0,
            "warnings_count": 0
        })

    def record_violation(self, rule_id: str, details: str, turn: int):
        """Record a ROE violation"""
        for rule in self.roe_rules:
            if rule["id"] == rule_id:
                rule["violations_count"] += 1
                self.violations.append({
                    "rule_id": rule_id,
                    "details": details,
                    "turn": turn,
                    "severity": "violation"
                })

    def record_warning(self, rule_id: str, details: str, turn: int):
        """Record a ROE warning"""
        for rule in self.roe_rules:
            if rule["id"] == rule_id:
                rule["warnings_count"] += 1
                self.violations.append({
                    "rule_id": rule_id,
                    "details": details,
                    "turn": turn,
                    "severity": "warning"
                })

    def get_compliance_rate(self) -> float:
        """Calculate ROE compliance rate"""
        total_checks = sum(rule["violations_count"] + rule["warnings_count"] for rule in self.roe_rules)
        if total_checks == 0:
            return 100.0
        # Simple compliance: 100 - (violations * 10 + warnings * 5)
        violations = sum(rule["violations_count"] for rule in self.roe_rules)
        warnings = sum(rule["warnings_count"] for rule in self.roe_rules)
        compliance = max(0, 100 - (violations * 10 + warnings * 5))
        return round(compliance, 1)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "roe_rules": self.roe_rules,
            "violations": self.violations[-10:],  # Last 10 violations
            "compliance_rate": self.get_compliance_rate(),
            "total_violations": sum(rule["violations_count"] for rule in self.roe_rules),
            "total_warnings": sum(rule["warnings_count"] for rule in self.roe_rules)
        }


@dataclass
class CasualtyEfficiencyTracker:
    """Track casualty vs effectiveness ratio"""
    initial_player_units: int = 0
    initial_enemy_units: int = 0
    player_destroyed: int = 0
    enemy_destroyed: int = 0
    player_damaged: int = 0
    enemy_damaged: int = 0

    def initialize(self, player_units: int, enemy_units: int):
        """Initialize with starting unit counts"""
        self.initial_player_units = player_units
        self.initial_enemy_units = enemy_units

    def update_casualties(self, player_destroyed: int = 0, enemy_destroyed: int = 0,
                          player_damaged: int = 0, enemy_damaged: int = 0):
        """Update casualty counts"""
        self.player_destroyed += player_destroyed
        self.enemy_destroyed += enemy_destroyed
        self.player_damaged += player_damaged
        self.enemy_damaged += enemy_damaged

    def get_efficiency_ratio(self) -> float:
        """Calculate casualty efficiency ratio (enemy destroyed per player lost)"""
        if self.player_destroyed == 0:
            return float('inf') if self.enemy_destroyed > 0 else 0.0
        return round(self.enemy_destroyed / self.player_destroyed, 2)

    def get_preservation_rate(self) -> float:
        """Calculate force preservation rate"""
        if self.initial_player_units == 0:
            return 100.0
        remaining = self.initial_player_units - self.player_destroyed
        return round(remaining / self.initial_player_units * 100, 1)

    def get_destruction_rate(self) -> float:
        """Calculate enemy destruction rate"""
        if self.initial_enemy_units == 0:
            return 0.0
        return round(self.enemy_destroyed / self.initial_enemy_units * 100, 1)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "efficiency_ratio": self.get_efficiency_ratio() if self.player_destroyed > 0 else float('inf'),
            "player_preservation": self.get_preservation_rate(),
            "enemy_destruction": self.get_destruction_rate(),
            "player_losses": {
                "destroyed": self.player_destroyed,
                "damaged": self.player_damaged,
                "total": self.player_destroyed + self.player_damaged
            },
            "enemy_losses": {
                "destroyed": self.enemy_destroyed,
                "damaged": self.enemy_damaged,
                "total": self.enemy_destroyed + self.enemy_damaged
            }
        }


@dataclass
class TimePerformanceTracker:
    """Track time management performance"""
    target_turns: int = 0
    current_turn: int = 0
    time_bonuses: int = 0
    time_penalties: int = 0

    def set_target_turns(self, target: int):
        """Set target turn count"""
        self.target_turns = target

    def advance_turn(self):
        """Advance to next turn"""
        self.current_turn += 1

    def add_bonus(self, reason: str, amount: int = 1):
        """Add time bonus"""
        self.time_bonuses += amount

    def add_penalty(self, reason: str, amount: int = 1):
        """Add time penalty"""
        self.time_penalties += amount

    def get_time_bonus_net(self) -> int:
        """Calculate net time bonus/penalty"""
        return self.time_bonuses - self.time_penalties

    def get_achievement_rate(self) -> float:
        """Calculate time target achievement rate"""
        if self.target_turns == 0:
            return 100.0
        effective_turns = self.current_turn - self.get_time_bonus_net()
        return round(max(0, (1 - effective_turns / self.target_turns)) * 100, 1)

    def is_within_time(self) -> bool:
        """Check if within target time"""
        effective_turns = self.current_turn - self.get_time_bonus_net()
        return effective_turns <= self.target_turns

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_turns": self.target_turns,
            "current_turn": self.current_turn,
            "effective_turns": self.current_turn - self.get_time_bonus_net(),
            "time_bonuses": self.time_bonuses,
            "time_penalties": self.time_penalties,
            "achievement_rate": self.get_achievement_rate(),
            "within_target": self.is_within_time()
        }


class TrainingScoreboard:
    """
    Main training scoreboard service.
    Tracks CCIR achievement, ROE compliance, casualty efficiency, and time performance.
    Provides real-time scoring and final grade calculation.
    """

    def __init__(self, game_id: int = 0):
        self.game_id = game_id
        self.ccir_tracker = CCIRTracker()
        self.roe_tracker = ROETracker()
        self.casualty_tracker = CasualtyEfficiencyTracker()
        self.time_tracker = TimePerformanceTracker()
        self.turn_history: List[Dict[str, Any]] = []
        self.grade: Optional[str] = None

    def initialize(self, player_units: int, enemy_units: int, target_turns: int):
        """Initialize scoreboard with game parameters"""
        self.casualty_tracker.initialize(player_units, enemy_units)
        self.time_tracker.set_target_turns(target_turns)

        # Initialize default CCIRs
        self.ccir_tracker.add_ccir("ccir_1", "Destroy enemy main force", CCIRPriority.CRITICAL.value, "enemy_main")
        self.ccir_tracker.add_ccir("ccir_2", "Preserve command element", CCIRPriority.HIGH.value, "command")
        self.ccir_tracker.add_ccir("ccir_3", "Secure objective area", CCIRPriority.HIGH.value, "objective")

        # Initialize default ROE rules
        self.roe_tracker.add_roe_rule("roe_1", "Do not engage civilian targets", "collision_check")
        self.roe_tracker.add_roe_rule("roe_2", "Verify target before engagement", "target_verification")
        self.roe_tracker.add_roe_rule("roe_3", "Use proportional force", "force_assessment")

    def record_turn(self, turn_number: int, stats: Dict[str, Any]):
        """Record turn statistics"""
        self.time_tracker.advance_turn()

        # Update casualty tracking
        if "player" in stats and "enemy" in stats:
            self.casualty_tracker.update_casualties(
                player_destroyed=stats["player"].get("destroyed", 0),
                enemy_destroyed=stats["enemy"].get("destroyed", 0),
                player_damaged=stats["player"].get("damaged", 0),
                enemy_damaged=stats["enemy"].get("damaged", 0)
            )

        # Record turn snapshot
        self.turn_history.append({
            "turn": turn_number,
            "ccir_rate": self.ccir_tracker.get_achievement_rate(),
            "roe_rate": self.roe_tracker.get_compliance_rate(),
            "efficiency": self.casualty_tracker.get_efficiency_ratio(),
            "time_rate": self.time_tracker.get_achievement_rate()
        })

    def calculate_overall_score(self) -> float:
        """Calculate overall training score (0-100)"""
        ccir_score = self.ccir_tracker.get_achievement_rate() * 0.25
        roe_score = self.roe_tracker.get_compliance_rate() * 0.20
        casualty_preservation = self.casualty_tracker.get_preservation_rate() * 0.30
        time_score = self.time_tracker.get_achievement_rate() * 0.25

        return round(ccir_score + roe_score + casualty_preservation + time_score, 1)

    def calculate_grade(self) -> str:
        """Calculate final grade based on overall score"""
        score = self.calculate_overall_score()

        if score >= 90:
            grade = "S"
        elif score >= 80:
            grade = "A"
        elif score >= 70:
            grade = "B"
        elif score >= 60:
            grade = "C"
        elif score >= 50:
            grade = "D"
        else:
            grade = "F"

        self.grade = grade
        return grade

    def get_star_rating(self) -> int:
        """Get star rating (1-5) based on grade"""
        if not self.grade:
            return 0
        grade_map = {"S": 5, "A": 4, "B": 3, "C": 2, "D": 1, "F": 0}
        return grade_map.get(self.grade, 0)

    def get_summary(self) -> Dict[str, Any]:
        """Get complete scoreboard summary"""
        score = self.calculate_overall_score()
        grade = self.calculate_grade()

        return {
            "game_id": self.game_id,
            "overall_score": score,
            "grade": grade,
            "star_rating": self.get_star_rating(),
            "ccir": self.ccir_tracker.to_dict(),
            "roe": self.roe_tracker.to_dict(),
            "casualty_efficiency": self.casualty_tracker.to_dict(),
            "time_performance": self.time_tracker.to_dict(),
            "turn_history": self.turn_history,
            "metrics": {
                "ccir_achievement_rate": self.ccir_tracker.get_achievement_rate(),
                "roe_compliance_rate": self.roe_tracker.get_compliance_rate(),
                "casualty_efficiency_ratio": self.casualty_tracker.get_efficiency_ratio(),
                "time_achievement_rate": self.time_tracker.get_achievement_rate()
            }
        }

    def get_realtime_metrics(self) -> Dict[str, Any]:
        """Get current realtime metrics for UI display"""
        return {
            "current_turn": self.time_tracker.current_turn,
            "ccir_achievement_rate": self.ccir_tracker.get_achievement_rate(),
            "roe_compliance_rate": self.roe_tracker.get_compliance_rate(),
            "casualty_efficiency": self.casualty_tracker.get_efficiency_ratio(),
            "time_performance": self.time_tracker.get_achievement_rate(),
            "overall_score": self.calculate_overall_score()
        }
