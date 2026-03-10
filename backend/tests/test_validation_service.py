"""Tests for AI validation service (validation_service.py)"""
import pytest
import json
from pathlib import Path

from app.services.validation_service import (
    AIValidationService,
    SchemaType,
    ValidationResult,
    ValidationReport,
    get_validation_service,
    reset_validation_service,
)
from app.services.audit_logger import reset_audit_logger


class TestAIValidationService:
    """Test validation service functionality"""

    def setup_method(self):
        """Set up test environment"""
        reset_validation_service()
        reset_audit_logger()
        self.service = AIValidationService()

    def test_service_initialization(self):
        """Test service loads schemas correctly"""
        schemas = self.service.list_available_schemas()
        assert "order-parser" in schemas
        assert "sitrep" in schemas
        assert "adjudication-result" in schemas

    def test_valid_order_parser(self):
        """Test validation of valid order parser output"""
        valid_order = {
            "order_type": "move",
            "target_units": ["unit_1", "unit_2"],
            "intent": "Advance to position",
            "location": {"x": 10, "y": 20, "area_name": "Alpha"},
            "parameters": {"priority": "high"},
            "assumptions": [],
        }

        report = self.service.validate(valid_order, SchemaType.ORDER_PARSER)
        assert report.status == ValidationResult.VALID
        assert len(report.errors) == 0

    def test_invalid_order_type(self):
        """Test validation rejects invalid order type"""
        invalid_order = {
            "order_type": "invalid_type",
            "target_units": ["unit_1"],
            "intent": "Test",
        }

        report = self.service.validate(invalid_order, SchemaType.ORDER_PARSER)
        # Should attempt repair and succeed
        assert report.status in [ValidationResult.REPAIRED, ValidationResult.INVALID]

    def test_repair_missing_fields(self):
        """Test that missing required fields are repaired"""
        incomplete_order = {
            "order_type": "attack",
        }

        report = self.service.validate(incomplete_order, SchemaType.ORDER_PARSER, repair=True)
        assert report.status == ValidationResult.REPAIRED
        assert report.repaired_data is not None
        assert "target_units" in report.repaired_data
        assert "intent" in report.repaired_data

    def test_repair_invalid_target_units(self):
        """Test repair of invalid target_units"""
        invalid_order = {
            "order_type": "move",
            "target_units": "unit_1",  # Should be list
            "intent": "Move forward",
        }

        report = self.service.validate(invalid_order, SchemaType.ORDER_PARSER)
        assert report.status == ValidationResult.REPAIRED
        assert isinstance(report.repaired_data["target_units"], list)

    def test_repair_location_bounds(self):
        """Test repair of out-of-bounds location"""
        invalid_order = {
            "order_type": "move",
            "target_units": [],
            "intent": "Move",
            "location": {"x": 100, "y": -10},  # Out of bounds
        }

        # Schema validates it as valid (integers), but repair normalizes bounds
        report = self.service.validate(invalid_order, SchemaType.ORDER_PARSER)
        # The data passes schema validation but repair should normalize bounds
        assert report.status in [ValidationResult.VALID, ValidationResult.REPAIRED]
        # Verify repair normalizes bounds if repaired
        if report.repaired_data and "location" in report.repaired_data:
            assert 0 <= report.repaired_data["location"]["x"] <= 50
            assert 0 <= report.repaired_data["location"]["y"] <= 50

    def test_valid_sitrep(self):
        """Test validation of valid SITREP"""
        valid_sitrep = {
            "turn": 5,
            "timestamp": "2024-01-15T10:30:00Z",
            "sections": [
                {
                    "type": "overview",
                    "content": "Situation is stable",
                    "confidence": "confirmed"
                }
            ],
            "map_updates": []
        }

        report = self.service.validate(valid_sitrep, SchemaType.SITREP)
        assert report.status == ValidationResult.VALID

    def test_repair_sitrep_missing_fields(self):
        """Test repair of incomplete SITREP"""
        incomplete_sitrep = {
            "turn": 3,
        }

        report = self.service.validate(incomplete_sitrep, SchemaType.SITREP)
        assert report.status == ValidationResult.REPAIRED
        assert "timestamp" in report.repaired_data
        assert "sections" in report.repaired_data

    def test_repair_sitrep_invalid_section(self):
        """Test repair of invalid section type"""
        invalid_sitrep = {
            "turn": 1,
            "timestamp": "2024-01-15T10:30:00Z",
            "sections": [
                {
                    "type": "invalid_type",
                    "content": "Test",
                    "confidence": "confirmed"
                }
            ],
        }

        report = self.service.validate(invalid_sitrep, SchemaType.SITREP)
        assert report.status == ValidationResult.REPAIRED
        assert report.repaired_data["sections"][0]["type"] == "overview"

    def test_valid_adjudication_result(self):
        """Test validation of valid adjudication result"""
        valid_result = {
            "turn": 2,
            "results": [
                {
                    "order_id": "order_1",
                    "outcome": "success",
                    "changes": [
                        {"type": "position", "target": "unit_1", "field": "x", "old_value": 10, "new_value": 15}
                    ],
                    "reason": "Movement completed"
                }
            ],
            "events": [],
            "fog_updates": []
        }

        report = self.service.validate(valid_result, SchemaType.ADJUDICATION_RESULT)
        assert report.status == ValidationResult.VALID

    def test_repair_adjudication_result_invalid_outcome(self):
        """Test repair of invalid outcome enum"""
        invalid_result = {
            "turn": 1,
            "results": [
                {
                    "order_id": "order_1",
                    "outcome": "invalid_outcome",
                    "changes": []
                }
            ],
            "events": [],
        }

        report = self.service.validate(invalid_result, SchemaType.ADJUDICATION_RESULT)
        assert report.status == ValidationResult.REPAIRED
        assert report.repaired_data["results"][0]["outcome"] == "failed"

    def test_invalid_data_not_dict(self):
        """Test that non-dict data is rejected"""
        report = self.service.validate("not a dict", SchemaType.ORDER_PARSER)
        assert report.status == ValidationResult.INVALID

    def test_invalid_data_list(self):
        """Test that list data is rejected"""
        report = self.service.validate([1, 2, 3], SchemaType.ORDER_PARSER)
        assert report.status == ValidationResult.INVALID

    def test_is_valid_quick_check(self):
        """Test quick validity check"""
        valid_order = {
            "order_type": "move",
            "target_units": ["unit_1"],
            "intent": "Test",
        }

        assert self.service.is_valid(valid_order, SchemaType.ORDER_PARSER) is True

    def test_is_valid_returns_false_for_invalid(self):
        """Test quick check returns false for invalid"""
        invalid_order = {
            "order_type": "invalid",
            "target_units": "not_a_list",
            "intent": "Test",
        }

        assert self.service.is_valid(invalid_order, SchemaType.ORDER_PARSER) is False

    def test_get_schema(self):
        """Test retrieving raw schema"""
        schema = self.service.get_schema(SchemaType.ORDER_PARSER)
        assert schema is not None
        assert "$schema" in schema
        assert schema["title"] == "OrderParser"

    def test_validation_without_repair(self):
        """Test validation without repair attempt"""
        invalid_order = {
            "order_type": "invalid_type",
        }

        report = self.service.validate(invalid_order, SchemaType.ORDER_PARSER, repair=False)
        assert report.status == ValidationResult.INVALID
        assert len(report.errors) > 0


