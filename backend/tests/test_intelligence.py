# Tests for Intelligence Service
import pytest
from app.services.intelligence import IntelligenceService, IntelligenceSource, ConfidenceLevel, create_intelligence_service


class TestIntelligenceService:
    def test_assess_enemy_unit_direct_contact(self):
        """Test enemy assessment with direct contact"""
        service = IntelligenceService(random_seed=42)
        assessment = service.assess_enemy_unit(
            "enemy_1",
            IntelligenceSource.DIRECT_CONTACT,
            {"direct_contact": True}
        )
        assert "unit_id" in assessment
        assert "confidence" in assessment
        assert "source" in assessment

    def test_assess_enemy_unit_night(self):
        """Test enemy assessment at night"""
        service = IntelligenceService(random_seed=42)
        assessment = service.assess_enemy_unit(
            "enemy_1",
            IntelligenceSource.RECON_REPORT,
            {"night": True}
        )
        assert assessment["unit_id"] == "enemy_1"

    def test_assess_enemy_unit_bad_weather(self):
        """Test enemy assessment in bad weather"""
        service = IntelligenceService(random_seed=42)
        assessment = service.assess_enemy_unit(
            "enemy_1",
            IntelligenceSource.AERIAL_RECON,
            {"bad_weather": True}
        )
        assert "accuracy" in assessment

    def test_assess_enemy_unit_has_nvg(self):
        """Test enemy assessment with NOD devices"""
        service = IntelligenceService(random_seed=42)
        assessment = service.assess_enemy_unit(
            "enemy_1",
            IntelligenceSource.RECON_REPORT,
            {"has_nvg": True}
        )
        assert assessment["accuracy"] > 0

    def test_generate_recon_report(self):
        """Test recon report generation"""
        service = IntelligenceService(random_seed=42)
        game_state = {"current_turn": 1}
        recon_units = [{"id": "recon_1", "x": 5, "y": 5, "recon_range": 3, "has_nvg": False}]
        enemy_units = [{"id": "enemy_1", "x": 6, "y": 6}]

        report = service.generate_recon_report(game_state, recon_units, enemy_units)
        assert "turn" in report
        assert "contacts" in report or "estimated_positions" in report

    def test_generate_aerial_recon_report(self):
        """Test aerial recon report generation"""
        service = IntelligenceService(random_seed=42)
        game_state = {"current_turn": 1}
        aerial_units = [{"id": "air_1", "coverage_area": 5}]
        enemy_units = [{"id": "enemy_1", "x": 10, "y": 10}]

        report = service.generate_aerial_recon_report(game_state, aerial_units, enemy_units)
        assert "turn" in report
        assert "aerial_observations" in report

    def test_process_signals_intel(self):
        """Test signals intelligence processing"""
        service = IntelligenceService(random_seed=42)
        game_state = {"current_turn": 1}
        comms = [{"content": "enemy movement detected"}]

        report = service.process_signals_intel(game_state, comms)
        assert "fragmentary_intel" in report

    def test_get_player_visible_enemies(self):
        """Test getting visible enemies"""
        service = IntelligenceService(random_seed=42)
        game_state = {"current_turn": 1}
        player_units = [{"id": "player_1", "x": 5, "y": 5}]
        enemy_units = [{"id": "enemy_1", "x": 6, "y": 6}]

        visible = service.get_player_visible_enemies(game_state, player_units, enemy_units)
        assert isinstance(visible, list)

    def test_create_intelligence_service(self):
        """Test service factory"""
        service = create_intelligence_service(seed=42)
        assert service is not None
        assert isinstance(service, IntelligenceService)


class TestIntelligenceSource:
    def test_all_sources_exist(self):
        """Test all intelligence sources exist"""
        assert IntelligenceSource.DIRECT_CONTACT.value == "direct_contact"
        assert IntelligenceSource.RECON_REPORT.value == "recon_report"
        assert IntelligenceSource.AERIAL_RECON.value == "aerial_recon"
        assert IntelligenceSource.SIGNALS_INTEL.value == "signals_intel"
        assert IntelligenceSource.COMMAND_INTEL.value == "command_intel"


class TestConfidenceLevel:
    def test_confidence_levels_exist(self):
        """Test confidence levels exist"""
        assert ConfidenceLevel.CONFIRMED.value == "confirmed"
        assert ConfidenceLevel.ESTIMATED.value == "推定"
        assert ConfidenceLevel.UNKNOWN.value == "不明"
