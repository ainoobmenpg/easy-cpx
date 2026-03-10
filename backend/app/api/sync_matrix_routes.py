# Sync Matrix API Routes - CPX-SYNC
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from app.database import get_db
from app.models import SyncMatrix
from datetime import datetime

router = APIRouter()


# Request/Response models
class SyncMatrixCreate(BaseModel):
    game_id: int
    name: str = "Default Sync Matrix"
    description: Optional[str] = None
    phases: Optional[List[str]] = None
    effects: Optional[List[str]] = None
    resolution: str = "turn"
    created_by: Optional[str] = None


class SyncMatrixUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    phases: Optional[List[str]] = None
    effects: Optional[List[str]] = None
    resolution: Optional[str] = None
    status: Optional[str] = None


class SyncMatrixEntryUpdate(BaseModel):
    phase: str
    effect: str
    value: Optional[str] = None
    notes: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    linked_opord_id: Optional[int] = None
    linked_ato_mission_id: Optional[int] = None
    linked_inject_id: Optional[str] = None


class SyncMatrixEntryResponse(BaseModel):
    phase: str
    effect: str
    value: Optional[str]
    notes: Optional[str]
    start_time: Optional[str]
    end_time: Optional[str]
    linked_opord_id: Optional[int]
    linked_ato_mission_id: Optional[int]
    linked_inject_id: Optional[str]


class SyncMatrixResponse(BaseModel):
    id: int
    game_id: int
    name: str
    description: Optional[str]
    phases: List[str]
    effects: List[str]
    resolution: str
    matrix_data: Dict[str, Any]
    status: str
    created_at: str
    updated_at: str
    created_by: Optional[str]


# Effect colors for frontend
EFFECT_COLORS = {
    "Recon": "#22c55e",
    "Fires": "#ef4444",
    "Maneuver": "#3b82f6",
    "Logistics": "#f59e0b",
}


# Default phases and effects
DEFAULT_PHASES = ["Phase 1", "Phase 2", "Phase 3", "Phase 4"]
DEFAULT_EFFECTS = ["Recon", "Fires", "Maneuver", "Logistics"]


def _init_matrix_data(phases: List[str], effects: List[str]) -> Dict[str, Any]:
    """Initialize empty matrix data structure"""
    matrix_data = {}
    for phase in phases:
        matrix_data[phase] = {}
        for effect in effects:
            matrix_data[phase][effect] = {
                "value": None,
                "notes": "",
                "start_time": None,
                "end_time": None,
                "linked_opord_id": None,
                "linked_ato_mission_id": None,
                "linked_inject_id": None,
            }
    return matrix_data


@router.post("/sync/matrices", response_model=SyncMatrixResponse)
def create_sync_matrix(
    matrix: SyncMatrixCreate,
    db: Session = Depends(get_db)
):
    """Create a new sync matrix"""
    phases = matrix.phases or DEFAULT_PHASES
    effects = matrix.effects or DEFAULT_EFFECTS

    db_matrix = SyncMatrix(
        game_id=matrix.game_id,
        name=matrix.name,
        description=matrix.description,
        phases=phases,
        effects=effects,
        resolution=matrix.resolution,
        matrix_data=_init_matrix_data(phases, effects),
        status="draft",
        created_by=matrix.created_by
    )
    db.add(db_matrix)
    db.commit()
    db.refresh(db_matrix)

    return SyncMatrixResponse(
        id=db_matrix.id,
        game_id=db_matrix.game_id,
        name=db_matrix.name,
        description=db_matrix.description,
        phases=db_matrix.phases,
        effects=db_matrix.effects,
        resolution=db_matrix.resolution,
        matrix_data=db_matrix.matrix_data,
        status=db_matrix.status,
        created_at=db_matrix.created_at.isoformat(),
        updated_at=db_matrix.updated_at.isoformat(),
        created_by=db_matrix.created_by
    )