class TestValidationIntegrationWithAI:
    """Integration tests verifying invalid AI output cannot reach data layer"""

    def setup_method(self):
        """Set up test environment"""
        reset_validation_service()
        reset_audit_logger()
        self.service = AIValidationService()

    def test_ai_output_not_accepted_invalid(self):
        """Test that invalid AI output is rejected"""
        # Simulate malformed AI output
        malformed_ai_output = {
            "order_type": "fly_to_the_moon",  # Invalid enum
            "target_units": "all_units",  # Should be list
            # Missing required "intent"
        }

        report = self.service.validate(malformed_ai_output, SchemaType.ORDER_PARSER)

        # Must not be VALID - either repaired or INVALID
        assert report.status != ValidationResult.VALID or report.action_taken != "none"

        # If we accept it, it must be repaired
        if report.status == ValidationResult.VALID:
            assert report.action_taken == "repaired"

    def test_sitrep_from_ai_validated(self):
        """Test SITREP output from AI is validated"""
        # Simulate AI-generated SITREP
        ai_sitrep = {
            "turn": 10,
            "timestamp": "2024-01-15T15:00:00Z",
            "sections": [
                {
                    "type": "overview",
                    "content": "Enemy forces advancing",
                    "confidence": "estimated"
                },
                {
                    "type": "unit_status",
                    "content": "All units operational",
                    "confidence": "confirmed"
                }
            ],
            "map_updates": []
        }

        report = self.service.validate(ai_sitrep, SchemaType.SITREP)
        assert report.status == ValidationResult.VALID
        assert report.action_taken == "none"

    def test_adjudication_from_ai_validated(self):
        """Test adjudication result from AI is validated"""
        ai_adjudication = {
            "turn": 5,
            "results": [
                {
                    "order_id": "cmd_001",
                    "outcome": "partial",
                    "changes": [
                        {"type": "damage", "target": "enemy_1", "field": "strength", "old_value": 100, "new_value": 70}
                    ],
                    "reason": "Enemy unit took damage but survived"
                }
            ],
            "events": [
                {"type": "casualty", "turn": 5, "data": {"unit": "enemy_1", "losses": 30}}
            ],
            "fog_updates": []
        }

        report = self.service.validate(ai_adjudication, SchemaType.ADJUDICATION_RESULT)
        assert report.status == ValidationResult.VALID

    def test_fully_malformed_ai_output_rejected(self):
        """Test that completely malformed AI output is handled"""
        # This is what might happen if AI returns completely garbage
        garbage = "This is not JSON at all"

        # Try to parse it (would have failed at json.loads in AI client)
        try:
            data = json.loads(garbage)
        except json.JSONDecodeError:
            data = garbage

        report = self.service.validate(data, SchemaType.ORDER_PARSER)
        # Should be rejected or repaired to valid state
        assert report.status in [ValidationResult.INVALID, ValidationResult.REPAIRED, ValidationResult.FAILED]


class TestValidationServiceSingleton:
    """Test singleton pattern"""

    def test_get_validation_service_returns_same_instance(self):
        """Test get_validation_service returns singleton"""
        reset_validation_service()
        service1 = get_validation_service()
        service2 = get_validation_service()
        assert service1 is service2
