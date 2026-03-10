# Sync Matrix Service - CPX-SYNC: Time x Effect Synchronization
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import json
import csv
from io import StringIO


@dataclass
class SyncMatrixEntryData:
    """Individual entry in sync matrix"""
    phase: str
    effect: str
    value: Optional[str] = None
    notes: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    linked_opord_id: Optional[int] = None
    linked_ato_mission_id: Optional[int] = None
    linked_inject_id: Optional[str] = None


@dataclass
class SyncMatrixData:
    """Sync matrix data structure"""
    matrix_id: Optional[int] = None
    game_id: int = 0
    name: str = "Default Sync Matrix"
    description: Optional[str] = None
    phases: List[str] = field(default_factory=lambda: ["Phase 1", "Phase 2", "Phase 3", "Phase 4"])
    effects: List[str] = field(default_factory=lambda: ["Recon", "Fires", "Maneuver", "Logistics"])
    resolution: str = "turn"
    matrix_data: Dict[str, Any] = field(default_factory=dict)
    status: str = "draft"
    created_at: str = ""
    updated_at: str = ""
    created_by: Optional[str] = None


class SyncMatrixService:
    """
    Service for managing Sync Matrix (CPX-SYNC)

    Provides timeline (phase/resolution) x effect (Recon/Fires/Maneuver/Logistics)
    synchronization planning, linked with OPORD/ATO/Inject.
    """

    DEFAULT_PHASES = ["Phase 1", "Phase 2", "Phase 3", "Phase 4"]
    DEFAULT_EFFECTS = ["Recon", "Fires", "Maneuver", "Logistics"]
    EFFECT_COLORS = {
        "Recon": "#22c55e",  # green
        "Fires": "#ef4444",  # red
        "Maneuver": "#3b82f6",  # blue
        "Logistics": "#f59e0b",  # amber
    }

    def __init__(self):
        self._current_matrix: Optional[SyncMatrixData] = None

    def create_default_matrix(
        self,
        game_id: int,
        name: str = "Default Sync Matrix",
        created_by: Optional[str] = None
    ) -> SyncMatrixData:
        """Create a default sync matrix with standard phases and effects"""
        now = datetime.now().isoformat()

        # Create copies to avoid mutating class-level constants
        phases = list(self.DEFAULT_PHASES)
        effects = list(self.DEFAULT_EFFECTS)

        # Initialize empty matrix structure
        matrix_data = {}
        for phase in phases:
            matrix_data[phase] = {}
            for effect in effects:
                matrix_data[phase][effect] = {
                    "value": None,
                    "notes": "",
                    "start_time": None,
                    "end_time": None,
                }

        self._current_matrix = SyncMatrixData(
            game_id=game_id,
            name=name,
            phases=phases,
            effects=effects,
            resolution="turn",
            matrix_data=matrix_data,
            status="draft",
            created_at=now,
            updated_at=now,
            created_by=created_by
        )

        return self._current_matrix

    def get_current_matrix(self) -> Optional[SyncMatrixData]:
        """Get the current sync matrix"""
        return self._current_matrix

    def set_matrix(self, matrix: SyncMatrixData) -> None:
        """Set the current sync matrix"""
        self._current_matrix = matrix

    def update_entry(
        self,
        phase: str,
        effect: str,
        value: Optional[str] = None,
        notes: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        linked_opord_id: Optional[int] = None,
        linked_ato_mission_id: Optional[int] = None,
        linked_inject_id: Optional[str] = None
    ) -> SyncMatrixData:
        """Update a single entry in the matrix"""
        if self._current_matrix is None:
            raise ValueError("No current matrix exists. Call create_default_matrix first.")

        if phase not in self._current_matrix.phases:
            raise ValueError(f"Unknown phase: {phase}")
        if effect not in self._current_matrix.effects:
            raise ValueError(f"Unknown effect: {effect}")

        entry = self._current_matrix.matrix_data.get(phase, {}).get(effect, {})

        if value is not None:
            entry["value"] = value
        if notes is not None:
            entry["notes"] = notes
        if start_time is not None:
            entry["start_time"] = start_time
        if end_time is not None:
            entry["end_time"] = end_time
        if linked_opord_id is not None:
            entry["linked_opord_id"] = linked_opord_id
        if linked_ato_mission_id is not None:
            entry["linked_ato_mission_id"] = linked_ato_mission_id
        if linked_inject_id is not None:
            entry["linked_inject_id"] = linked_inject_id

        if phase not in self._current_matrix.matrix_data:
            self._current_matrix.matrix_data[phase] = {}
        self._current_matrix.matrix_data[phase][effect] = entry

        self._current_matrix.updated_at = datetime.now().isoformat()

        return self._current_matrix

    def get_entry(self, phase: str, effect: str) -> Optional[Dict[str, Any]]:
        """Get a specific entry from the matrix"""
        if self._current_matrix is None:
            return None

        return self._current_matrix.matrix_data.get(phase, {}).get(effect)

    def add_phase(self, phase_name: str) -> SyncMatrixData:
        """Add a new phase to the matrix"""
        if self._current_matrix is None:
            raise ValueError("No current matrix exists.")

        if phase_name in self._current_matrix.phases:
            raise ValueError(f"Phase already exists: {phase_name}")

        self._current_matrix.phases.append(phase_name)

        # Initialize entries for new phase
        if phase_name not in self._current_matrix.matrix_data:
            self._current_matrix.matrix_data[phase_name] = {}

        for effect in self._current_matrix.effects:
            self._current_matrix.matrix_data[phase_name][effect] = {
                "value": None,
                "notes": "",
                "start_time": None,
                "end_time": None,
            }

        self._current_matrix.updated_at = datetime.now().isoformat()
        return self._current_matrix

    def add_effect(self, effect_name: str) -> SyncMatrixData:
        """Add a new effect to the matrix"""
        if self._current_matrix is None:
            raise ValueError("No current matrix exists.")

        if effect_name in self._current_matrix.effects:
            raise ValueError(f"Effect already exists: {effect_name}")

        self._current_matrix.effects.append(effect_name)

        # Initialize entries for new effect
        for phase in self._current_matrix.phases:
            if phase not in self._current_matrix.matrix_data:
                self._current_matrix.matrix_data[phase] = {}
            self._current_matrix.matrix_data[phase][effect_name] = {
                "value": None,
                "notes": "",
                "start_time": None,
                "end_time": None,
            }

        self._current_matrix.updated_at = datetime.now().isoformat()
        return self._current_matrix

    def remove_phase(self, phase_name: str) -> SyncMatrixData:
        """Remove a phase from the matrix"""
        if self._current_matrix is None:
            raise ValueError("No current matrix exists.")

        if phase_name not in self._current_matrix.phases:
            raise ValueError(f"Phase not found: {phase_name}")

        self._current_matrix.phases.remove(phase_name)
        if phase_name in self._current_matrix.matrix_data:
            del self._current_matrix.matrix_data[phase_name]

        self._current_matrix.updated_at = datetime.now().isoformat()
        return self._current_matrix

    def remove_effect(self, effect_name: str) -> SyncMatrixData:
        """Remove an effect from the matrix"""
        if self._current_matrix is None:
            raise ValueError("No current matrix exists.")

        if effect_name not in self._current_matrix.effects:
            raise ValueError(f"Effect not found: {effect_name}")

        self._current_matrix.effects.remove(effect_name)

        # Remove effect from all phases
        for phase in self._current_matrix.phases:
            if phase in self._current_matrix.matrix_data:
                if effect_name in self._current_matrix.matrix_data[phase]:
                    del self._current_matrix.matrix_data[phase][effect_name]

        self._current_matrix.updated_at = datetime.now().isoformat()
        return self._current_matrix

    def to_dict(self) -> Dict[str, Any]:
        """Convert sync matrix to dictionary for API response"""
        if self._current_matrix is None:
            return {}

        matrix = self._current_matrix
        return {
            "matrix_id": matrix.matrix_id,
            "game_id": matrix.game_id,
            "name": matrix.name,
            "description": matrix.description,
            "phases": matrix.phases,
            "effects": matrix.effects,
            "resolution": matrix.resolution,
            "matrix_data": matrix.matrix_data,
            "status": matrix.status,
            "effect_colors": self.EFFECT_COLORS,
            "created_at": matrix.created_at,
            "updated_at": matrix.updated_at,
            "created_by": matrix.created_by
        }

    def format_for_display(self) -> str:
        """Format sync matrix for display"""
        if self._current_matrix is None:
            return "No active sync matrix"

        matrix = self._current_matrix
        lines = [
            f"【Sync Matrix: {matrix.name}】",
            f"Resolution: {matrix.resolution} | Status: {matrix.status}",
            "",
            "Phases: " + " | ".join(matrix.phases),
            "Effects: " + " | ".join(matrix.effects),
            "",
            "=== Matrix ===",
        ]

        # Header row
        header = ["Phase\\Effect"] + matrix.effects
        lines.append(" | ".join(header))
        lines.append("-" * 60)

        # Data rows
        for phase in matrix.phases:
            row = [phase]
            for effect in matrix.effects:
                entry = matrix.matrix_data.get(phase, {}).get(effect, {})
                value = entry.get("value", "-") or "-"
                row.append(str(value))
            lines.append(" | ".join(row))

        return "\n".join(lines)

    def export_to_csv(self) -> str:
        """Export sync matrix to CSV format"""
        if self._current_matrix is None:
            return ""

        matrix = self._current_matrix
        output = StringIO()
        writer = csv.writer(output)

        # Header
        header = ["Phase", "Effect", "Value", "Notes", "Start Time", "End Time",
                  "Linked OPORD", "Linked ATO Mission", "Linked Inject"]
        writer.writerow(header)

        # Data rows
        for phase in matrix.phases:
            for effect in matrix.effects:
                entry = matrix.matrix_data.get(phase, {}).get(effect, {})
                row = [
                    phase,
                    effect,
                    entry.get("value", ""),
                    entry.get("notes", ""),
                    entry.get("start_time", ""),
                    entry.get("end_time", ""),
                    entry.get("linked_opord_id", ""),
                    entry.get("linked_ato_mission_id", ""),
                    entry.get("linked_inject_id", ""),
                ]
                writer.writerow(row)

        return output.getvalue()

    def export_to_json(self) -> Dict[str, Any]:
        """Export sync matrix to JSON format"""
        return self.to_dict()