@router.get("/sync/matrices/{game_id}", response_model=SyncMatrixResponse)
def get_sync_matrix(
    game_id: int,
    db: Session = Depends(get_db)
):
    """Get the latest sync matrix for a game"""
    matrix = db.query(SyncMatrix).filter(
        SyncMatrix.game_id == game_id
    ).order_by(SyncMatrix.updated_at.desc()).first()

    if not matrix:
        # Return default matrix structure
        return SyncMatrixResponse(
            id=0,
            game_id=game_id,
            name="Default Sync Matrix",
            description=None,
            phases=DEFAULT_PHASES,
            effects=DEFAULT_EFFECTS,
            resolution="turn",
            matrix_data=_init_matrix_data(DEFAULT_PHASES, DEFAULT_EFFECTS),
            status="draft",
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat(),
            created_by=None
        )

    return SyncMatrixResponse(
        id=matrix.id,
        game_id=matrix.game_id,
        name=matrix.name,
        description=matrix.description,
        phases=matrix.phases,
        effects=matrix.effects,
        resolution=matrix.resolution,
        matrix_data=matrix.matrix_data,
        status=matrix.status,
        created_at=matrix.created_at.isoformat(),
        updated_at=matrix.updated_at.isoformat(),
        created_by=matrix.created_by
    )


@router.put("/sync/matrices/{game_id}/{matrix_id}", response_model=SyncMatrixResponse)
def update_sync_matrix(
    game_id: int,
    matrix_id: int,
    update: SyncMatrixUpdate,
    db: Session = Depends(get_db)
):
    """Update sync matrix metadata"""
    matrix = db.query(SyncMatrix).filter(
        SyncMatrix.id == matrix_id,
        SyncMatrix.game_id == game_id
    ).first()

    if not matrix:
        raise HTTPException(status_code=404, detail="Sync matrix not found")

    if update.name is not None:
        matrix.name = update.name
    if update.description is not None:
        matrix.description = update.description
    if update.phases is not None:
        matrix.phases = update.phases
    if update.effects is not None:
        matrix.effects = update.effects
    if update.resolution is not None:
        matrix.resolution = update.resolution
    if update.status is not None:
        matrix.status = update.status

    db.commit()
    db.refresh(matrix)

    return SyncMatrixResponse(
        id=matrix.id,
        game_id=matrix.game_id,
        name=matrix.name,
        description=matrix.description,
        phases=matrix.phases,
        effects=matrix.effects,
        resolution=matrix.resolution,
        matrix_data=matrix.matrix_data,
        status=matrix.status,
        created_at=matrix.created_at.isoformat(),
        updated_at=matrix.updated_at.isoformat(),
        created_by=matrix.created_by
    )


@router.put("/sync/matrices/{game_id}/{matrix_id}/entry", response_model=SyncMatrixResponse)
def update_matrix_entry(
    game_id: int,
    matrix_id: int,
    entry: SyncMatrixEntryUpdate,
    db: Session = Depends(get_db)
):
    """Update a specific entry in the sync matrix"""
    matrix = db.query(SyncMatrix).filter(
        SyncMatrix.id == matrix_id,
        SyncMatrix.game_id == game_id
    ).first()

    if not matrix:
        raise HTTPException(status_code=404, detail="Sync matrix not found")

    # Get or initialize matrix data
    matrix_data = matrix.matrix_data or {}

    # Initialize phase if needed
    if entry.phase not in matrix_data:
        matrix_data[entry.phase] = {}

    # Get or initialize entry
    current_entry = matrix_data[entry.phase].get(entry.effect, {})

    # Update fields
    if entry.value is not None:
        current_entry["value"] = entry.value
    if entry.notes is not None:
        current_entry["notes"] = entry.notes
    if entry.start_time is not None:
        current_entry["start_time"] = entry.start_time
    if entry.end_time is not None:
        current_entry["end_time"] = entry.end_time
    if entry.linked_opord_id is not None:
        current_entry["linked_opord_id"] = entry.linked_opord_id
    if entry.linked_ato_mission_id is not None:
        current_entry["linked_ato_mission_id"] = entry.linked_ato_mission_id
    if entry.linked_inject_id is not None:
        current_entry["linked_inject_id"] = entry.linked_inject_id

    matrix_data[entry.phase][entry.effect] = current_entry
    matrix.matrix_data = matrix_data

    db.commit()
    db.refresh(matrix)

    return SyncMatrixResponse(
        id=matrix.id,
        game_id=matrix.game_id,
        name=matrix.name,
        description=matrix.description,
        phases=matrix.phases,
        effects=matrix.effects,
        resolution=matrix.resolution,
        matrix_data=matrix.matrix_data,
        status=matrix.status,
        created_at=matrix.created_at.isoformat(),
        updated_at=matrix.updated_at.isoformat(),
        created_by=matrix.created_by
    )


