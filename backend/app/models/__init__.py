# Database models for Operational CPX
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Enum, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()


class UnitStatus(enum.Enum):
    INTACT = "intact"
    LIGHT_DAMAGE = "light_damage"
    MEDIUM_DAMAGE = "medium_damage"
    HEAVY_DAMAGE = "heavy_damage"
    DESTROYED = "destroyed"


class SupplyLevel(enum.Enum):
    FULL = "full"
    DEPLETED = "depleted"
    EXHAUSTED = "exhausted"


class OrderType(enum.Enum):
    MOVE = "move"
    ATTACK = "attack"
    DEFEND = "defend"
    SUPPORT = "support"
    RETREAT = "retreat"
    RECON = "recon"
    SUPPLY = "supply"
    SPECIAL = "special"


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    current_turn = Column(Integer, default=1)
    current_time = Column(String, default="06:00")
    weather = Column(String, default="clear")
    phase = Column(String, default="orders")  # orders, adjudication, sitrep
    is_active = Column(Boolean, default=True)

    units = relationship("Unit", back_populates="game")
    turns = relationship("Turn", back_populates="game")
    orders = relationship("Order", back_populates="game")


class Unit(Base):
    __tablename__ = "units"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"))
    name = Column(String, nullable=False)
    unit_type = Column(String, nullable=False)  # infantry, armor, artillery, air, etc.
    side = Column(String, nullable=False)  # player, enemy
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    status = Column(Enum(UnitStatus), default=UnitStatus.INTACT)
    ammo = Column(Enum(SupplyLevel), default=SupplyLevel.FULL)
    fuel = Column(Enum(SupplyLevel), default=SupplyLevel.FULL)
    readiness = Column(Enum(SupplyLevel), default=SupplyLevel.FULL)
    strength = Column(Integer, default=100)  # 0-100

    # Extended resources (for advanced resource management)
    interceptors = Column(Integer, default=0)  # Air defense missiles
    precision_munitions = Column(Integer, default=0)  # Guided munitions

    game = relationship("Game", back_populates="units")
    order = relationship("Order", back_populates="unit", uselist=False)


class Turn(Base):
    __tablename__ = "turns"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"))
    turn_number = Column(Integer, nullable=False)
    time = Column(String, nullable=False)
    weather = Column(String)
    phase = Column(String)

    # AI generated content
    sitrep = Column(JSON)
    excon_orders = Column(JSON)

    game = relationship("Game", back_populates="turns")
    orders = relationship("Order", back_populates="turn")
    events = relationship("Event", back_populates="turn")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"))
    unit_id = Column(Integer, ForeignKey("units.id"))
    turn_id = Column(Integer, ForeignKey("turns.id"))

    order_type = Column(Enum(OrderType), nullable=False)
    target_units = Column(JSON)  # List of unit IDs
    intent = Column(Text, nullable=False)
    location_x = Column(Float)
    location_y = Column(Float)
    location_name = Column(String)
    parameters = Column(JSON)

    # Parsed and result
    parsed_order = Column(JSON)
    result = Column(JSON)
    outcome = Column(String)  # success, partial, failed, blocked, cancelled

    game = relationship("Game", back_populates="orders")
    unit = relationship("Unit", back_populates="order")
    turn = relationship("Turn", back_populates="orders")


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    turn_id = Column(Integer, ForeignKey("turns.id"))

    event_type = Column(String, nullable=False)
    data = Column(JSON)
    description = Column(Text)

    turn = relationship("Turn", back_populates="events")


# Fog of War - Player knowledge
class PlayerKnowledge(Base):
    __tablename__ = "player_knowledge"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"))

    # What the player knows
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=True)
    x = Column(Float)
    y = Column(Float)
    area_name = Column(String)

    # Knowledge level
    confidence = Column(String)  # confirmed, estimated, unknown
    last_observed_turn = Column(Integer)

    # Player's interpretation
    interpreted_type = Column(String)
    interpreted_side = Column(String)


# Commander Order - High-level command intent
class CommanderOrder(Base):
    __tablename__ = "commander_orders"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"))
    turn_issued = Column(Integer, nullable=False)

    # Command hierarchy
    intent = Column(Text)  # Strategic intent
    mission = Column(Text)  # Specific mission
    constraints = Column(Text)  # Operational constraints
    roe = Column(Text)  # Rules of Engagement
    priorities = Column(JSON)  # Priority list
    time_limit = Column(String)  # Time constraint

    # Available forces
    available_forces = Column(JSON)  # List of available units

    # Reporting requirements
    reporting_requirements = Column(JSON)  # Events that must be reported
    last_reported = Column(JSON)  # What was last reported

    # Status
    status = Column(String, default="active")  # active, superseded, completed
    superseded_by = Column(Integer, ForeignKey("commander_orders.id"), nullable=True)

    game = relationship("Game")
