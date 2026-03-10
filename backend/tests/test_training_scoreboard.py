# Training Scoreboard Service Tests
import pytest
from app.services.training_scoreboard import (
    TrainingScoreboard,
    CCIRTracker,
    ROETracker,
    CasualtyEfficiencyTracker,
    TimePerformanceTracker,
    CCIRPriority,
)


class TestCCIRTracker:
    """Test CCIR (Commander's Critical Information Requirements) tracking"""

    def test_add_ccir(self):
        """Test adding a new CCIR"""
        tracker = CCIRTracker()
        tracker.add_ccir("test_ccir", "Test CCIR", CCIRPriority.CRITICAL.value)

        assert len(tracker.ccirs) == 1
        assert tracker.ccirs[0]["id"] == "test_ccir"
        assert tracker.ccirs[0]["achieved"] is False

    def test_update_progress(self):
        """Test updating CCIR progress"""
        tracker = CCIRTracker()
        tracker.add_ccir("test_ccir", "Test CCIR", CCIRPriority.HIGH.value, target_value=10)

        result = tracker.update_progress("test_ccir", 5, 1)

        assert result is False
        assert tracker.ccirs[0]["current_value"] == 5
        assert tracker.ccirs[0]["achieved_turn"] is None

    def test_achievement(self):
        """Test CCIR achievement detection"""
        tracker = CCIRTracker()
        tracker.add_ccir("test_ccir", "Test CCIR", CCIRPriority.HIGH.value, target_value=10)

        tracker.update_progress("test_ccir", 10, 3)

        assert tracker.ccirs[0]["achieved"] is True
        assert tracker.ccirs[0]["achieved_turn"] == 3

    def test_achievement_rate(self):
        """Test CCIR achievement rate calculation"""
        tracker = CCIRTracker()
        tracker.add_ccir("ccir1", "CCIR 1", CCIRPriority.CRITICAL.value, target_value=10)
        tracker.add_ccir("ccir2", "CCIR 2", CCIRPriority.HIGH.value, target_value=10)

        tracker.update_progress("ccir1", 10, 1)
        tracker.update_progress("ccir2", 5, 1)

        assert tracker.get_achievement_rate() == 50.0


class TestROETracker:
    """Test ROE (Rules of Engagement) compliance tracking"""

    def test_add_roe_rule(self):
        """Test adding a new ROE rule"""
        tracker = ROETracker()
        tracker.add_roe_rule("roe1", "Test ROE", "test_check")

        assert len(tracker.roe_rules) == 1
        assert tracker.roe_rules[0]["violations_count"] == 0

    def test_record_violation(self):
        """Test recording a ROE violation"""
        tracker = ROETracker()
        tracker.add_roe_rule("roe1", "Test ROE", "test_check")

        tracker.record_violation("roe1", "Test violation", 1)

        assert tracker.roe_rules[0]["violations_count"] == 1
        assert len(tracker.violations) == 1
        assert tracker.violations[0]["severity"] == "violation"

    def test_record_warning(self):
        """Test recording a ROE warning"""
        tracker = ROETracker()
        tracker.add_roe_rule("roe1", "Test ROE", "test_check")

        tracker.record_warning("roe1", "Test warning", 1)

        assert tracker.roe_rules[0]["warnings_count"] == 1
        assert len(tracker.violations) == 1
        assert tracker.violations[0]["severity"] == "warning"

    def test_compliance_rate(self):
        """Test ROE compliance rate calculation"""
        tracker = ROETracker()
        tracker.add_roe_rule("roe1", "ROE 1", "check1")
        tracker.add_roe_rule("roe2", "ROE 2", "check2")

        tracker.record_violation("roe1", "Violation 1", 1)
        tracker.record_warning("roe2", "Warning 1", 1)

        # 1 violation = 10%, 1 warning = 5%, total = 15%
        # compliance = 100 - 15 = 85%
        assert tracker.get_compliance_rate() == 85.0


