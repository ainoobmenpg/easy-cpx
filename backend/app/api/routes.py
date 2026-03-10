# Game API Routes
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Literal
from typing import Optional, List, Dict
from app.database import get_db
from app.models import Game, Unit, Turn, Order, OrderType, PlayerKnowledge, Event, GameMode, is_arcade_game
from app.services.adjudication import RuleEngine
from app.services.arcade_adjudication import ArcadeAdjudication
from app.services.ai_client import AIClient
from app.services.game_state_service import get_game_state_with_fow
from app.services.scenario_manager import ScenarioManager
from app.services.debriefing import DebriefingGenerator
from app.services.friction_events import FrictionEventService
from app.services.opord_service import OpordService, get_opord_service
from app.services.logistics_service import LogisticsService, create_logistics_service
from app.services.rate_limiter import get_rate_limiter
from app.services.audit_logger import get_audit_logger, AuditEventType, AuditSeverity
from app.services.cycle_manager import (
    initialize_game_cycles,
    advance_cycle,
    get_cycle_penalty,
    apply_cycle_penalties,
    get_cycle_summary,
)
from app.services.replay_service import ReplayService, create_replay_service
import asyncio
import os

router = APIRouter()

# Security: Flag for internal endpoint access
ENABLE_INTERNAL_ENDPOINTS = os.getenv("ENABLE_INTERNAL_ENDPOINTS", "false").lower() == "true"

# Rate limiter instance
_rate_limiter = get_rate_limiter()
_audit_logger = get_audit_logger()


def get_client_id(request: Request) -> str:
    """Extract client identifier from request (IP or user ID)"""
    # Try to get user ID first if authenticated
    if hasattr(request.state, 'user_id'):
        return f"user:{request.state.user_id}"

    # Fall back to IP address
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return f"ip:{forwarded.split(',')[0].strip()}"
    return f"ip:{request.client.host if request.client else 'unknown'}"


def check_internal_access():
    """Check if internal endpoints are enabled"""
    if not ENABLE_INTERNAL_ENDPOINTS:
        raise HTTPException(status_code=401, detail="Internal endpoints are disabled")


