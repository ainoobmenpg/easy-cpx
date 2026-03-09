# Game API Routes
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Literal
from typing import Optional, List
from app.database import get_db
from app.models import Game, Unit, Turn, Order, OrderType, PlayerKnowledge, Event
from app.services.adjudication import RuleEngine
from app.services.ai_client import AIClient
from app.services.game_state_service import get_game_state_with_fow
from app.services.scenario_manager import ScenarioManager
from app.services.debriefing import DebriefingGenerator
from app.services.friction_events import FrictionEventService
import asyncio

router = APIRouter()


# Pydantic schemas for request bodies
class GameCreate(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {"name": "Operation Desert Storm"}
    })

    name: str = Field(..., min_length=1, max_length=100)


# Game endpoints
@router.get("/games/")
def list_games(db: Session = Depends(get_db)):
    """List all games"""
    games = db.query(Game).all()
    return [
        {
            "id": game.id,
            "name": game.name,
            "current_turn": game.current_turn,
            "current_date": game.current_date,
            "current_time": game.current_time,
            "weather": game.weather,
            "phase": game.phase,
            "is_active": game.is_active
        }
        for game in games
    ]


@router.post("/games/")
def create_game(request: GameCreate, db: Session = Depends(get_db)):
    """Create a new game"""
    game = Game(name=request.name)
    db.add(game)
    db.commit()
    db.refresh(game)
    return {
        "id": game.id,
        "name": game.name,
        "current_turn": game.current_turn,
        "current_time": game.current_time,
        "weather": game.weather,
        "phase": game.phase,
        "is_active": game.is_active
    }


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
        "current_date": game.current_date,
        "current_time": game.current_time,
        "weather": game.weather,
        "phase": game.phase,
        "is_active": game.is_active,
        "terrain_data": game.terrain_data,
        "map_width": game.map_width,
        "map_height": game.map_height,
    }


@router.get("/games/{game_id}/units")
def get_game_units(game_id: int, db: Session = Depends(get_db)):
    """Get player-visible units for a game (Fog of War applied)"""
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    # Get internal engine state
    engine = RuleEngine(db)
    engine_state = engine.get_game_state(game_id)

    # Apply Fog of War
    return get_game_state_with_fow(db, game_id, engine_state)


@router.post("/games/{game_id}/units/")
def create_unit(
    game_id: int = Path(..., gt=0),
    name: str = Query(..., min_length=1, max_length=100),
    unit_type: str = Query(..., min_length=1, max_length=50),
    side: str = Query(..., pattern="^(player|enemy)$"),
    x: float = Query(..., ge=0, le=100),
    y: float = Query(..., ge=0, le=100),
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
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "unit_id": 1,
            "order_type": "move",
            "target_units": None,
            "intent": "第1大隊を地点Aへ移動し、敵主力部隊を攻撃せよ",
            "location_x": 25.0,
            "location_y": 30.0,
            "location_name": "地点A",
            "priority": "high"
        }
    })

    unit_id: int = Field(..., gt=0)
    order_type: Literal["move", "attack", "defend", "support", "retreat", "recon", "supply", "special"]
    target_units: Optional[List[int]] = None
    intent: str = Field(..., min_length=1, max_length=1000)
    location_x: Optional[float] = Field(None, ge=0, le=100)
    location_y: Optional[float] = Field(None, ge=0, le=100)
    location_name: Optional[str] = Field(None, max_length=100)
    priority: Literal["high", "normal", "low"] = "normal"

    @field_validator("target_units")
    @classmethod
    def target_units_positive(cls, v):
        if v is not None:
            for item in v:
                if item <= 0:
                    raise ValueError("target unit ID must be positive")
        return v


class OrderParseRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "player_input": "第1戦車大隊は北方から敵装甲部隊の側面を突け。第2歩兵大隊は前線を維持し火力支援を行え。",
            "game_id": 1
        }
    })

    player_input: str = Field(..., min_length=1, max_length=2000)
    game_id: int = Field(..., gt=0)


class TurnAdvanceRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {"game_id": 1}
    })

    game_id: int = Field(..., gt=0)


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
        turn.enemy_results = enemy_results  # Save enemy AI decisions

        # Save enemy results to Event table for historical tracking
        for enemy_result in enemy_results:
            event = Event(
                turn_id=turn.id,
                event_type="enemy_action",
                data=enemy_result,
                description=enemy_result.get("unit_name", "Enemy unit") + " - " + enemy_result.get("outcome", "unknown")
            )
            db.add(event)

        db.commit()

    return {
        "turn": result.get("turn"),
        "results": result.get("results"),
        "events": result.get("events"),
        "enemy_results": enemy_results,
        "sitrep": sitrep,
        "next_time": result.get("next_time")
    }


@router.get("/games/{game_id}/state")
def get_game_state(game_id: int, db: Session = Depends(get_db)):
    """Get current game state with Fog of War applied"""
    # Validate game exists
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    # Get internal engine state (contains full truth)
    engine = RuleEngine(db)
    engine_state = engine.get_game_state(game_id)

    # Apply Fog of War and build response (separated concern)
    return get_game_state_with_fow(db, game_id, engine_state)


# Internal/Debug endpoints - exposes true state (FOR AUTHORIZED USE ONLY)
@router.get("/internal/games/{game_id}/true-state")
def get_true_state(game_id: int, db: Session = Depends(get_db)):
    """
    Get internal game state with full truth (Fog of War NOT applied).
    WARNING: This endpoint exposes all enemy positions, ammo, fuel, etc.
    Only use for debugging, admin panels, or internal services.
    """
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    # Get internal engine state (full truth)
    engine = RuleEngine(db)
    engine_state = engine.get_game_state(game_id)

    # Add game metadata
    engine_state["terrain_data"] = game.terrain_data
    engine_state["map_width"] = game.map_width
    engine_state["map_height"] = game.map_height

    return engine_state


@router.get("/internal/games/{game_id}/units")
def get_internal_units(game_id: int, db: Session = Depends(get_db)):
    """
    Get all units with full truth (Fog of War NOT applied).
    WARNING: This exposes all enemy positions and status.
    Only use for debugging or internal services.
    """
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    engine = RuleEngine(db)
    engine_state = engine.get_game_state(game_id)
    return engine_state.get("units", [])


@router.get("/games/{game_id}/sitrep")
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
    model_config = ConfigDict(json_schema_extra={
        "example": {"x": 25.0, "y": 30.0}
    })

    x: float = Field(..., ge=0, le=100)
    y: float = Field(..., ge=0, le=100)


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
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "scenario_id": "israel_2026",
            "game_name": "Operation Judea 2026"
        }
    })

    scenario_id: str = Field(..., min_length=1, max_length=100)
    game_name: str = Field(..., min_length=1, max_length=100)


@router.post("/games/start")
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
@router.get("/games/{game_id}/debriefing")
async def get_debriefing(game_id: int, db: Session = Depends(get_db)):
    """Get debriefing report for a game"""
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    generator = DebriefingGenerator()
    return await generator.generate_debriefing(game_id, db)


class EndGameRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {"game_id": 1}
    })

    game_id: int = Field(..., gt=0)


# Lightweight API endpoints
# Designed for simple frontend integration

class TurnCommitRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "game_id": 1,
            "orders": [
                {
                    "unit_id": 1,
                    "order_type": "move",
                    "target_units": None,
                    "intent": "第1大隊を北方へ移動せよ",
                    "location_x": 25.0,
                    "location_y": 30.0,
                    "location_name": "北方",
                    "priority": "high"
                }
            ]
        }
    })

    game_id: int = Field(..., gt=0)
    orders: List[OrderCreate]


