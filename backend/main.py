import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import get_db, init_db
from app.api.routes import router as api_router
from app.api.auth_routes import router as auth_router
from app.api.websocket_routes import router as ws_router
from app.api.opord_routes import router as opord_router
from app.api.control_measures_routes import router as cm_router
from app.api.ato_aco_routes import router as ato_router
from app.api.chat_routes import router as chat_router
from app.api.training_routes import router as training_router
from app.api.sync_matrix_routes import router as sync_matrix_router
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
app.include_router(auth_router, prefix="/api", tags=["auth"])
app.include_router(ws_router, tags=["websocket"])
app.include_router(opord_router, prefix="/api", tags=["opord"])
app.include_router(cm_router, prefix="/api", tags=["control-measures"])
app.include_router(ato_router, prefix="/api", tags=["ato-aco"])
app.include_router(chat_router, prefix="/api", tags=["chat"])
app.include_router(training_router, prefix="/api", tags=["training"])
app.include_router(sync_matrix_router, prefix="/api", tags=["sync-matrix"])


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