@router.get("/sync/matrices/{game_id}/export/csv")
def export_sync_matrix_csv(
    game_id: int,
    db: Session = Depends(get_db)
):
    """Export sync matrix as CSV"""
    import csv
    from io import StringIO

    matrix = db.query(SyncMatrix).filter(
        SyncMatrix.game_id == game_id
    ).order_by(SyncMatrix.updated_at.desc()).first()

    if not matrix:
        phases = DEFAULT_PHASES
        effects = DEFAULT_EFFECTS
        matrix_data = _init_matrix_data(phases, effects)
    else:
        phases = matrix.phases
        effects = matrix.effects
        matrix_data = matrix.matrix_data or {}

    output = StringIO()
    writer = csv.writer(output)

    # Header
    header = ["Phase", "Effect", "Value", "Notes", "Start Time", "End Time",
              "Linked OPORD", "Linked ATO Mission", "Linked Inject"]
    writer.writerow(header)

    # Data rows
    for phase in phases:
        for effect in effects:
            entry = matrix_data.get(phase, {}).get(effect, {})
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

    return {
        "filename": f"sync_matrix_{game_id}.csv",
        "content": output.getvalue()
    }


@router.get("/sync/matrices/{game_id}/export/json")
def export_sync_matrix_json(
    game_id: int,
    db: Session = Depends(get_db)
):
    """Export sync matrix as JSON"""
    matrix = db.query(SyncMatrix).filter(
        SyncMatrix.game_id == game_id
    ).order_by(SyncMatrix.updated_at.desc()).first()

    if not matrix:
        return {
            "game_id": game_id,
            "name": "Default Sync Matrix",
            "phases": DEFAULT_PHASES,
            "effects": DEFAULT_EFFECTS,
            "resolution": "turn",
            "matrix_data": _init_matrix_data(DEFAULT_PHASES, DEFAULT_EFFECTS),
            "status": "draft",
            "effect_colors": EFFECT_COLORS
        }

    return {
        "id": matrix.id,
        "game_id": matrix.game_id,
        "name": matrix.name,
        "description": matrix.description,
        "phases": matrix.phases,
        "effects": matrix.effects,
        "resolution": matrix.resolution,
        "matrix_data": matrix.matrix_data,
        "status": matrix.status,
        "effect_colors": EFFECT_COLORS,
        "created_at": matrix.created_at.isoformat() if matrix.created_at else None,
        "updated_at": matrix.updated_at.isoformat() if matrix.updated_at else None,
        "created_by": matrix.created_by
    }


@router.get("/sync/matrices/{game_id}/versions")
def get_matrix_versions(
    game_id: int,
    db: Session = Depends(get_db)
):
    """Get all versions of sync matrix for a game"""
    matrices = db.query(SyncMatrix).filter(
        SyncMatrix.game_id == game_id
    ).order_by(SyncMatrix.updated_at.desc()).all()

    return [
        {
            "id": m.id,
            "name": m.name,
            "status": m.status,
            "created_by": m.created_by,
            "created_at": m.created_at.isoformat() if m.created_at else None,
            "updated_at": m.updated_at.isoformat() if m.updated_at else None
        }
        for m in matrices
    ]


@router.delete("/sync/matrices/{game_id}/{matrix_id}")
def delete_sync_matrix(
    game_id: int,
    matrix_id: int,
    db: Session = Depends(get_db)
):
    """Delete a sync matrix"""
    matrix = db.query(SyncMatrix).filter(
        SyncMatrix.id == matrix_id,
        SyncMatrix.game_id == game_id
    ).first()

    if not matrix:
        raise HTTPException(status_code=404, detail="Sync matrix not found")

    db.delete(matrix)
    db.commit()

    return {"message": "Sync matrix deleted", "id": matrix_id}
