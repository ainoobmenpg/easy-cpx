from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./operational_cpx.db"
)

# For SQLite compatibility
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def migrate_db():
    """Migrate database schema - add missing columns to existing tables"""
    inspector = inspect(engine)

    # Get existing tables
    tables = inspector.get_table_names()

    if "games" in tables:
        existing_columns = [col["name"] for col in inspector.get_columns("games")]

        # Columns to add if missing
        new_game_columns = {
            "terrain_data": "JSON",
            "map_width": "INTEGER DEFAULT 50",
            "map_height": "INTEGER DEFAULT 50",
            "player_score": "INTEGER DEFAULT 0",
            "enemy_score": "INTEGER DEFAULT 0",
            "ccir_data": "JSON",
            "planning_cycle": "JSON",
            "air_tasking_cycle": "JSON",
            "logistics_cycle": "JSON",
            "game_mode": "TEXT DEFAULT 'simulation'",
        }

        with engine.connect() as conn:
            for col_name, col_type in new_game_columns.items():
                if col_name not in existing_columns:
                    try:
                        # For SQLite, use ALTER TABLE ADD COLUMN
                        if "sqlite" in DATABASE_URL:
                            conn.execute(text(f"ALTER TABLE games ADD COLUMN {col_name} {col_type}"))
                        else:
                            # For PostgreSQL, use ADD COLUMN
                            conn.execute(text(f"ALTER TABLE games ADD COLUMN {col_name} {col_type}"))
                        conn.commit()
                        print(f"Added column {col_name} to games table")
                    except Exception as e:
                        print(f"Column {col_name} may already exist: {e}")

    if "units" in tables:
        existing_columns = [col["name"] for col in inspector.get_columns("units")]

        new_unit_columns = {
            "infantry_subtype": "TEXT",
            "recon_value": "REAL DEFAULT 1.0",
            "visibility_range": "INTEGER DEFAULT 3",
            "observation_confidence": "TEXT",
            "last_observed_turn": "INTEGER",
            "confidence_score": "INTEGER",
            "estimated_x": "REAL",
            "estimated_y": "REAL",
            "position_accuracy": "INTEGER DEFAULT 0",
            "last_known_type": "TEXT",
            "observation_sources": "JSON",
            "interceptors": "INTEGER DEFAULT 0",
            "precision_munitions": "INTEGER DEFAULT 0",
            "faction": "TEXT",
            "echelon": "TEXT",
            "callsign": "TEXT",
        }

        with engine.connect() as conn:
            for col_name, col_type in new_unit_columns.items():
                if col_name not in existing_columns:
                    try:
                        if "sqlite" in DATABASE_URL:
                            conn.execute(text(f"ALTER TABLE units ADD COLUMN {col_name} {col_type}"))
                        else:
                            conn.execute(text(f"ALTER TABLE units ADD COLUMN {col_name} {col_type}"))
                        conn.commit()
                        print(f"Added column {col_name} to units table")
                    except Exception as e:
                        print(f"Column {col_name} may already exist: {e}")


def init_db():
    """Initialize database tables"""
    from app.models import Base
    Base.metadata.create_all(bind=engine)
    # Run migrations to add missing columns
    migrate_db()