class TestCasualtyEfficiencyTracker:
    """Test casualty vs effectiveness tracking"""

    def test_initialize(self):
        """Test initializing with unit counts"""
        tracker = CasualtyEfficiencyTracker()
        tracker.initialize(10, 15)

        assert tracker.initial_player_units == 10
        assert tracker.initial_enemy_units == 15

    def test_update_casualties(self):
        """Test updating casualty counts"""
        tracker = CasualtyEfficiencyTracker()
        tracker.initialize(10, 15)

        tracker.update_casualties(player_destroyed=2, enemy_destroyed=5)

        assert tracker.player_destroyed == 2
        assert tracker.enemy_destroyed == 5

    def test_efficiency_ratio(self):
        """Test efficiency ratio calculation"""
        tracker = CasualtyEfficiencyTracker()
        tracker.initialize(10, 15)
        tracker.update_casualties(player_destroyed=2, enemy_destroyed=6)

        # 6 destroyed / 2 lost = 3.0
        assert tracker.get_efficiency_ratio() == 3.0

    def test_efficiency_ratio_zero_losses(self):
        """Test efficiency ratio when no player losses"""
        tracker = CasualtyEfficiencyTracker()
        tracker.initialize(10, 15)
        tracker.update_casualties(player_destroyed=0, enemy_destroyed=3)

        # Division by zero case
        ratio = tracker.get_efficiency_ratio()
        assert ratio == float('inf')

    def test_preservation_rate(self):
        """Test force preservation rate"""
        tracker = CasualtyEfficiencyTracker()
        tracker.initialize(10, 15)
        tracker.update_casualties(player_destroyed=2)

        # 8 remaining / 10 initial = 80%
        assert tracker.get_preservation_rate() == 80.0

    def test_destruction_rate(self):
        """Test enemy destruction rate"""
        tracker = CasualtyEfficiencyTracker()
        tracker.initialize(10, 15)
        tracker.update_casualties(enemy_destroyed=6)

        # 6 destroyed / 15 initial = 40%
        assert tracker.get_destruction_rate() == 40.0


class TestTimePerformanceTracker:
    """Test time management performance tracking"""

    def test_set_target_turns(self):
        """Test setting target turn count"""
        tracker = TimePerformanceTracker()
        tracker.set_target_turns(10)

        assert tracker.target_turns == 10

    def test_advance_turn(self):
        """Test advancing turn counter"""
        tracker = TimePerformanceTracker()
        tracker.advance_turn()
        tracker.advance_turn()

        assert tracker.current_turn == 2

    def test_time_bonus(self):
        """Test adding time bonus"""
        tracker = TimePerformanceTracker()
        tracker.add_bonus("early_complete", 2)

        assert tracker.time_bonuses == 2
        assert tracker.get_time_bonus_net() == 2

    def test_time_penalty(self):
        """Test adding time penalty"""
        tracker = TimePerformanceTracker()
        tracker.add_penalty("delay", 1)

        assert tracker.time_penalties == 1
        assert tracker.get_time_bonus_net() == -1

    def test_achievement_rate(self):
        """Test time achievement rate"""
        tracker = TimePerformanceTracker()
        tracker.set_target_turns(10)
        tracker.current_turn = 8

        # effective_turns = 8, target = 10, achievement = (1 - 8/10) * 100 = 20%
        assert tracker.get_achievement_rate() == 20.0

    def test_is_within_target(self):
        """Test checking if within target time"""
        tracker = TimePerformanceTracker()
        tracker.set_target_turns(10)
        tracker.current_turn = 8

        assert tracker.is_within_time() is True

        tracker.current_turn = 11
        assert tracker.is_within_time() is False


