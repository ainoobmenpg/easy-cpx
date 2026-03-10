# Training Scoreboard API Routes
from fastapi import APIRouter
from typing import Dict, Optional
from pydantic import BaseModel

from app.services.training_scoreboard import TrainingScoreboard

router = APIRouter(prefix="/training", tags=["training"])

# In-memory storage for scoreboards (in production, use database)
_scoreboards: Dict[int, TrainingScoreboard] = {}


class InitializeScoreboardRequest(BaseModel):
    game_id: int
    player_units: int
    enemy_units: int
    target_turns: int


class UpdateScoreboardRequest(BaseModel):
    game_id: int
    turn_number: int
    player_destroyed: int = 0
    enemy_destroyed: int = 0
    player_damaged: int = 0
    enemy_damaged: int = 0
    ccir_updates: Optional[Dict[str, float]] = None
    roe_violations: Optional[list] = None
    time_bonus: int = 0
    time_penalty: int = 0


class FinalizeScoreboardRequest(BaseModel):
    game_id: int


@router.post("/initialize")
async def initialize_scoreboard(request: InitializeScoreboardRequest):
    """Initialize a new training scoreboard for a game"""
    scoreboard = TrainingScoreboard(request.game_id)
    scoreboard.initialize(
        player_units=request.player_units,
        enemy_units=request.enemy_units,
        target_turns=request.target_turns
    )
    _scoreboards[request.game_id] = scoreboard

    return {
        "status": "initialized",
        "game_id": request.game_id,
        "message": f"Training scoreboard initialized with {request.player_units} player units, {request.enemy_units} enemy units"
    }


@router.post("/update")
async def update_scoreboard(request: UpdateScoreboardRequest):
    """Update scoreboard with turn results"""
    scoreboard = _scoreboards.get(request.game_id)
    if not scoreboard:
        return {"error": "Scoreboard not initialized"}

    # Update CCIR progress
    if request.ccir_updates:
        for ccir_id, value in request.ccir_updates.items():
            scoreboard.ccir_tracker.update_progress(ccir_id, value, request.turn_number)

    # Record ROE violations
    if request.roe_violations:
        for violation in request.roe_violations:
            scoreboard.roe_tracker.record_violation(
                violation.get("rule_id", "roe_1"),
                violation.get("details", "Unknown violation"),
                request.turn_number
            )

    # Record time bonuses/penalties
    if request.time_bonus > 0:
        scoreboard.time_tracker.add_bonus("manual_bonus", request.time_bonus)
    if request.time_penalty > 0:
        scoreboard.time_tracker.add_penalty("manual_penalty", request.time_penalty)

    # Update casualties
    scoreboard.casualty_tracker.update_casualties(
        player_destroyed=request.player_destroyed,
        enemy_destroyed=request.enemy_destroyed,
        player_damaged=request.player_damaged,
        enemy_damaged=request.enemy_damaged
    )

    # Record turn
    stats = {
        "player": {"destroyed": request.player_destroyed, "damaged": request.player_damaged},
        "enemy": {"destroyed": request.enemy_destroyed, "damaged": request.enemy_damaged}
    }
    scoreboard.record_turn(request.turn_number, stats)

    return {
        "status": "updated",
        "turn": request.turn_number,
        "metrics": scoreboard.get_realtime_metrics()
    }


@router.get("/metrics/{game_id}")
async def get_metrics(game_id: int):
    """Get current training metrics for a game"""
    scoreboard = _scoreboards.get(game_id)
    if not scoreboard:
        return {"error": "Scoreboard not initialized"}

    return scoreboard.get_realtime_metrics()


@router.get("/summary/{game_id}")
async def get_summary(game_id: int):
    """Get complete scoreboard summary with grades"""
    scoreboard = _scoreboards.get(game_id)
    if not scoreboard:
        return {"error": "Scoreboard not initialized"}

    return scoreboard.get_summary()


@router.post("/finalize")
async def finalize_scoreboard(request: FinalizeScoreboardRequest):
    """Finalize scoreboard and get final grade"""
    scoreboard = _scoreboards.get(request.game_id)
    if not scoreboard:
        return {"error": "Scoreboard not initialized"}

    summary = scoreboard.get_summary()

    return {
        "status": "finalized",
        "game_id": request.game_id,
        "final_grade": summary["grade"],
        "star_rating": summary["star_rating"],
        "overall_score": summary["overall_score"],
        "summary": summary
    }


@router.delete("/{game_id}")
async def delete_scoreboard(game_id: int):
    """Delete a scoreboard"""
    if game_id in _scoreboards:
        del _scoreboards[game_id]
        return {"status": "deleted", "game_id": game_id}
    return {"error": "Scoreboard not found"}
