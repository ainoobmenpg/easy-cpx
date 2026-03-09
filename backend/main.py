from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import get_db, init_db
from app.api.routes import router as api_router
from app.models import Game, Unit, UnitStatus, SupplyLevel

app = FastAPI(title="Operational CPX API", version="0.1.0")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api", tags=["game"])


@app.on_event("startup")
def startup_event():
    """Initialize database and create default game"""
    from app.database import SessionLocal

    init_db()

    # Create default game if not exists
    db = SessionLocal()
    try:
        game = db.query(Game).filter(Game.id == 1).first()
        if not game:
            game = Game(name="Default Game")
            db.add(game)
            db.commit()
            db.refresh(game)

            # Create initial units with Israel 2026 scenario deployment
            # Player: northern border (X: 5-15, Y: 25-35)
            # Enemy: Lebanon side (X: 25-40, Y: 20-35)
            units = [
                Unit(game_id=1, name="1st Battalion", unit_type="nato_infantry", side="player", x=8, y=30, status=UnitStatus.INTACT, ammo=SupplyLevel.FULL, fuel=SupplyLevel.FULL, readiness=SupplyLevel.FULL),
                Unit(game_id=1, name="2nd Battalion", unit_type="nato_infantry", side="player", x=12, y=28, status=UnitStatus.INTACT, ammo=SupplyLevel.FULL, fuel=SupplyLevel.FULL, readiness=SupplyLevel.FULL),
                Unit(game_id=1, name="Alpha Company", unit_type="nato_armor", side="player", x=6, y=32, status=UnitStatus.INTACT, ammo=SupplyLevel.FULL, fuel=SupplyLevel.FULL, readiness=SupplyLevel.FULL),
                Unit(game_id=1, name="Bravo Company", unit_type="nato_armor", side="player", x=10, y=26, status=UnitStatus.INTACT, ammo=SupplyLevel.FULL, fuel=SupplyLevel.FULL, readiness=SupplyLevel.FULL),
                Unit(game_id=1, name="Artillery Battery A", unit_type="nato_artillery", side="player", x=5, y=28, status=UnitStatus.INTACT, ammo=SupplyLevel.FULL, fuel=SupplyLevel.FULL, readiness=SupplyLevel.FULL),
                Unit(game_id=1, name="Air Defense Platoon", unit_type="nato_air_defense", side="player", x=4, y=30, status=UnitStatus.INTACT, ammo=SupplyLevel.FULL, fuel=SupplyLevel.FULL, readiness=SupplyLevel.FULL),
                Unit(game_id=1, name="Recon Platoon", unit_type="nato_multirole", side="player", x=14, y=30, status=UnitStatus.INTACT, ammo=SupplyLevel.FULL, fuel=SupplyLevel.FULL, readiness=SupplyLevel.FULL),
                # Enemy units
                Unit(game_id=1, name="Enemy Tank Co 1", unit_type="wp_armor", side="enemy", x=30, y=28, status=UnitStatus.INTACT, ammo=SupplyLevel.FULL, fuel=SupplyLevel.FULL, readiness=SupplyLevel.FULL),
                Unit(game_id=1, name="Enemy Tank Co 2", unit_type="wp_armor", side="enemy", x=35, y=32, status=UnitStatus.INTACT, ammo=SupplyLevel.FULL, fuel=SupplyLevel.FULL, readiness=SupplyLevel.FULL),
                Unit(game_id=1, name="Enemy Motor Rifle 1", unit_type="wp_infantry", side="enemy", x=28, y=26, status=UnitStatus.INTACT, ammo=SupplyLevel.FULL, fuel=SupplyLevel.FULL, readiness=SupplyLevel.FULL),
                Unit(game_id=1, name="Enemy Motor Rifle 2", unit_type="wp_infantry", side="enemy", x=32, y=30, status=UnitStatus.INTACT, ammo=SupplyLevel.FULL, fuel=SupplyLevel.FULL, readiness=SupplyLevel.FULL),
                Unit(game_id=1, name="Enemy Artillery", unit_type="wp_artillery", side="enemy", x=38, y=28, status=UnitStatus.INTACT, ammo=SupplyLevel.FULL, fuel=SupplyLevel.FULL, readiness=SupplyLevel.FULL),
                Unit(game_id=1, name="Enemy SAM 1", unit_type="wp_air_defense", side="enemy", x=36, y=26, status=UnitStatus.INTACT, ammo=SupplyLevel.FULL, fuel=SupplyLevel.FULL, readiness=SupplyLevel.FULL),
                Unit(game_id=1, name="Enemy SAM 2", unit_type="wp_air_defense", side="enemy", x=40, y=30, status=UnitStatus.INTACT, ammo=SupplyLevel.FULL, fuel=SupplyLevel.FULL, readiness=SupplyLevel.FULL),
            ]
            for unit in units:
                db.add(unit)
            db.commit()
    finally:
        db.close()


@app.get("/")
def read_root():
    return {"message": "Operational CPX API", "version": "0.1.0"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
