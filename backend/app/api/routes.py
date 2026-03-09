# Game API Routes
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from app.database import get_db
from app.models import Game, Unit, Turn, Order, OrderType
from app.services.adjudication import RuleEngine
from app.services.ai_client import AIClient
from app.services.scenario_manager import ScenarioManager
from app.services.debriefing import DebriefingGenerator
import asyncio

router = APIRouter()


# Game endpoints
@router.post("/games/")
def create_game(name: str, db: Session = Depends(get_db)):
    """Create a new game"""
    game = Game(name=name)
    db.add(game)
    db.commit()
    db.refresh(game)
    return game


@router.get("/games/{game_id}")
def get_game(game_id: int, db: Session = Depends(get_db)):
    """Get game by ID"""
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return {
        "id": game.id,
        "name": game.name,
        "current_turn": game.current_turn,
        "current_time": game.current_time,
        "weather": game.weather,
        "phase": game.phase,
        "is_active": game.is_active
    }


@router.get("/games/{game_id}/units")
def get_game_units(game_id: int, db: Session = Depends(get_db)):
    """Get all units for a game"""
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    units = db.query(Unit).filter(Unit.game_id == game_id).all()
    return [
        {
            "id": u.id,
            "name": u.name,
            "type": u.unit_type,
            "side": u.side,
            "x": u.x,
            "y": u.y,
            "status": u.status.value if u.status else None,
            "ammo": u.ammo.value if u.ammo else None,
            "fuel": u.fuel.value if u.fuel else None,
            "readiness": u.readiness.value if u.readiness else None,
            "strength": u.strength
        }
        for u in units
    ]


@router.post("/games/{game_id}/units/")
def create_unit(
    game_id: int,
    name: str,
    unit_type: str,
    side: str,
    x: float,
    y: float,
    db: Session = Depends(get_db)
):
    """Create a new unit"""
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    unit = Unit(
        game_id=game_id,
        name=name,
        unit_type=unit_type,
        side=side,
        x=x,
        y=y
    )
    db.add(unit)
    db.commit()
    db.refresh(unit)
    return unit


# Pydantic schemas
class OrderCreate(BaseModel):
    unit_id: int
    order_type: str
    target_units: Optional[List[int]] = None
    intent: str
    location_x: Optional[float] = None
    location_y: Optional[float] = None
    location_name: Optional[str] = None
    priority: Optional[str] = "normal"


class OrderParseRequest(BaseModel):
    player_input: str
    game_id: int


class TurnAdvanceRequest(BaseModel):
    game_id: int