@router.post("/turn/commit")
async def turn_commit(request: TurnCommitRequest, db: Session = Depends(get_db)):
    """
    Lightweight endpoint: Process orders -> adjudication -> update in one go.
    This combines order creation and turn advancement for simple frontend use.
    """
    game = db.query(Game).filter(Game.id == request.game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

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

    # Create orders from request
    order_results = []
    for order_req in request.orders:
        # Validate unit exists
        unit = db.query(Unit).filter(Unit.id == order_req.unit_id).first()
        if not unit:
            order_results.append({
                "unit_id": order_req.unit_id,
                "status": "error",
                "error": "Unit not found"
            })
            continue

        db_order = Order(
            game_id=game.id,
            unit_id=order_req.unit_id,
            turn_id=turn.id,
            order_type=OrderType[order_req.order_type.upper()],
            target_units=order_req.target_units,
            intent=order_req.intent,
            location_x=order_req.location_x,
            location_y=order_req.location_y,
            location_name=order_req.location_name,
            parameters={"priority": order_req.priority} if order_req.priority else None
        )
        db.add(db_order)
        db.commit()
        db.refresh(db_order)

        order_results.append({
            "id": db_order.id,
            "unit_id": order_req.unit_id,
            "order_type": order_req.order_type,
            "status": "submitted"
        })

    # Run adjudication
    engine = RuleEngine(db)
    ai = AIClient()
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
        Turn.turn_number == game.current_turn
    ).first()

    if turn:
        turn.sitrep = sitrep
        turn.excon_orders = excon_orders
        turn.enemy_results = enemy_results

        # Save enemy results to Event table
        for enemy_result in enemy_results:
            event = Event(
                turn_id=turn.id,
                event_type="enemy_action",
                data=enemy_result,
                description=enemy_result.get("unit_name", "Enemy unit") + " - " + enemy_result.get("outcome", "unknown")
            )
            db.add(event)

        db.commit()

    return {
        "turn": result.get("turn"),
        "orders_submitted": order_results,
        "results": result.get("results"),
        "events": result.get("events"),
        "enemy_results": enemy_results,
        "sitrep": sitrep,
        "next_time": result.get("next_time"),
        "next_turn": game.current_turn
    }


@router.get("/sitrep")
def get_sitrep_light(game_id: int, turn: int = None, db: Session = Depends(get_db)):
    """
    Lightweight endpoint: Get latest SITREP card.
    Returns the most recent available SITREP for the game.
    """
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    target_turn = turn if turn is not None else game.current_turn - 1
    turn_obj = db.query(Turn).filter(
        Turn.game_id == game_id,
        Turn.turn_number == target_turn
    ).first()

    if not turn_obj or not turn_obj.sitrep:
        return {
            "available": False,
            "message": "No SITREP available yet",
            "game_id": game_id,
            "current_turn": game.current_turn
        }

    return {
        "available": True,
        "game_id": game_id,
        "turn": target_turn,
        "sitrep": turn_obj.sitrep
    }


class EventDrawRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "game_id": 1,
            "seed": 42
        }
    })

    game_id: int = Field(..., gt=0)
    seed: Optional[int] = None


@router.post("/event/draw")
async def event_draw(request: EventDrawRequest, db: Session = Depends(get_db)):
    """
    Lightweight endpoint: Draw a random event card.
    Returns a random friction event for the current game state.
    """
    game = db.query(Game).filter(Game.id == request.game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    # Get engine state for context
    engine = RuleEngine(db)
    game_state = engine.get_game_state(request.game_id)

    # Generate event with optional seed
    friction_service = FrictionEventService(random_seed=request.seed)

    # Check if event should occur
    conditions = {
        "night": game.current_time.startswith(("19", "20", "21", "22", "23", "00", "01", "02", "03", "04", "05")),
        "bad_weather": game.weather in ["rain", "storm", "snow", "fog"],
        "high_intensity": game.current_turn > 3,
    }

    should_draw = friction_service.should_generate_event(game.current_turn, conditions)

    if not should_draw:
        return {
            "drawn": False,
            "event": None,
            "reason": "No event this turn",
            "game_id": request.game_id,
            "turn": game.current_turn
        }

    # Generate the event
    event = friction_service.generate_event(game_state)

    # Save event to database
    turn = db.query(Turn).filter(
        Turn.game_id == game.id,
        Turn.turn_number == game.current_turn
    ).first()

    if turn:
        db_event = Event(
            turn_id=turn.id,
            event_type="friction",
            data=event,
            description=event.get("title", "Friction Event")
        )
        db.add(db_event)
        db.commit()

    return {
        "drawn": True,
        "event": event,
        "game_id": request.game_id,
        "turn": game.current_turn
    }
