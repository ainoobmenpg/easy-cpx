# ATO/ACO API Routes - Air Tasking Order and Air Control Order
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from app.database import get_db
from app.models import AirMission, AirCorridor
from datetime import datetime

router = APIRouter()


# Request/Response models
class AirMissionCreate(BaseModel):
    game_id: int
    mission_number: str
    mission_type: str  # cas, bai, sead, isr, airlift
    scheduled_turn: int
    tot: Optional[str] = None
    aircraft_type: Optional[str] = None
    aircraft_count: int = 1
    target_x: Optional[float] = None
    target_y: Optional[float] = None
    target_description: Optional[str] = None
    created_by: Optional[str] = None


class AirMissionUpdate(BaseModel):
    status: Optional[str] = None
    tot: Optional[str] = None
    target_x: Optional[float] = None
    target_y: Optional[float] = None
    target_description: Optional[str] = None
    results: Optional[dict] = None


class AirMissionResponse(BaseModel):
    id: int
    game_id: int
    mission_number: str
    mission_type: str
    scheduled_turn: int
    tot: Optional[str]
    aircraft_type: Optional[str]
    aircraft_count: int
    target_x: Optional[float]
    target_y: Optional[float]
    target_description: Optional[str]
    status: str
    results: Optional[dict]
    created_by: Optional[str]
    created_at: str


class AirCorridorCreate(BaseModel):
    game_id: int
    name: str
    corridor_type: str = "transit"
    waypoints: List[List[float]]  # [[x1, y1], [x2, y2], ...]
    altitude_min: Optional[int] = None
    altitude_max: Optional[int] = None
    status: str = "active"


class AirCorridorUpdate(BaseModel):
    name: Optional[str] = None
    waypoints: Optional[List[List[float]]] = None
    altitude_min: Optional[int] = None
    altitude_max: Optional[int] = None
    status: Optional[str] = None


class AirCorridorResponse(BaseModel):
    id: int
    game_id: int
    name: str
    corridor_type: str
    waypoints: List[List[float]]
    altitude_min: Optional[int]
    altitude_max: Optional[int]
    status: str
    created_at: str


# Air Mission endpoints
@router.post("/ato/missions", response_model=AirMissionResponse)
def create_air_mission(
    mission: AirMissionCreate,
    db: Session = Depends(get_db)
):
    """Create a new air mission (ATO entry)"""
    db_mission = AirMission(
        game_id=mission.game_id,
        mission_number=mission.mission_number,
        mission_type=mission.mission_type,
        scheduled_turn=mission.scheduled_turn,
        tot=mission.tot,
        aircraft_type=mission.aircraft_type,
        aircraft_count=mission.aircraft_count,
        target_x=mission.target_x,
        target_y=mission.target_y,
        target_description=mission.target_description,
        created_by=mission.created_by
    )
    db.add(db_mission)
    db.commit()
    db.refresh(db_mission)

    return AirMissionResponse(
        id=db_mission.id,
        game_id=db_mission.game_id,
        mission_number=db_mission.mission_number,
        mission_type=db_mission.mission_type,
        scheduled_turn=db_mission.scheduled_turn,
        tot=db_mission.tot,
        aircraft_type=db_mission.aircraft_type,
        aircraft_count=db_mission.aircraft_count,
        target_x=db_mission.target_x,
        target_y=db_mission.target_y,
        target_description=db_mission.target_description,
        status=db_mission.status,
        results=db_mission.results,
        created_by=db_mission.created_by,
        created_at=db_mission.created_at.isoformat()
    )


