import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import get_db, init_db
from app.api.routes import router as api_router
from app.models import Game, Unit, UnitStatus, SupplyLevel

app = FastAPI(title="Operational CPX API", version="0.1.0")

# CORS configuration from environment variable
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api", tags=["game"])


@app.on_event("startup")
def startup_event():
    """Initialize database"""
    init_db()
    # Game creation is now handled via POST /api/games/ or POST /api/game/start
    # No default game is created at startup


@app.get("/")
def read_root():
    return {"message": "Operational CPX API", "version": "0.1.0"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
