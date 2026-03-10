# OPORD/FRAGO API Routes for persistence
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from app.database import get_db
from app.services.opord_service import (
    OpordPersistenceService,
    get_opord_service,
    OPORDData
)
from app.services.auth_service import AuthService, extract_token
from datetime import datetime

router = APIRouter()


# Request/Response models
class OpordSaveRequest(BaseModel):
    game_id: int
    status: str = "draft"


class FragoSaveRequest(BaseModel):
    game_id: int
    opord_id: int
    frago_number: str
    changes: Dict[str, Any]
    summary: str
    issued_by: str


class OpordResponse(BaseModel):
    opord_id: str
    game_id: int
    title: str
    situation: Dict[str, Any]
    mission: Dict[str, Any]
    execution: Dict[str, Any]
    coordination: Dict[str, Any]
    service_support: Dict[str, Any]


@router.post("/opord/save")
def save_opord(
    request: OpordSaveRequest,
    db: Session = Depends(get_db)
):
    """Save current OPORD to database"""
    opord_service = get_opord_service()
    current_opord = opord_service.get_current_opord()

    if not current_opord:
        raise HTTPException(status_code=404, detail="No current OPORD exists")

    # Use persistence service
    persistence = OpordPersistenceService(db)
    record = persistence.save_opord(current_opord, request.status)

    return {
        "id": record.id,
        "version": record.version,
        "status": record.status,
        "saved_at": record.created_at.isoformat()
    }


@router.get("/opord/{game_id}")
def get_opord(
    game_id: int,
    db: Session = Depends(get_db)
):
    """Load OPORD from database"""
    persistence = OpordPersistenceService(db)
    opord = persistence.load_opord(game_id)

    if not opord:
        # Return in-memory if no DB record
        opord_service = get_opord_service()
        current = opord_service.get_current_opord()
        if current:
            return {"opord": opord_service.to_dict(current), "source": "memory"}
        raise HTTPException(status_code=404, detail="No OPORD found")

    return {"opord": opord_service.to_dict(opord), "source": "database"}


@router.get("/opord/{game_id}/versions")
def get_opord_versions(
    game_id: int,
    db: Session = Depends(get_db)
):
    """Get all OPORD versions"""
    persistence = OpordPersistenceService(db)
    versions = persistence.get_opord_versions(game_id)
    return {"versions": versions}


@router.post("/frago/save")
def save_frago(
    request: FragoSaveRequest,
    db: Session = Depends(get_db)
):
    """Save a FRAGO to database"""
    persistence = OpordPersistenceService(db)

    frago = persistence.save_frago(
        opord_id=request.opord_id,
        game_id=request.game_id,
        frago_number=request.frago_number,
        changes=request.changes,
        summary=request.summary,
        issued_by=request.issued_by
    )

    return {
        "id": frago.id,
        "frago_number": frago.frago_number,
        "version": frago.version,
        "status": frago.status,
        "saved_at": frago.created_at.isoformat()
    }


@router.get("/frago/{game_id}/chain")
def get_frago_chain(
    game_id: int,
    chain_name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get FRAGO chain for a game"""
    persistence = OpordPersistenceService(db)
    chain = persistence.get_frago_chain(game_id, chain_name)
    return {"chain": chain}
