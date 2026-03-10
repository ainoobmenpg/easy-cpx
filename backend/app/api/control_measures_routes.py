# Control Measures API Routes - CRUD for PL/Boundary/Airspace
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from app.database import get_db
from app.models import ControlMeasure

router = APIRouter()


# Request/Response models
class ControlMeasureCreate(BaseModel):
    game_id: int
    measure_type: str  # phase_line, boundary, airspace
    name: str
    description: Optional[str] = None
    points: List[List[float]]  # [[x1, y1], [x2, y2], ...]
    color: str = "#ff0000"
    line_style: str = "solid"
    owning_side: Optional[str] = None
    airspace_type: Optional[str] = None
    altitude_low: Optional[int] = None
    altitude_high: Optional[int] = None
    status: Optional[str] = "active"
    created_by: Optional[str] = None


class ControlMeasureUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    points: Optional[List[List[float]]] = None
    color: Optional[str] = None
    line_style: Optional[str] = None
    owning_side: Optional[str] = None
    airspace_type: Optional[str] = None
    altitude_low: Optional[int] = None
    altitude_high: Optional[int] = None
    status: Optional[str] = None


class ControlMeasureResponse(BaseModel):
    id: int
    game_id: int
    measure_type: str
    name: str
    description: Optional[str]
    points: List[List[float]]
    color: str
    line_style: str
    owning_side: Optional[str]
    airspace_type: Optional[str]
    altitude_low: Optional[int]
    altitude_high: Optional[int]
    status: str
    created_by: Optional[str]
    created_at: str


# CRUD endpoints
@router.post("/control-measures", response_model=ControlMeasureResponse)
def create_control_measure(
    measure: ControlMeasureCreate,
    db: Session = Depends(get_db)
):
    """Create a new control measure"""
    db_measure = ControlMeasure(
        game_id=measure.game_id,
        measure_type=measure.measure_type,
        name=measure.name,
        description=measure.description,
        points=measure.points,
        color=measure.color,
        line_style=measure.line_style,
        owning_side=measure.owning_side,
        airspace_type=measure.airspace_type,
        altitude_low=measure.altitude_low,
        altitude_high=measure.altitude_high,
        status=measure.status,
        created_by=measure.created_by
    )
    db.add(db_measure)
    db.commit()
    db.refresh(db_measure)

    return ControlMeasureResponse(
        id=db_measure.id,
        game_id=db_measure.game_id,
        measure_type=db_measure.measure_type,
        name=db_measure.name,
        description=db_measure.description,
        points=db_measure.points,
        color=db_measure.color,
        line_style=db_measure.line_style,
        owning_side=db_measure.owning_side,
        airspace_type=db_measure.airspace_type,
        altitude_low=db_measure.altitude_low,
        altitude_high=db_measure.altitude_high,
        status=db_measure.status,
        created_by=db_measure.created_by,
        created_at=db_measure.created_at.isoformat()
    )


@router.get("/control-measures/{game_id}", response_model=List[ControlMeasureResponse])
def get_control_measures(
    game_id: int,
    measure_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all control measures for a game"""
    query = db.query(ControlMeasure).filter(ControlMeasure.game_id == game_id)

    if measure_type:
        query = query.filter(ControlMeasure.measure_type == measure_type)

    measures = query.all()

    return [
        ControlMeasureResponse(
            id=m.id,
            game_id=m.game_id,
            measure_type=m.measure_type,
            name=m.name,
            description=m.description,
            points=m.points,
            color=m.color,
            line_style=m.line_style,
            owning_side=m.owning_side,
            airspace_type=m.airspace_type,
            altitude_low=m.altitude_low,
            altitude_high=m.altitude_high,
            status=m.status,
            created_by=m.created_by,
            created_at=m.created_at.isoformat()
        )
        for m in measures
    ]


@router.get("/control-measures/{game_id}/{measure_id}", response_model=ControlMeasureResponse)
def get_control_measure(
    game_id: int,
    measure_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific control measure"""
    measure = db.query(ControlMeasure).filter(
        ControlMeasure.id == measure_id,
        ControlMeasure.game_id == game_id
    ).first()

    if not measure:
        raise HTTPException(status_code=404, detail="Control measure not found")

    return ControlMeasureResponse(
        id=measure.id,
        game_id=measure.game_id,
        measure_type=measure.measure_type,
        name=measure.name,
        description=measure.description,
        points=measure.points,
        color=measure.color,
        line_style=measure.line_style,
        owning_side=measure.owning_side,
        airspace_type=measure.airspace_type,
        altitude_low=measure.altitude_low,
        altitude_high=measure.altitude_high,
        status=measure.status,
        created_by=measure.created_by,
        created_at=measure.created_at.isoformat()
    )


@router.put("/control-measures/{game_id}/{measure_id}", response_model=ControlMeasureResponse)
def update_control_measure(
    game_id: int,
    measure_id: int,
    update: ControlMeasureUpdate,
    db: Session = Depends(get_db)
):
    """Update a control measure"""
    measure = db.query(ControlMeasure).filter(
        ControlMeasure.id == measure_id,
        ControlMeasure.game_id == game_id
    ).first()

    if not measure:
        raise HTTPException(status_code=404, detail="Control measure not found")

    # Apply updates
    if update.name is not None:
        measure.name = update.name
    if update.description is not None:
        measure.description = update.description
    if update.points is not None:
        measure.points = update.points
    if update.color is not None:
        measure.color = update.color
    if update.line_style is not None:
        measure.line_style = update.line_style
    if update.owning_side is not None:
        measure.owning_side = update.owning_side
    if update.airspace_type is not None:
        measure.airspace_type = update.airspace_type
    if update.altitude_low is not None:
        measure.altitude_low = update.altitude_low
    if update.altitude_high is not None:
        measure.altitude_high = update.altitude_high
    if update.status is not None:
        measure.status = update.status

    db.commit()
    db.refresh(measure)

    return ControlMeasureResponse(
        id=measure.id,
        game_id=measure.game_id,
        measure_type=measure.measure_type,
        name=measure.name,
        description=measure.description,
        points=measure.points,
        color=measure.color,
        line_style=measure.line_style,
        owning_side=measure.owning_side,
        airspace_type=measure.airspace_type,
        altitude_low=measure.altitude_low,
        altitude_high=measure.altitude_high,
        status=measure.status,
        created_by=measure.created_by,
        created_at=measure.created_at.isoformat()
    )


@router.delete("/control-measures/{game_id}/{measure_id}")
def delete_control_measure(
    game_id: int,
    measure_id: int,
    db: Session = Depends(get_db)
):
    """Delete a control measure"""
    measure = db.query(ControlMeasure).filter(
        ControlMeasure.id == measure_id,
        ControlMeasure.game_id == game_id
    ).first()

    if not measure:
        raise HTTPException(status_code=404, detail="Control measure not found")

    db.delete(measure)
    db.commit()

    return {"message": "Control measure deleted", "id": measure_id}