async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware"""
    client_id = get_client_id(request)
    endpoint = request.url.path

    is_allowed, rate_info = _rate_limiter.check_rate_limit(client_id, endpoint)

    if not is_allowed:
        # Log rate limit exceeded
        _audit_logger.log_event(
            event_type=AuditEventType.RATE_LIMIT_EXCEEDED,
            action="rate_limit_exceeded",
            result="blocked",
            severity=AuditSeverity.WARNING,
            ip_address=request.client.host if request.client else None,
            endpoint=endpoint,
            method=request.method,
            details={"client_id": client_id, "retry_after": rate_info["retry_after"]}
        )

        return JSONResponse(
            status_code=429,
            content={
                "detail": "Rate limit exceeded",
                "retry_after": rate_info["retry_after"]
            },
            headers={
                "X-RateLimit-Limit": str(rate_info["limit"]),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(rate_info["reset"]),
                "Retry-After": str(rate_info["retry_after"])
            }
        )

    response = await call_next(request)

    # Add rate limit headers to response
    response.headers["X-RateLimit-Limit"] = str(rate_info["limit"])
    response.headers["X-RateLimit-Remaining"] = str(rate_info["remaining"])
    response.headers["X-RateLimit-Reset"] = str(rate_info["reset"])

    return response


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
    # Initialize cycles for CPX-CYCLES
    initial_cycles = initialize_game_cycles(1)
    game.planning_cycle = initial_cycles["planning"]
    game.air_tasking_cycle = initial_cycles["air_tasking"]
    game.logistics_cycle = initial_cycles["logistics"]
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
        "is_active": game.is_active,
        "planning_cycle": game.planning_cycle,
        "air_tasking_cycle": game.air_tasking_cycle,
        "logistics_cycle": game.logistics_cycle,
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
        "planning_cycle": game.planning_cycle,
        "air_tasking_cycle": game.air_tasking_cycle,
        "logistics_cycle": game.logistics_cycle,
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
    order_type: Literal["move", "attack", "defend", "support", "retreat", "recon", "supply", "special", "wait"]
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

    # Security: Only allow orders for player units
    if unit.side != "player":
        raise HTTPException(status_code=403, detail="Cannot submit orders for enemy units")

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

    # Branch based on game_mode
    if is_arcade_game(game.game_mode):
        # Arcade mode: Use ArcadeAdjudication
        arcade_engine = ArcadeAdjudication(db)
        return arcade_engine.get_game_state(game_id)

    # Classic/Simulation mode: Use RuleEngine with Fog of War
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
    check_internal_access()  # Security: require ENABLE_INTERNAL_ENDPOINTS=true

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
    check_internal_access()  # Security: require ENABLE_INTERNAL_ENDPOINTS=true

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


@router.get("/units/{unit_id}/reachable")
def get_unit_reachable(unit_id: int, db: Session = Depends(get_db)):
    """Get reachable positions for a unit (for movement preview in Arcade mode).

    Returns all grid positions with info on whether the unit can reach them
    based on movement points and terrain costs.
    """
    # Check if unit is ArcadeUnit
    from app.models import ArcadeUnit
    arcade_unit = db.query(ArcadeUnit).filter(ArcadeUnit.id == unit_id).first()

    if arcade_unit:
        # Use ArcadeAdjudication for Arcade mode
        engine = ArcadeAdjudication(db)
        return engine.get_reachable_positions(unit_id)

    # Fallback to regular Unit (Classic mode)
    unit = db.query(Unit).filter(Unit.id == unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")

    # Get game for terrain data
    game = db.query(Game).filter(Game.id == unit.game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    # For Classic mode, use RuleEngine
    from app.services.adjudication import RuleEngine
    engine = RuleEngine(db)
    return engine.get_reachable_positions_classic(unit_id)


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

    Branches based on game_mode:
    - Classic (Simulation): Uses RuleEngine with full unit model
    - Arcade: Uses ArcadeAdjudication with simplified 2D6 rules
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

    # Branch based on game_mode
    if is_arcade_game(game.game_mode):
        # Arcade mode: Use ArcadeAdjudication
        return await _arcade_turn_commit(request, db, game, turn)
    else:
        # Classic/Simulation mode: Use RuleEngine
        return await _classic_turn_commit(request, db, game, turn)


async def _classic_turn_commit(request, db, game, turn):
    """Handle Classic/Simulation mode turn commit"""
    from sqlalchemy.orm import joinedload
    from app.models import Unit

    # Pre-load all units for validation in one query
    unit_ids = [o.unit_id for o in request.orders]
    units_map = {u.id: u for u in db.query(Unit).filter(Unit.id.in_(unit_ids)).all()} if unit_ids else {}

    # Create orders from request
    order_results = []
    orders_to_add = []
    for order_req in request.orders:
        # Validate unit exists using pre-loaded map
        unit = units_map.get(order_req.unit_id)
        if not unit:
            order_results.append({
                "unit_id": order_req.unit_id,
                "status": "error",
                "error": "Unit not found"
            })
            continue

        # Security: Only allow orders for player units
        if unit.side != "player":
            order_results.append({
                "unit_id": order_req.unit_id,
                "status": "error",
                "error": "Cannot submit orders for enemy units"
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
        orders_to_add.append((order_req, db_order))

    # Batch insert all orders in one transaction
    if orders_to_add:
        db.add_all([o[1] for o in orders_to_add])
        db.commit()

        # Refresh all orders to get their IDs
        for order_req, db_order in orders_to_add:
            db.refresh(db_order)
            order_results.append({
                "id": db_order.id,
                "unit_id": order_req.unit_id,
                "order_type": order_req.order_type,
                "status": "submitted"
            })

    # Run adjudication with RuleEngine
    engine = RuleEngine(db)
    ai = AIClient()
    result = engine.adjudicate_turn(request.game_id)

    # Add unit names to results (optimized with joinedload)
    order_ids = [r.get("order_id") for r in result.get("results", []) if r.get("order_id")]
    if order_ids:
        orders_with_units = db.query(Order).options(joinedload(Order.unit)).filter(Order.id.in_(order_ids)).all()
        order_unit_map = {o.id: o.unit for o in orders_with_units if o.unit}

        for r in result.get("results", []):
            unit = order_unit_map.get(r.get("order_id"))
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


async def _arcade_turn_commit(request, db, game, turn):
    """Handle Arcade mode turn commit"""
    from app.models import ArcadeUnit

    # Pre-load all arcade units for validation in one query
    unit_ids = [o.unit_id for o in request.orders]
    units_map = {u.id: u for u in db.query(ArcadeUnit).filter(ArcadeUnit.id.in_(unit_ids)).all()} if unit_ids else {}

    # Create orders from request (for ArcadeUnit)
    order_results = []
    orders_to_add = []
    for order_req in request.orders:
        # Validate arcade unit exists using pre-loaded map
        unit = units_map.get(order_req.unit_id)
        if not unit:
            order_results.append({
                "unit_id": order_req.unit_id,
                "status": "error",
                "error": "ArcadeUnit not found"
            })
            continue

        # Security: Only allow orders for player units
        if unit.side != "player":
            order_results.append({
                "unit_id": order_req.unit_id,
                "status": "error",
                "error": "Cannot submit orders for enemy units"
            })
            continue

        # Store order in DB for history
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
        orders_to_add.append((order_req, db_order))

    # Batch insert all orders in one transaction
    if orders_to_add:
        db.add_all([o[1] for o in orders_to_add])
        db.commit()

        # Refresh all orders to get their IDs
        for order_req, db_order in orders_to_add:
            db.refresh(db_order)
            order_results.append({
                "id": db_order.id,
                "unit_id": order_req.unit_id,
                "order_type": order_req.order_type,
                "status": "submitted"
        })

    # Run adjudication with ArcadeAdjudication
    arcade_engine = ArcadeAdjudication(db)

    # Convert orders to Arcade format
    arcade_orders = []
    for order_req in request.orders:
        order_dict = {
            "unit_id": order_req.unit_id,
            "order_type": order_req.order_type,
        }
        if order_req.location_x is not None:
            order_dict["location_x"] = int(order_req.location_x)
        if order_req.location_y is not None:
            order_dict["location_y"] = int(order_req.location_y)
        if order_req.target_units and len(order_req.target_units) > 0:
            order_dict["target_id"] = order_req.target_units[0]
        arcade_orders.append(order_dict)

    result = arcade_engine.adjudicate_turn(request.game_id, arcade_orders)

    # Get updated game state
    game_state = arcade_engine.get_game_state(request.game_id)

    # CPX-LOG: Advance logistics turn and get events
    logistics = create_logistics_service(request.game_id)
    logistics_events = logistics.advance_turn(game.current_turn)

    # Get logistics summary for SITREP
    logistics_summary = logistics.get_logistics_summary(game.current_turn)

    # For Arcade mode, generate a simple SITREP
    sitrep = _generate_arcade_sitrep(result, game_state, logistics_summary)

    # Save to turn
    turn = db.query(Turn).filter(
        Turn.game_id == request.game_id,
        Turn.turn_number == game.current_turn
    ).first()

    if turn:
        turn.sitrep = sitrep
        turn.excon_orders = None
        turn.enemy_results = result.get("enemy_actions", [])
        db.commit()

    # Advance turn
    game.current_turn += 1

    # CPX-CYCLES: Update all cycles after turn advancement
    if game.planning_cycle:
        game.planning_cycle = advance_cycle(game.planning_cycle, game.current_turn)
    if game.air_tasking_cycle:
        game.air_tasking_cycle = advance_cycle(game.air_tasking_cycle, game.current_turn)
    if game.logistics_cycle:
        game.logistics_cycle = advance_cycle(game.logistics_cycle, game.current_turn)

    db.commit()

    return {
        "turn": result.get("turn", game.current_turn - 1),
        "orders_submitted": order_results,
        "results": result,
        "events": result.get("events", []),
        "enemy_results": result.get("enemy_actions", []),
        "sitrep": sitrep,
        "next_time": None,
        "next_turn": game.current_turn,
        "victory": result.get("victory"),
        "cycles": get_cycle_summary({
            "planning": game.planning_cycle,
            "air_tasking": game.air_tasking_cycle,
            "logistics": game.logistics_cycle,
        }),
    }


def _generate_arcade_sitrep(arcade_result: dict, game_state: dict, logistics_summary: dict = None) -> str:
    """Generate a simple SITREP for Arcade mode"""
    lines = []
    lines.append(f"=== Turn {arcade_result.get('turn', '?')} SITREP ===")

    # Victory/Defeat
    if arcade_result.get("victory") == "PLAYER_WINS":
        lines.append("VICTORY! All enemy units have been destroyed.")
    elif arcade_result.get("victory") == "ENEMY_WINS":
        lines.append("DEFEAT! All your units have been destroyed.")

    # Moves
    if arcade_result.get("moves"):
        lines.append("\nMovements:")
        for move in arcade_result["moves"]:
            lines.append(f"  - {move.get('unit', 'Unknown')}: {move.get('result', '?')}")

    # Attacks
    if arcade_result.get("attacks"):
        lines.append("\nCombat:")
        for attack in arcade_result["attacks"]:
            lines.append(
                f"  - {attack.get('attacker', '?')} vs {attack.get('defender', '?')}: "
                f"{attack.get('result', '?')} (dmg: {attack.get('damage_to_defender', 0)})"
            )

    # STRIKE results
    if arcade_result.get("strikes"):
        lines.append("\nSTRIKE Actions:")
        for strike in arcade_result["strikes"]:
            result = strike.get("result", "?")
            if result == "SUCCESS":
                lines.append(
                    f"  - {strike.get('unit', '?')}: STRIKE activated! "
                    f"+{strike.get('attack_modifier', 2)} attack modifier. "
                    f"Tokens remaining: {strike.get('strikes_remaining', '?')}"
                )
            else:
                lines.append(
                    f"  - {strike.get('unit', '?')}: STRIKE failed - {strike.get('reason', 'unknown')}"
                )

    # WAIT results (informational only)
    if arcade_result.get("waits"):
        lines.append("\nWait:")
        for wait in arcade_result["waits"]:
            lines.append(f"  - {wait.get('unit', '?')}: Waiting")

    # Destructions
    if arcade_result.get("destructions"):
        lines.append("\nDestroyed:")
        for name in arcade_result["destructions"]:
            lines.append(f"  - {name}")

    # CPX-LOG: Logistics section
    if logistics_summary:
        lines.append("\n[LOGSITREP]")
        status = logistics_summary.get("overall_status", "unknown")
        lines.append(f"  Supply Status: {status.upper()}")

        # Routes
        routes = logistics_summary.get("routes", [])
        if routes:
            lines.append("  Supply Routes:")
            for route in routes[:3]:  # Show first 3
                status_icon = "OK" if route.get("status") == "open" else "X"
                lines.append(f"    [{status_icon}] {route.get('name', 'Route')}: {route.get('distance', 0)}km")

        # Convoys
        convoys = logistics_summary.get("active_convoys", [])
        if convoys:
            lines.append(f"  Active Convoys: {len(convoys)}")

    # Unit status
    units = game_state.get("units", [])
    player_units = [u for u in units if u.get("side") == "player"]
    enemy_units = [u for u in units if u.get("side") == "enemy"]

    lines.append(f"\nRemaining forces: Player {len(player_units)} | Enemy {len(enemy_units)}")

    return "\n".join(lines)


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


# ==========================================
# OPORD/FRAGO API Endpoints (SMESC Format)
# ==========================================

class OpordCreateRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "game_id": 1,
            "title": "Operation Northern Guardian"
        }
    })

    game_id: int = Field(..., gt=0)
    title: str = Field(default="作戦計画")


class OpordUpdateRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "title": "Updated Operation Plan",
            "situation": {
                "enemy_situation": "Enemy forces have regrouped in the northern sector"
            }
        }
    })

    title: Optional[str] = None
    classification: Optional[Literal["unclassified", "confidential", "secret", "top_secret"]] = None
    effective_date: Optional[str] = None
    situation: Optional[dict] = None
    mission: Optional[dict] = None
    execution: Optional[dict] = None
    coordination: Optional[dict] = None
    service_support: Optional[dict] = None


@router.get("/games/{game_id}/opord")
def get_opord(game_id: int):
    """
    Get the current OPORD for a game.
    Returns the SMESC format OPORD/FRAGO.
    """
    opord_service = get_opord_service()
    opord = opord_service.get_current_opord()

    if opord is None:
        # Create default OPORD if none exists
        opord_service.create_default_opord(game_id)

    return {
        "success": True,
        "opord": opord_service.to_dict()
    }


@router.post("/games/{game_id}/opord")
def create_opord(game_id: int, request: OpordCreateRequest):
    """
    Create a new OPORD for a game.
    """
    opord_service = get_opord_service()
    opord = opord_service.create_default_opord(game_id, request.title)

    return {
        "success": True,
        "opord": opord_service.to_dict()
    }


@router.put("/games/{game_id}/opord")
def update_opord(game_id: int, request: OpordUpdateRequest):
    """
    Update an existing OPORD.
    """
    opord_service = get_opord_service()
    current_opord = opord_service.get_current_opord()

    if current_opord is None:
        opord_service.create_default_opord(game_id)

    # Update title
    if request.title is not None:
        opord_service._current_opord.title = request.title

    # Update classification
    if request.classification is not None:
        opord_service._current_opord.classification = request.classification

    # Update effective date
    if request.effective_date is not None:
        opord_service._current_opord.effective_date = request.effective_date

    # Update situation section
    if request.situation is not None:
        opord_service.update_situation(**request.situation)

    # Update mission section
    if request.mission is not None:
        opord_service.update_mission(**request.mission)

    # Update execution section
    if request.execution is not None:
        opord_service.update_execution(**request.execution)

    # Update coordination section
    if request.coordination is not None:
        opord_service.update_coordination(**request.coordination)

    # Update service support section
    if request.service_support is not None:
        opord_service.update_service_support(**request.service_support)

    return {
        "success": True,
        "opord": opord_service.to_dict()
    }


@router.get("/games/{game_id}/opord/display")
def get_opord_display(game_id: int):
    """
    Get OPORD formatted for display in UI.
    """
    opord_service = get_opord_service()
    opord = opord_service.get_current_opord()

    if opord is None:
        opord_service.create_default_opord(game_id)

    return {
        "success": True,
        "formatted": opord_service.format_for_display()
    }


# ==========================================
# CPX-4: MEL/MIL (Inject) System API Endpoints
# ==========================================

# In-memory inject system storage (per game)
# In production, this would be stored in the database
_inject_systems: dict[int, Any] = {}


class InjectTriggerRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "inject_id": "inj_comms_01",
            "turn": 3,
            "trigger_type": "immediate"
        }
    })

    inject_id: str
    turn: int
    trigger_type: str = "immediate"


class InjectCancelRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "inject_id": "inj_comms_01"
        }
    })

    inject_id: str


@router.get("/injects/{game_id}")
def get_injects(game_id: int, db: Session = Depends(get_db)):
    """
    Get all injects for a game.
    Returns available injects, active effects, and history.
    """
    from app.services.inject_system import create_inject_system

    # Get or create inject system for this game
    if game_id not in _inject_systems:
        _inject_systems[game_id] = create_inject_system(game_id)

    inject_system = _inject_systems[game_id]

    return {
        "game_id": game_id,
        "injects": inject_system.get_available_injects(),
        "triggered_injects": [
            inj for inj in inject_system._available_injects.values()
            if inj.get("status") == "triggered"
        ],
        "active_effects": inject_system.get_active_effects(),
        "history": inject_system.get_inject_history(),
        "summary": inject_system.get_inject_summary()
    }


@router.post("/injects/{game_id}/trigger")
def trigger_inject(
    game_id: int,
    request: InjectTriggerRequest,
    db: Session = Depends(get_db)
):
    """
    Trigger an inject immediately.
    Returns the inject log entry.
    """
    from app.services.inject_system import create_inject_system

    # Get or create inject system for this game
    if game_id not in _inject_systems:
        _inject_systems[game_id] = create_inject_system(game_id)

    inject_system = _inject_systems[game_id]

    # Get game state for context
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    # Build simple game state for inject evaluation
    engine = RuleEngine(db)
    game_state = engine.get_game_state(game_id)

    # Trigger the inject
    result = inject_system.trigger_immediate_inject(
        request.inject_id,
        request.turn,
        game_state
    )

    if result is None:
        raise HTTPException(status_code=400, detail="Inject not found or not available")

    return {
        "success": True,
        "inject": result
    }


@router.post("/injects/{game_id}/cancel")
def cancel_inject(
    game_id: int,
    request: InjectCancelRequest
):
    """
    Cancel an available inject.
    """
    from app.services.inject_system import create_inject_system

    # Get or create inject system for this game
    if game_id not in _inject_systems:
        _inject_systems[game_id] = create_inject_system(game_id)

    inject_system = _inject_systems[game_id]

    success = inject_system.cancel_inject(request.inject_id)

    if not success:
        raise HTTPException(status_code=400, detail="Inject not found or not cancellable")

    return {
        "success": True,
        "message": f"Inject {request.inject_id} cancelled"
    }


@router.post("/injects/{game_id}/reset")
def reset_inject(
    game_id: int,
    request: InjectCancelRequest
):
    """
    Reset a triggered inject to available status.
    """
    from app.services.inject_system import create_inject_system

    # Get or create inject system for this game
    if game_id not in _inject_systems:
        _inject_systems[game_id] = create_inject_system(game_id)

    inject_system = _inject_systems[game_id]

    success = inject_system.reset_inject(request.inject_id)

    if not success:
        raise HTTPException(status_code=400, detail="Inject not found or not resettable")

    return {
        "success": True,
        "message": f"Inject {request.inject_id} reset to available"
    }


@router.get("/injects/{game_id}/effects")
def get_active_effects(game_id: int):
    """
    Get currently active effects for a game.
    Returns modifiers to be applied in adjudication.
    """
    from app.services.inject_system import create_inject_system

    # Get or create inject system for this game
    if game_id not in _inject_systems:
        _inject_systems[game_id] = create_inject_system(game_id)

    inject_system = _inject_systems[game_id]

    return {
        "game_id": game_id,
        "active_effects": inject_system.get_active_effects(),
        "modifiers": {
            "movement": inject_system.get_effect_modifier("movement"),
            "combat": inject_system.get_effect_modifier("combat"),
            "reconnaissance": inject_system.get_effect_modifier("reconnaissance"),
            "supply": inject_system.get_effect_modifier("supply"),
            "morale": inject_system.get_effect_modifier("morale")
        }
    }


@router.post("/injects/{game_id}/decrement-turn")
def decrement_effects_turn(game_id: int):
    """
    Decrement effect durations at end of turn.
    Called by turn commit/adjudication.
    """
    from app.services.inject_system import create_inject_system

    if game_id not in _inject_systems:
        return {
            "success": True,
            "message": "No active effects"
        }

    inject_system = _inject_systems[game_id]
    expired = inject_system.decrement_effect_duration(0)  # Turn is handled externally

    return {
        "success": True,
        "expired_effects": expired
    }


# ============================================================
# CPX-REPORTS: Report API Endpoints (Plan/Sync/Situation/Sustain)
# ============================================================

class ReportRequest(BaseModel):
    game_id: int = Field(..., gt=0)
    format: Literal["plan", "sync", "situation", "sustain"] = Field(..., description="Report format: plan (OPORD), sync (OPSUM), situation (SITREP/INTSUM), sustain (LOGSITREP)")
    turn: Optional[int] = None
    options: Optional[dict] = None


@router.post("/reports/generate")
def generate_report(request: ReportRequest, db: Session = Depends(get_db)):
    """
    Generate a military report in the specified format.
    - plan: OPORD (SMESC) - Commander's plan
    - sync: OPSUM - Operations synchronization
    - situation: SITREP/INTSUM - Current situation
    - sustain: LOGSITREP - Logistics status
    """
    from app.services.report_generator import get_report_generator
    from app.services.sitrep_generator import SitrepGenerator

    game = db.query(Game).filter(Game.id == request.game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    target_turn = request.turn if request.turn is not None else game.current_turn

    # Get engine state
    engine = RuleEngine(db)
    game_state = engine.get_game_state(request.game_id)
    game_state["turn"] = target_turn

    # Get enemy knowledge for reports
    enemy_knowledge = {"confirmed": [], "estimated": [], "unknown": []}
    orders = db.query(Order).filter(
        Order.game_id == request.game_id,
        Order.turn <= target_turn
    ).all()

    order_results = []
    for order in orders:
        order_results.append({
            "order_id": str(order.id),
            "unit_name": order.unit.name if order.unit else "Unknown",
            "order_type": order.order_type.value if order.order_type else "unknown",
            "outcome": "success",
            "intent": order.intent or ""
        })

    # Get sitrep generator
    sitrep_gen = SitrepGenerator(db)

    # Generate report based on format
    report_gen = get_report_generator(sitrep_gen)

    if request.format == "plan":
        # OPORD - Commander's Plan
        return report_gen.generate("sitrep", game_state, {"include_plan": True})
    elif request.format == "sync":
        # OPSUM - Operations Sync
        return report_gen.generate("opsumm", game_state, {
            "order_results": order_results,
            "current_orders": [],
            "planned_orders": []
        })
    elif request.format == "situation":
        # SITREP/INTSUM - Current Situation
        return report_gen.generate("intsumm", game_state, {
            "enemy_knowledge": enemy_knowledge,
            "order_results": order_results
        })
    elif request.format == "sustain":
        # LOGSITREP - Logistics/Sustainment
        return report_gen.generate("logsitrep", game_state, {})

    raise HTTPException(status_code=400, detail="Invalid report format")


@router.get("/reports/{game_id}")
def get_reports_list(game_id: int, db: Session = Depends(get_db)):
    """
    Get list of available reports for a game.
    """
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    # Get available turns with reports
    turns_with_reports = db.query(Turn).filter(
        Turn.game_id == game_id,
        Turn.sitrep.isnot(None)
    ).all()

    return {
        "game_id": game_id,
        "available_reports": [
            {
                "turn": t.turn_number,
                "has_sitrep": bool(t.sitrep)
            }
            for t in turns_with_reports
        ],
        "current_turn": game.current_turn
    }


# =============================================================================
# CPX-REPLAY: Replay API Endpoints
# =============================================================================

@router.get("/replay/{game_id}/timeline")
def get_replay_timeline(game_id: int, db: Session = Depends(get_db)):
    """
    Get event timeline for replay.
    """
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    replay_service = create_replay_service(game_id)
    if not replay_service.load_from_db(db, game_id):
        raise HTTPException(status_code=400, detail="Failed to load replay data")

    timeline = replay_service.get_event_timeline()
    return {
        "game_id": game_id,
        "seed": replay_service.seed,
        "turn_seeds": replay_service.get_turn_seeds(),
        "total_turns": replay_service.get_total_turns(),
        "timeline": timeline
    }


@router.get("/replay/{game_id}/turn/{turn_number}")
def get_replay_turn(game_id: int, turn_number: int, db: Session = Depends(get_db)):
    """
    Get replay data for a specific turn.
    """
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    replay_service = create_replay_service(game_id)
    if not replay_service.load_from_db(db, game_id):
        raise HTTPException(status_code=400, detail="Failed to load replay data")

    turn_summary = replay_service.get_turn_summary(turn_number)
    if not turn_summary:
        raise HTTPException(status_code=404, detail="Turn not found")

    return turn_summary


@router.get("/replay/{game_id}/state/{turn_number}")
def get_replay_state(game_id: int, turn_number: int, db: Session = Depends(get_db)):
    """
    Get reconstructed state at a specific turn.
    """
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    replay_service = create_replay_service(game_id)
    if not replay_service.load_from_db(db, game_id):
        raise HTTPException(status_code=400, detail="Failed to load replay data")

    state = replay_service.get_state_at_turn(turn_number)
    return {
        "turn": state.turn_number,
        "time": state.time,
        "weather": state.weather,
        "seed": state.seed,
        "turn_seed": state.turn_seed,
        "events": state.events
    }


@router.post("/replay/from-logs")
def create_replay_from_logs(log_data: List[Dict[str, Any]]):
    """
    Create a replay session from log data (for external replay viewers).
    """
    replay_service = create_replay_service()
    if not replay_service.load_from_logs(log_data):
        raise HTTPException(status_code=400, detail="Failed to load log data")

    return {
        "seed": replay_service.seed,
        "turn_seeds": replay_service.get_turn_seeds(),
        "total_turns": replay_service.get_total_turns(),
        "timeline": replay_service.get_event_timeline()
    }
