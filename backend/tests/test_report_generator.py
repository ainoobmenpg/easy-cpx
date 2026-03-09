# Tests for Report Generator
import pytest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.report_generator import (
    UnifiedReportGenerator,
    SALUTEGenerator,
    INTSUMGenerator,
    OPSUMGenerator,
    LOGSITREPGenerator,
    get_report_generator
)


# Sample game state for testing
SAMPLE_GAME_STATE = {
    "turn": 5,
    "time": "08:00",
    "weather": "clear",
    "units": [
        {
            "id": 1,
            "name": "Alpha Team",
            "type": "infantry",
            "side": "player",
            "x": 10,
            "y": 20,
            "status": "intact",
            "ammo": "full",
            "fuel": "full",
            "readiness": "full",
            "strength": 100
        },
        {
            "id": 2,
            "name": "Bravo Team",
            "type": "armor",
            "side": "player",
            "x": 15,
            "y": 25,
            "status": "light_damage",
            "ammo": "depleted",
            "fuel": "full",
            "readiness": "full",
            "strength": 80
        },
        {
            "id": 101,
            "name": "Enemy Force",
            "type": "armor",
            "side": "enemy",
            "x": 30,
            "y": 40,
            "status": "intact",
            "ammo": "full",
            "fuel": "full",
            "readiness": "full",
            "strength": 100
        }
    ]
}

SAMPLE_ENEMY_KNOWLEDGE = {
    "confirmed": [101],
    "estimated": [],
    "unknown": []
}

SAMPLE_ORDER_RESULTS = [
    {"unit_name": "Alpha Team", "outcome": "success", "intent": "前進"},
    {"unit_name": "Bravo Team", "outcome": "partial", "intent": "攻撃"}
]


class TestSALUTEGenerator:
    def test_generate_salute_basic(self):
        """Test basic SALUTE generation"""
        generator = SALUTEGenerator()

        unit_data = {
            "size": "1個小隊",
            "activity": "移動中",
            "location": "Grid 10-20",
            "unit_name": "Alpha Team",
            "equipment": "小火器"
        }

        result = generator.generate(unit_data, SAMPLE_GAME_STATE, "中脅威")

        assert "report_id" in result
        assert result["turn"] == 5
        assert result["size"] == "1個小隊"
        assert result["activity"] == "移動中"
        assert result["location"] == "Grid 10-20"
        assert result["unit"] == "Alpha Team"
        assert result["time"] == "08:00"
        assert result["equipment"] == "小火器"
        assert result["assessment"] == "中脅威"
        assert result["report_id"].startswith("SALUTE-")


class TestINTSUMGenerator:
    def test_generate_intsum_basic(self):
        """Test basic INTSUM generation"""
        generator = INTSUMGenerator()

        result = generator.generate(
            SAMPLE_GAME_STATE,
            SAMPLE_ENEMY_KNOWLEDGE,
            SAMPLE_ORDER_RESULTS
        )

        assert "report_id" in result
        assert result["turn"] == 5
        assert "enemy_dispositions" in result
        assert "friendly_dispositions" in result
        assert "recommendations" in result
        assert result["report_id"].startswith("INTSUM-")

    def test_intsum_enemy_dispositions(self):
        """Test enemy disposition tracking"""
        generator = INTSUMGenerator()

        result = generator.generate(
            SAMPLE_GAME_STATE,
            SAMPLE_ENEMY_KNOWLEDGE,
            SAMPLE_ORDER_RESULTS
        )

        # Confirmed enemy should be in dispositions
        enemy_disp = result["enemy_dispositions"]
        assert len(enemy_disp) == 1
        assert enemy_disp[0]["unit_name"] == "Enemy Force"
        assert enemy_disp[0]["assessment"] == "confirmed"

    def test_intsum_friendly_dispositions(self):
        """Test friendly disposition tracking"""
        generator = INTSUMGenerator()

        result = generator.generate(
            SAMPLE_GAME_STATE,
            SAMPLE_ENEMY_KNOWLEDGE,
            SAMPLE_ORDER_RESULTS
        )

        # Should have 2 friendly units
        friendly_disp = result["friendly_dispositions"]
        assert len(friendly_disp) == 2

    def test_intsum_recommendations(self):
        """Test recommendation generation"""
        generator = INTSUMGenerator()

        result = generator.generate(
            SAMPLE_GAME_STATE,
            SAMPLE_ENEMY_KNOWLEDGE,
            SAMPLE_ORDER_RESULTS
        )

        # Should have at least one recommendation
        assert len(result["recommendations"]) > 0


class TestOPSUMGenerator:
    def test_generate_opsumm_basic(self):
        """Test basic OPSUM generation"""
        generator = OPSUMGenerator()

        result = generator.generate(
            SAMPLE_GAME_STATE,
            SAMPLE_ORDER_RESULTS,
            [],
            []
        )

        assert "report_id" in result
        assert result["turn"] == 5
        assert "operations_conducted" in result
        assert "commander_assessment" in result
        assert result["report_id"].startswith("OPSUM-")

    def test_opsum_operations_conducted(self):
        """Test operation outcome tracking"""
        generator = OPSUMGenerator()

        result = generator.generate(
            SAMPLE_GAME_STATE,
            SAMPLE_ORDER_RESULTS,
            [],
            []
        )

        ops = result["operations_conducted"]
        assert len(ops) == 2
        assert ops[0]["outcome"] == "success"
        assert ops[1]["outcome"] == "partial"

    def test_opsum_commander_assessment(self):
        """Test commander assessment based on outcomes"""
        generator = OPSUMGenerator()

        # All success
        result = generator.generate(
            SAMPLE_GAME_STATE,
            [{"unit_name": "Test", "outcome": "success", "intent": "test"}],
            [],
            []
        )

        assert "全作戦成功" in result["commander_assessment"] or "success" in result["commander_assessment"].lower()