# Global instance
_sync_matrix_service = SyncMatrixService()


def get_sync_matrix_service() -> SyncMatrixService:
    """Get the global sync matrix service"""
    return _sync_matrix_service


# =============================================================================
# Database Persistence Methods for Sync Matrix
# =============================================================================

def _dataclass_to_dict(obj) -> dict:
    """Convert a dataclass to a dictionary"""
    if obj is None:
        return {}
    if hasattr(obj, '__dataclassfields__'):
        result = {}
        for field in obj.__dataclassfields__.keys():
            value = getattr(obj, field, None)
            if value is not None:
                if hasattr(value, '__dataclassfields__'):
                    result[field] = _dataclass_to_dict(value)
                elif isinstance(value, list):
                    result[field] = [
                        _dataclass_to_dict(v) if hasattr(v, '__dataclassfields__') else v
                        for v in value
                    ]
                else:
                    result[field] = value
        return result
    return {}


class SyncMatrixPersistenceService:
    """Service for persisting Sync Matrix to database"""

    def __init__(self, db):
        self.db = db

    def save_matrix(self, matrix: SyncMatrixData, status: str = "draft") -> "SyncMatrix":
        """Save a sync matrix to the database"""
        from app.models import SyncMatrix

        matrix_record = SyncMatrix(
            game_id=matrix.game_id,
            name=matrix.name,
            description=matrix.description,
            phases=matrix.phases,
            effects=matrix.effects,
            resolution=matrix.resolution,
            matrix_data=matrix.matrix_data,
            status=status,
            created_by=matrix.created_by
        )

        self.db.add(matrix_record)
        self.db.commit()
        self.db.refresh(matrix_record)
        return matrix_record

    def load_matrix(self, game_id: int) -> Optional[SyncMatrixData]:
        """Load the latest sync matrix for a game"""
        from app.models import SyncMatrix

        matrix_record = self.db.query(SyncMatrix).filter(
            SyncMatrix.game_id == game_id
        ).order_by(SyncMatrix.updated_at.desc()).first()

        if not matrix_record:
            return None

        return self._record_to_matrix_data(matrix_record)

    def _record_to_matrix_data(self, record: "SyncMatrix") -> SyncMatrixData:
        """Convert database record to SyncMatrixData"""
        return SyncMatrixData(
            matrix_id=record.id,
            game_id=record.game_id,
            name=record.name,
            description=record.description,
            phases=record.phases or self.DEFAULT_PHASES,
            effects=record.effects or self.DEFAULT_EFFECTS,
            resolution=record.resolution or "turn",
            matrix_data=record.matrix_data or {},
            status=record.status or "draft",
            created_at=record.created_at.isoformat() if record.created_at else "",
            updated_at=record.updated_at.isoformat() if record.updated_at else "",
            created_by=record.created_by
        )

    def get_matrix_versions(self, game_id: int) -> list[dict]:
        """Get all versions of sync matrix for a game"""
        from app.models import SyncMatrix

        records = self.db.query(SyncMatrix).filter(
            SyncMatrix.game_id == game_id
        ).order_by(SyncMatrix.updated_at.desc()).all()

        return [
            {
                "id": r.id,
                "name": r.name,
                "status": r.status,
                "created_by": r.created_by,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None
            }
            for r in records
        ]

    def update_matrix_entry(
        self,
        matrix_id: int,
        phase: str,
        effect: str,
        value: Optional[str] = None,
        notes: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        linked_opord_id: Optional[int] = None,
        linked_ato_mission_id: Optional[int] = None,
        linked_inject_id: Optional[str] = None
    ) -> Optional["SyncMatrix"]:
        """Update a specific entry in the matrix"""
        from app.models import SyncMatrix

        matrix_record = self.db.query(SyncMatrix).filter(
            SyncMatrix.id == matrix_id
        ).first()

        if not matrix_record:
            return None

        # Get current matrix data
        matrix_data = matrix_record.matrix_data or {}

        # Initialize phase if needed
        if phase not in matrix_data:
            matrix_data[phase] = {}

        # Get or initialize entry
        entry = matrix_data[phase].get(effect, {})

        # Update fields
        if value is not None:
            entry["value"] = value
        if notes is not None:
            entry["notes"] = notes
        if start_time is not None:
            entry["start_time"] = start_time
        if end_time is not None:
            entry["end_time"] = end_time
        if linked_opord_id is not None:
            entry["linked_opord_id"] = linked_opord_id
        if linked_ato_mission_id is not None:
            entry["linked_ato_mission_id"] = linked_ato_mission_id
        if linked_inject_id is not None:
            entry["linked_inject_id"] = linked_inject_id

        matrix_data[phase][effect] = entry
        matrix_record.matrix_data = matrix_data

        self.db.commit()
        self.db.refresh(matrix_record)
        return matrix_record