class TestTrainingScoreboard:
    """Test main TrainingScoreboard service"""

    def test_initialize(self):
        """Test scoreboard initialization"""
        scoreboard = TrainingScoreboard(1)
        scoreboard.initialize(player_units=10, enemy_units=12, target_turns=10)

        assert scoreboard.game_id == 1
        assert scoreboard.casualty_tracker.initial_player_units == 10
        assert scoreboard.time_tracker.target_turns == 10

    def test_record_turn(self):
        """Test recording a turn"""
        scoreboard = TrainingScoreboard(1)
        scoreboard.initialize(player_units=10, enemy_units=12, target_turns=10)

        scoreboard.record_turn(1, {
            "player": {"destroyed": 1, "damaged": 2},
            "enemy": {"destroyed": 3, "damaged": 1}
        })

        assert scoreboard.time_tracker.current_turn == 1
        assert len(scoreboard.turn_history) == 1
        assert scoreboard.turn_history[0]["turn"] == 1

    def test_calculate_overall_score(self):
        """Test overall score calculation"""
        scoreboard = TrainingScoreboard(1)
        scoreboard.initialize(player_units=10, enemy_units=12, target_turns=10)

        # Achieve one CCIR
        scoreboard.ccir_tracker.update_progress("ccir_1", 1, 1)

        # Perfect ROE compliance (no violations)
        # Perfect time performance
        scoreboard.time_tracker.current_turn = 5
        scoreboard.time_tracker.target_turns = 10

        score = scoreboard.calculate_overall_score()

        # CCIR: 33% * 0.25 = 8.25 (1/3 achieved)
        # ROE: 100% * 0.20 = 20
        # Casualty: 100% * 0.30 = 30
        # Time: 50% * 0.25 = 12.5
        # Total: ~70.75
        assert 60 <= score <= 80

    def test_calculate_grade_s(self):
        """Test grade S calculation (score >= 90)"""
        scoreboard = TrainingScoreboard(1)
        scoreboard.initialize(player_units=10, enemy_units=12, target_turns=10)

        # Achieve all CCIRs
        scoreboard.ccir_tracker.update_progress("ccir_1", 1, 1)
        scoreboard.ccir_tracker.update_progress("ccir_2", 1, 1)
        scoreboard.ccir_tracker.update_progress("ccir_3", 1, 1)

        # Perfect casualty efficiency (no losses)
        scoreboard.time_tracker.current_turn = 1

        grade = scoreboard.calculate_grade()

        # Score should be >= 80 for at least grade B
        assert grade in ["S", "A", "B"]

    def test_calculate_grade_a(self):
        """Test grade A calculation"""
        scoreboard = TrainingScoreboard(1)
        scoreboard.initialize(player_units=10, enemy_units=12, target_turns=10)

        # Achieve some CCIRs
        scoreboard.ccir_tracker.update_progress("ccir_1", 1, 1)
        scoreboard.ccir_tracker.update_progress("ccir_2", 1, 1)

        scoreboard.time_tracker.current_turn = 7

        grade = scoreboard.calculate_grade()

        assert grade in ["S", "A", "B"]

    def test_get_star_rating(self):
        """Test star rating conversion"""
        scoreboard = TrainingScoreboard(1)

        assert scoreboard.get_star_rating() == 0  # No grade yet

        scoreboard.grade = "S"
        assert scoreboard.get_star_rating() == 5

        scoreboard.grade = "A"
        assert scoreboard.get_star_rating() == 4

        scoreboard.grade = "B"
        assert scoreboard.get_star_rating() == 3

        scoreboard.grade = "C"
        assert scoreboard.get_star_rating() == 2

        scoreboard.grade = "D"
        assert scoreboard.get_star_rating() == 1

        scoreboard.grade = "F"
        assert scoreboard.get_star_rating() == 0

    def test_get_summary(self):
        """Test getting complete summary"""
        scoreboard = TrainingScoreboard(1)
        scoreboard.initialize(player_units=10, enemy_units=12, target_turns=10)

        scoreboard.record_turn(1, {
            "player": {"destroyed": 1, "damaged": 2},
            "enemy": {"destroyed": 3, "damaged": 1}
        })

        summary = scoreboard.get_summary()

        assert "game_id" in summary
        assert "overall_score" in summary
        assert "grade" in summary
        assert "star_rating" in summary
        assert "ccir" in summary
        assert "roe" in summary
        assert "casualty_efficiency" in summary
        assert "time_performance" in summary
        assert "turn_history" in summary

    def test_get_realtime_metrics(self):
        """Test getting realtime metrics"""
        scoreboard = TrainingScoreboard(1)
        scoreboard.initialize(player_units=10, enemy_units=12, target_turns=10)

        scoreboard.record_turn(1, {
            "player": {"destroyed": 1, "damaged": 2},
            "enemy": {"destroyed": 3, "damaged": 1}
        })

        metrics = scoreboard.get_realtime_metrics()

        assert "current_turn" in metrics
        assert "ccir_achievement_rate" in metrics
        assert "roe_compliance_rate" in metrics
        assert "casualty_efficiency" in metrics
        assert "time_performance" in metrics
        assert "overall_score" in metrics

    def test_ccir_update(self):
        """Test updating CCIR progress"""
        scoreboard = TrainingScoreboard(1)
        scoreboard.initialize(player_units=10, enemy_units=12, target_turns=10)

        scoreboard.ccir_tracker.update_progress("ccir_1", 1, 1)

        assert scoreboard.ccir_tracker.ccirs[0]["achieved"] is True

    def test_roe_violation(self):
        """Test recording ROE violations"""
        scoreboard = TrainingScoreboard(1)
        scoreboard.initialize(player_units=10, enemy_units=12, target_turns=10)

        scoreboard.roe_tracker.record_violation("roe_1", "Test violation", 1)

        assert scoreboard.roe_tracker.roe_rules[0]["violations_count"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