class TestLOGSITREPGenerator:
    def test_generate_logsitrep_basic(self):
        """Test basic LOGSITREP generation"""
        generator = LOGSITREPGenerator()

        result = generator.generate(SAMPLE_GAME_STATE)

        assert "report_id" in result
        assert result["turn"] == 5
        assert "supply_status" in result
        assert "supply_lines" in result
        assert "resupply_requests" in result
        assert result["report_id"].startswith("LOGSITREP-")

    def test_logsitrep_supply_status(self):
        """Test supply status calculation"""
        generator = LOGSITREPGenerator()

        result = generator.generate(SAMPLE_GAME_STATE)

        supply = result["supply_status"]

        # Check ammo
        assert "ammo" in supply
        assert supply["ammo"]["full"] == 2  # Alpha + Enemy
        assert supply["ammo"]["depleted"] == 1  # Bravo

        # Check fuel
        assert "fuel" in supply
        assert supply["fuel"]["full"] == 3

    def test_logsitrep_resupply_requests(self):
        """Test auto-generated resupply requests"""
        generator = LOGSITREPGenerator()

        result = generator.generate(SAMPLE_GAME_STATE)

        # Bravo has depleted ammo, should generate request
        requests = result["resupply_requests"]
        assert len(requests) > 0
        assert any(r["type"] == "ammo" for r in requests)


class TestUnifiedReportGenerator:
    def test_get_report_generator(self):
        """Test singleton pattern"""
        gen1 = get_report_generator()
        gen2 = get_report_generator()
        assert gen1 is gen2

    def test_generate_sitrep_format(self):
        """Test SITREP format generation"""
        generator = get_report_generator()

        result = generator.generate("sitrep", SAMPLE_GAME_STATE)

        assert result["format"] == "sitrep"
        assert "content" in result

    def test_generate_intsumm_format(self):
        """Test INTSUM format generation"""
        generator = get_report_generator()

        result = generator.generate("intsumm", SAMPLE_GAME_STATE, {
            "enemy_knowledge": SAMPLE_ENEMY_KNOWLEDGE,
            "order_results": SAMPLE_ORDER_RESULTS
        })

        assert result["format"] == "intsumm"
        assert "content" in result

    def test_generate_opsumm_format(self):
        """Test OPSUM format generation"""
        generator = get_report_generator()

        result = generator.generate("opsumm", SAMPLE_GAME_STATE, {
            "order_results": SAMPLE_ORDER_RESULTS
        })

        assert result["format"] == "opsumm"
        assert "content" in result

    def test_generate_logsitrep_format(self):
        """Test LOGSITREP format generation"""
        generator = get_report_generator()

        result = generator.generate("logsitrep", SAMPLE_GAME_STATE)

        assert result["format"] == "logsitrep"
        assert "content" in result

    def test_generate_salute_format(self):
        """Test SALUTE format generation"""
        generator = get_report_generator()

        result = generator.generate("salute", SAMPLE_GAME_STATE, {
            "unit_data": {
                "size": "1個小隊",
                "activity": "防御中",
                "location": "Grid 10-20",
                "unit_name": "Alpha Team",
                "equipment": "小火器"
            },
            "assessment": "低脅威"
        })

        assert result["format"] == "salute"
        assert result["content"]["assessment"] == "低脅威"

    def test_generate_all_formats(self):
        """Test generating all formats at once"""
        generator = get_report_generator()

        result = generator.generate_all(SAMPLE_GAME_STATE, {
            "enemy_knowledge": SAMPLE_ENEMY_KNOWLEDGE,
            "order_results": SAMPLE_ORDER_RESULTS
        })

        assert "sitrep" in result
        assert "intsumm" in result
        assert "opsumm" in result
        assert "logsitrep" in result

    def test_unknown_format_raises(self):
        """Test that unknown format raises ValueError"""
        generator = get_report_generator()

        with pytest.raises(ValueError):
            generator.generate("unknown_format", SAMPLE_GAME_STATE)

    def test_report_id_uniqueness(self):
        """Test that report IDs are unique"""
        generator = get_report_generator()

        ids = set()
        for _ in range(10):
            result = generator.generate("intsumm", SAMPLE_GAME_STATE)
            ids.add(result["report_id"])

        # All IDs should be unique
        assert len(ids) == 10

    def test_turn_and_timestamp_present(self):
        """Test that turn and timestamp are present in all reports"""
        generator = get_report_generator()

        for format_type in ["sitrep", "intsumm", "opsumm", "logsitrep"]:
            result = generator.generate(format_type, SAMPLE_GAME_STATE)

            assert "turn" in result
            assert "timestamp" in result
            assert "generated_at" in result
            assert result["turn"] == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
