# AI Output Validation Service - CPX-VALIDATION
# Validates AI outputs against JSON schemas with fallback handling

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

import jsonschema
from jsonschema import ValidationError

from app.services.audit_logger import (
    AuditEventType,
    AuditSeverity,
    get_audit_logger,
)


logger = logging.getLogger(__name__)


class SchemaType(Enum):
    """Supported schema types for validation"""
    ORDER_PARSER = "order-parser"
    SITREP = "sitrep"
    ADJUDICATION_RESULT = "adjudication-result"
    AAR = "aar"


class ValidationResult(Enum):
    """Validation result status"""
    VALID = "valid"
    INVALID = "invalid"
    REPAIRED = "repaired"
    FAILED = "failed"


@dataclass
class ValidationReport:
    """Report of validation result"""
    status: ValidationResult
    schema_type: SchemaType
    original_data: Dict[str, Any]
    errors: List[str]
    repaired_data: Optional[Dict[str, Any]] = None
    action_taken: str = "none"


class AIValidationService:
    """
    Validates AI outputs against JSON schemas with fallback and repair capabilities.
    Ensures no invalid data reaches the data layer.
    """

    def __init__(self, schema_dir: Optional[Path] = None):
        """
        Initialize validation service.

        Args:
            schema_dir: Directory containing schema files. Defaults to shared/schemas
        """
        if schema_dir is None:
            # Default to shared/schemas relative to backend
            schema_dir = Path(__file__).parent.parent.parent.parent / "shared" / "schemas"

        self.schema_dir = schema_dir
        self._schemas: Dict[SchemaType, Dict[str, Any]] = {}
        self._audit_logger = get_audit_logger()
        self._load_schemas()

    def _load_schemas(self) -> None:
        """Load all available schemas from disk"""
        schema_map = {
            SchemaType.ORDER_PARSER: "order-parser.schema.json",
            SchemaType.SITREP: "sitrep.schema.json",
            SchemaType.ADJUDICATION_RESULT: "adjudication-result.schema.json",
            SchemaType.AAR: "aar.schema.json",
        }

        for schema_type, filename in schema_map.items():
            schema_path = self.schema_dir / filename
            if schema_path.exists():
                try:
                    with open(schema_path, "r", encoding="utf-8") as f:
                        self._schemas[schema_type] = json.load(f)
                    logger.info(f"Loaded schema: {filename}")
                except Exception as e:
                    logger.error(f"Failed to load schema {filename}: {e}")
            else:
                logger.warning(f"Schema not found: {schema_path}")

    def validate(
        self,
        data: Any,
        schema_type: SchemaType,
        repair: bool = True,
    ) -> ValidationReport:
        """
        Validate data against a schema with optional repair.

        Args:
            data: Data to validate (dict from JSON parsing)
            schema_type: Type of schema to validate against
            repair: Whether to attempt repair on invalid data

        Returns:
            ValidationReport with status and details
        """
        # Ensure data is a dict
        if not isinstance(data, dict):
            return self._create_error_report(
                schema_type,
                data,
                ["Data is not a valid JSON object"],
                ValidationResult.INVALID,
            )

        schema = self._schemas.get(schema_type)
        if not schema:
            return self._create_error_report(
                schema_type,
                data,
                [f"Schema not loaded: {schema_type.value}"],
                ValidationResult.FAILED,
            )

        # First attempt: direct validation
        errors = self._validate_against_schema(data, schema)
        if not errors:
            return ValidationReport(
                status=ValidationResult.VALID,
                schema_type=schema_type,
                original_data=data,
                errors=[],
                action_taken="none",
            )

        # Second attempt: try repair if enabled
        if repair:
            repaired = self._attempt_repair(data, schema_type)
            repair_errors = self._validate_against_schema(repaired, schema)

            if not repair_errors:
                self._log_validation_event(
                    schema_type,
                    "repair_success",
                    errors,
                    data,
                )
                return ValidationReport(
                    status=ValidationResult.REPAIRED,
                    schema_type=schema_type,
                    original_data=data,
                    errors=errors,
                    repaired_data=repaired,
                    action_taken="repaired",
                )

        # All attempts failed - log and return failure
        self._log_validation_event(
            schema_type,
            "validation_failed",
            errors,
            data,
        )

        return ValidationReport(
            status=ValidationResult.INVALID,
            schema_type=schema_type,
            original_data=data,
            errors=errors,
            action_taken="rejected",
        )

    def _validate_against_schema(
        self,
        data: Dict[str, Any],
        schema: Dict[str, Any],
    ) -> List[str]:
        """Validate data against schema and return list of errors"""
        validator = jsonschema.Draft7Validator(schema)
        errors = []

        for error in validator.iter_errors(data):
            path = ".".join(str(p) for p in error.path) if error.path else "root"
            errors.append(f"{path}: {error.message}")

        return errors

    def _attempt_repair(
        self,
        data: Dict[str, Any],
        schema_type: SchemaType,
    ) -> Dict[str, Any]:
        """
        Attempt to repair invalid data to match schema.
        Returns repaired data or original if repair is not possible.
        """
        repaired = data.copy()

        # Type-specific repair strategies
        if schema_type == SchemaType.ORDER_PARSER:
            repaired = self._repair_order_parser(repaired)
        elif schema_type == SchemaType.SITREP:
            repaired = self._repair_sitrep(repaired)
        elif schema_type == SchemaType.ADJUDICATION_RESULT:
            repaired = self._repair_adjudication_result(repaired)

        return repaired

    def _repair_order_parser(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Repair order parser output"""
        repaired = data.copy()

        # Ensure required fields exist
        if "order_type" not in repaired:
            repaired["order_type"] = "move"
        else:
            valid_types = ["move", "attack", "defend", "support", "retreat", "recon", "supply", "special"]
            if repaired["order_type"] not in valid_types:
                repaired["order_type"] = "move"

        # Ensure target_units is a list
        if "target_units" not in repaired:
            repaired["target_units"] = []
        elif not isinstance(repaired["target_units"], list):
            repaired["target_units"] = [repaired["target_units"]] if repaired["target_units"] else []

        # Ensure intent exists
        if "intent" not in repaired or not repaired["intent"]:
            repaired["intent"] = repaired.get("intent", "Unknown order")

        # Ensure parameters is an object
        if "parameters" not in repaired or not isinstance(repaired["parameters"], dict):
            repaired["parameters"] = {"priority": "normal"}

        # Ensure location is valid if present, remove if None or invalid
        if "location" in repaired:
            if repaired["location"] is None or repaired["location"] == {}:
                # Remove null/empty location as it's optional in schema
                del repaired["location"]
            elif isinstance(repaired["location"], dict):
                if "x" in repaired["location"]:
                    repaired["location"]["x"] = max(0, min(50, repaired["location"]["x"]))
                if "y" in repaired["location"]:
                    repaired["location"]["y"] = max(0, min(50, repaired["location"]["y"]))

        # Ensure assumptions is a list
        if "assumptions" not in repaired:
            repaired["assumptions"] = []

        return repaired

    def _repair_sitrep(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Repair SITREP output"""
        repaired = data.copy()

        # Ensure turn exists
        if "turn" not in repaired:
            repaired["turn"] = 1

        # Ensure timestamp exists
        if "timestamp" not in repaired:
            from datetime import datetime
            repaired["timestamp"] = datetime.utcnow().isoformat() + "Z"

        # Ensure sections is a list
        if "sections" not in repaired:
            repaired["sections"] = []
        elif not isinstance(repaired["sections"], list):
            repaired["sections"] = [repaired["sections"]] if repaired["sections"] else []

        # Repair each section
        valid_section_types = ["overview", "unit_status", "enemy_activity", "logistics", "orders_result", "friction", "command"]
        valid_confidences = ["confirmed", "estimated", "unknown"]

        repaired_sections = []
        for section in repaired["sections"]:
            if not isinstance(section, dict):
                continue

            # Ensure type is valid
            section_type = section.get("type", "overview")
            if section_type not in valid_section_types:
                section_type = "overview"

            # Ensure content exists
            content = section.get("content", "")
            if not content:
                content = "No information available."

            # Ensure confidence is valid
            confidence = section.get("confidence", "confirmed")
            if confidence not in valid_confidences:
                confidence = "confirmed"

            repaired_sections.append({
                "type": section_type,
                "content": content,
                "confidence": confidence,
            })

        repaired["sections"] = repaired_sections

        # Ensure map_updates is a list
        if "map_updates" not in repaired:
            repaired["map_updates"] = []

        return repaired

    def _repair_adjudication_result(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Repair adjudication result output"""
        repaired = data.copy()

        # Ensure turn exists
        if "turn" not in repaired:
            repaired["turn"] = 1

        # Ensure results is a list
        if "results" not in repaired:
            repaired["results"] = []
        elif not isinstance(repaired["results"], list):
            repaired["results"] = [repaired["results"]] if repaired["results"] else []

        # Ensure events is a list
        if "events" not in repaired:
            repaired["events"] = []
        elif not isinstance(repaired["events"], list):
            repaired["events"] = [repaired["events"]] if repaired["events"] else []

        # Repair each result
        valid_outcomes = ["success", "partial", "failed", "blocked", "cancelled"]

        repaired_results = []
        for result in repaired["results"]:
            if not isinstance(result, dict):
                continue

            # Ensure required fields
            if "order_id" not in result:
                result["order_id"] = "unknown"
            if "outcome" not in result or result["outcome"] not in valid_outcomes:
                result["outcome"] = "failed"
            if "changes" not in result or not isinstance(result["changes"], list):
                result["changes"] = []

            repaired_results.append(result)

        repaired["results"] = repaired_results

        # Ensure fog_updates is a list
        if "fog_updates" not in repaired:
            repaired["fog_updates"] = []

        return repaired

    def _create_error_report(
        self,
        schema_type: SchemaType,
        original_data: Any,
        errors: List[str],
        status: ValidationResult,
    ) -> ValidationReport:
        """Create an error report"""
        return ValidationReport(
            status=status,
            schema_type=schema_type,
            original_data=original_data if isinstance(original_data, dict) else {},
            errors=errors,
            action_taken="rejected",
        )

    def _log_validation_event(
        self,
        schema_type: SchemaType,
        action: str,
        errors: List[str],
        original_data: Dict[str, Any],
    ) -> None:
        """Log validation failure to audit logger"""
        try:
            # Determine severity based on action
            severity = AuditSeverity.WARNING
            if action == "validation_failed":
                severity = AuditSeverity.ERROR

            # Truncate data for log (avoid huge logs)
            data_preview = str(original_data)[:500] if original_data else ""

            self._audit_logger.log_event(
                event_type=AuditEventType.INVALID_REQUEST,
                action=f"ai_validation_{action}",
                result="failure" if "failed" in action else "success",
                severity=severity,
                resource_type="ai_output",
                resource_id=schema_type.value,
                details={
                    "schema_type": schema_type.value,
                    "error_count": len(errors),
                    "errors": errors[:10],  # Limit errors logged
                    "data_preview": data_preview,
                },
            )
        except Exception as e:
            logger.error(f"Failed to log validation event: {e}")

    def is_valid(self, data: Any, schema_type: SchemaType) -> bool:
        """
        Quick check if data is valid for a schema.
        Does not attempt repair - use validate() for that.

        Args:
            data: Data to check
            schema_type: Schema type to validate against

        Returns:
            True if valid, False otherwise
        """
        schema = self._schemas.get(schema_type)
        if not schema or not isinstance(data, dict):
            return False

        validator = jsonschema.Draft7Validator(schema)
        return validator.is_valid(data)

    def get_schema(self, schema_type: SchemaType) -> Optional[Dict[str, Any]]:
        """Get raw schema for a type"""
        return self._schemas.get(schema_type)

    def list_available_schemas(self) -> List[str]:
        """List available schema types"""
        return [st.value for st in SchemaType]


# Global validation service instance
_validation_service: Optional[AIValidationService] = None


def get_validation_service() -> AIValidationService:
    """Get the global validation service instance"""
    global _validation_service
    if _validation_service is None:
        _validation_service = AIValidationService()
    return _validation_service


def reset_validation_service() -> None:
    """Reset the global validation service (for testing)"""
    global _validation_service
    _validation_service = None