@router.get("/ato/missions/{game_id}", response_model=List[AirMissionResponse])
def get_air_missions(
    game_id: int,
    turn: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all air missions for a game"""
    query = db.query(AirMission).filter(AirMission.game_id == game_id)

    if turn:
        query = query.filter(AirMission.scheduled_turn == turn)
    if status:
        query = query.filter(AirMission.status == status)

    missions = query.order_by(AirMission.scheduled_turn).all()

    return [
        AirMissionResponse(
            id=m.id,
            game_id=m.game_id,
            mission_number=m.mission_number,
            mission_type=m.mission_type,
            scheduled_turn=m.scheduled_turn,
            tot=m.tot,
            aircraft_type=m.aircraft_type,
            aircraft_count=m.aircraft_count,
            target_x=m.target_x,
            target_y=m.target_y,
            target_description=m.target_description,
            status=m.status,
            results=m.results,
            created_by=m.created_by,
            created_at=m.created_at.isoformat()
        )
        for m in missions
    ]


@router.put("/ato/missions/{game_id}/{mission_id}", response_model=AirMissionResponse)
def update_air_mission(
    game_id: int,
    mission_id: int,
    update: AirMissionUpdate,
    db: Session = Depends(get_db)
):
    """Update an air mission"""
    mission = db.query(AirMission).filter(
        AirMission.id == mission_id,
        AirMission.game_id == game_id
    ).first()

    if not mission:
        raise HTTPException(status_code=404, detail="Air mission not found")

    if update.status is not None:
        mission.status = update.status
    if update.tot is not None:
        mission.tot = update.tot
    if update.target_x is not None:
        mission.target_x = update.target_x
    if update.target_y is not None:
        mission.target_y = update.target_y
    if update.target_description is not None:
        mission.target_description = update.target_description
    if update.results is not None:
        mission.results = update.results

    db.commit()
    db.refresh(mission)

    return AirMissionResponse(
        id=mission.id,
        game_id=mission.game_id,
        mission_number=mission.mission_number,
        mission_type=mission.mission_type,
        scheduled_turn=mission.scheduled_turn,
        tot=mission.tot,
        aircraft_type=mission.aircraft_type,
        aircraft_count=mission.aircraft_count,
        target_x=mission.target_x,
        target_y=mission.target_y,
        target_description=mission.target_description,
        status=mission.status,
        results=mission.results,
        created_by=mission.created_by,
        created_at=mission.created_at.isoformat()
    )


# Air Corridor endpoints (ACO)
@router.post("/aco/corridors", response_model=AirCorridorResponse)
def create_air_corridor(
    corridor: AirCorridorCreate,
    db: Session = Depends(get_db)
):
    """Create a new air corridor (ACO entry)"""
    db_corridor = AirCorridor(
        game_id=corridor.game_id,
        name=corridor.name,
        corridor_type=corridor.corridor_type,
        waypoints=corridor.waypoints,
        altitude_min=corridor.altitude_min,
        altitude_max=corridor.altitude_max,
        status=corridor.status
    )
    db.add(db_corridor)
    db.commit()
    db.refresh(db_corridor)

    return AirCorridorResponse(
        id=db_corridor.id,
        game_id=db_corridor.game_id,
        name=db_corridor.name,
        corridor_type=db_corridor.corridor_type,
        waypoints=db_corridor.waypoints,
        altitude_min=db_corridor.altitude_min,
        altitude_max=db_corridor.altitude_max,
        status=db_corridor.status,
        created_at=db_corridor.created_at.isoformat()
    )


@router.get("/aco/corridors/{game_id}", response_model=List[AirCorridorResponse])
def get_air_corridors(
    game_id: int,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all air corridors for a game"""
    query = db.query(AirCorridor).filter(AirCorridor.game_id == game_id)

    if status:
        query = query.filter(AirCorridor.status == status)

    corridors = query.all()

    return [
        AirCorridorResponse(
            id=c.id,
            game_id=c.game_id,
            name=c.name,
            corridor_type=c.corridor_type,
            waypoints=c.waypoints,
            altitude_min=c.altitude_min,
            altitude_max=c.altitude_max,
            status=c.status,
            created_at=c.created_at.isoformat()
        )
        for c in corridors
    ]


@router.delete("/aco/corridors/{game_id}/{corridor_id}")
def delete_air_corridor(
    game_id: int,
    corridor_id: int,
    db: Session = Depends(get_db)
):
    """Delete an air corridor"""
    corridor = db.query(AirCorridor).filter(
        AirCorridor.id == corridor_id,
        AirCorridor.game_id == game_id
    ).first()

    if not corridor:
        raise HTTPException(status_code=404, detail="Air corridor not found")

    db.delete(corridor)
    db.commit()

    return {"message": "Air corridor deleted", "id": corridor_id}