@router.post("/parse-order")
async def parse_order(request: OrderParseRequest, db: Session = Depends(get_db)):
    """Parse player's natural language order using AI"""
    game = db.query(Game).filter(Game.id == request.game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    ai = AIClient()
    game_context = {
        "turn": game.current_turn,
        "time": game.current_time,
        "weather": game.weather
    }

    parsed = await ai.parse_order(request.player_input, game_context)
    return parsed


@router.post("/orders/")
def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    """Submit a player order"""
    unit = db.query(Unit).filter(Unit.id == order.unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")

    game = db.query(Game).filter(Game.id == unit.game_id).first()

    # Get or create current turn
    turn = db.query(Turn).filter(
        Turn.game_id == game.id,
        Turn.turn_number == game.current_turn
    ).first()

    if not turn:
        turn = Turn(
            game_id=game.id,
            turn_number=game.current_turn,
            time=game.current_time,
            weather=game.weather,
            phase="orders"
        )
        db.add(turn)
        db.commit()
        db.refresh(turn)

    db_order = Order(
        game_id=game.id,
        unit_id=order.unit_id,
        turn_id=turn.id,
        order_type=OrderType[order.order_type.upper()],
        target_units=order.target_units,
        intent=order.intent,
        location_x=order.location_x,
        location_y=order.location_y,
        location_name=order.location_name,
        parameters={"priority": order.priority} if order.priority else None
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)

    return {
        "id": db_order.id,
        "order_type": db_order.order_type.value,
        "intent": db_order.intent,
        "status": "submitted"
    }


@router.post("/advance-turn")
async def advance_turn(request: TurnAdvanceRequest, db: Session = Depends(get_db)):
    """Advance game turn - process orders and generate SITREP"""
    game = db.query(Game).filter(Game.id == request.game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    engine = RuleEngine(db)
    ai = AIClient()

    # Run adjudication
    result = engine.adjudicate_turn(request.game_id)

    # Add unit names to results
    for r in result.get("results", []):
        order = db.query(Order).filter(Order.id == r.get("order_id")).first()
        if order:
            unit = db.query(Unit).filter(Unit.id == order.unit_id).first()
            r["unit_name"] = unit.name if unit else "Unknown"

    # Get updated game state
    game_state = engine.get_game_state(request.game_id)

    # Generate SITREP
    sitrep = await ai.generate_sitrep(game_state, result.get("results", []))

    # Generate enemy orders
    excon_orders = await ai.generate_excon_orders(game_state)

    # Process enemy orders using the rule engine
    enemy_results = engine.process_enemy_orders(request.game_id, excon_orders)

    # Save to turn
    turn = db.query(Turn).filter(
        Turn.game_id == request.game_id,
        Turn.turn_number == game.current_turn - 1  # After advancement
    ).first()

    if turn:
        turn.sitrep = sitrep
        turn.excon_orders = excon_orders
        db.commit()

    return {
        "turn": result.get("turn"),
        "results": result.get("results"),
        "events": result.get("events"),
        "enemy_results": enemy_results,
        "sitrep": sitrep,
        "next_time": result.get("next_time")
    }


@router.get("/game/{game_id}/state")
def get_game_state(game_id: int, db: Session = Depends(get_db)):
    """Get current game state"""
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    engine = RuleEngine(db)
    return engine.get_game_state(game_id)


@router.get("/game/{game_id}/sitrep")
def get_sitrep(game_id: int, turn: int = None, db: Session = Depends(get_db)):
    """Get SITREP for specified turn or latest available"""
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    target_turn = turn if turn is not None else game.current_turn - 1
    turn = db.query(Turn).filter(
        Turn.game_id == game_id,
        Turn.turn_number == target_turn
    ).first()

    if not turn or not turn.sitrep:
        return {"message": "No SITREP available yet"}

    return turn.sitrep


class MoveUnitRequest(BaseModel):
    x: float
    y: float


@router.post("/units/{unit_id}/move")
def move_unit(unit_id: int, request: MoveUnitRequest, db: Session = Depends(get_db)):
    """Move unit to new position (drag and drop)"""
    unit = db.query(Unit).filter(Unit.id == unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")

    # Update position (in grid scale 0-50)
    unit.x = request.x
    unit.y = request.y
    db.commit()
    db.refresh(unit)

    return {"success": True, "unit_id": unit_id, "x": unit.x, "y": unit.y}


# Scenario endpoints
@router.get("/scenarios")
def get_scenarios():
    """Get list of all available scenarios"""
    manager = ScenarioManager()
    return manager.load_scenarios()


@router.get("/scenarios/{scenario_id}")
def get_scenario(scenario_id: str):
    """Get detailed scenario by ID"""
    manager = ScenarioManager()
    scenario = manager.get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scenario


class GameStartRequest(BaseModel):
    scenario_id: str
    game_name: str


@router.post("/game/start")
def start_game(request: GameStartRequest, db: Session = Depends(get_db)):
    """Start a new game from a scenario"""
    manager = ScenarioManager()
    try:
        result = manager.create_game_from_scenario(
            request.scenario_id,
            request.game_name,
            db
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Debriefing endpoints
@router.get("/game/{game_id}/debriefing")
async def get_debriefing(game_id: int, db: Session = Depends(get_db)):
    """Get debriefing report for a game"""
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    generator = DebriefingGenerator()
    return await generator.generate_debriefing(game_id, db)


class EndGameRequest(BaseModel):
    game_id: int


@router.post("/game/end")
def end_game(request: EndGameRequest, db: Session = Depends(get_db)):
    """End a game and mark it as inactive"""
    game = db.query(Game).filter(Game.id == request.game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    game.is_active = False
    db.commit()

    return {"success": True, "game_id": game.id, "message": "Game ended"}
