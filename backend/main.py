from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import get_db, init_db
from app.api.routes import router as api_router
from app.models import Game, Unit, UnitStatus

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

            # Create initial units
            units = [
                Unit(game_id=1, name="第1大隊", unit_type="infantry", side="player", x=10, y=25, status=UnitStatus.INTACT),
                Unit(game_id=1, name="第2大隊", unit_type="infantry", side="player", x=15, y=20, status=UnitStatus.INTACT),
                Unit(game_id=1, name="第3大隊", unit_type="armor", side="player", x=12, y=30, status=UnitStatus.INTACT),
                Unit(game_id=1, name="敵主力", unit_type="infantry", side="enemy", x=35, y=25, status=UnitStatus.INTACT),
                Unit(game_id=1, name="敵増援", unit_type="armor", side="enemy", x=40, y=20, status=UnitStatus.INTACT),
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
