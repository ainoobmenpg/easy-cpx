# Database models for Operational CPX
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Enum, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()


# Unit Type Enum - unified vocabulary
class UnitType(enum.Enum):
    ARMOR = "armor"
    INFANTRY = "infantry"
    ATGM = "atgm"
    SNIPER = "sniper"
    SCOUT = "scout"
    ARTILLERY = "artillery"
    AIR_DEFENSE = "air_defense"
    ATTACK_HELO = "attack_helo"
    TRANSPORT_HELO = "transport_helo"
    AIRCRAFT = "aircraft"
    UAV = "uav"
    RECON = "recon"
    SUPPORT = "support"


# Mapping from legacy unit type strings to UnitType
LEGACY_UNIT_TYPE_MAP: dict[str, UnitType] = {
    # NATO prefixes
    "nato_armor": UnitType.ARMOR,
    "nato_infantry": UnitType.INFANTRY,
    "nato_atgm": UnitType.ATGM,
    "nato_artillery": UnitType.ARTILLERY,
    "nato_air_defense": UnitType.AIR_DEFENSE,
    "nato_recon": UnitType.RECON,
    "nato_uav": UnitType.UAV,
    "nato_aircraft": UnitType.AIRCRAFT,
    "nato_attack_helo": UnitType.ATTACK_HELO,
    "nato_transport_helo": UnitType.TRANSPORT_HELO,
    "nato_support": UnitType.SUPPORT,
    # WP prefixes
    "wp_armor": UnitType.ARMOR,
    "wp_infantry": UnitType.INFANTRY,
    "wp_atgm": UnitType.ATGM,
    "wp_artillery": UnitType.ARTILLERY,
    "wp_air_defense": UnitType.AIR_DEFENSE,
    "wp_recon": UnitType.RECON,
    "wp_uav": UnitType.UAV,
    "wp_aircraft": UnitType.AIRCRAFT,
    "wp_attack_helo": UnitType.ATTACK_HELO,
    "wp_transport_helo": UnitType.TRANSPORT_HELO,
    "wp_support": UnitType.SUPPORT,
    # Direct mappings
    "armor": UnitType.ARMOR,
    "tank": UnitType.ARMOR,
    "infantry": UnitType.INFANTRY,
    "inf": UnitType.INFANTRY,
    "atgm": UnitType.ATGM,
    "anti-tank": UnitType.ATGM,
    "sniper": UnitType.SNIPER,
    "scout": UnitType.SCOUT,
    "artillery": UnitType.ARTILLERY,
    "howitzer": UnitType.ARTILLERY,
    "mlrs": UnitType.ARTILLERY,
    "air_defense": UnitType.AIR_DEFENSE,
    "sam": UnitType.AIR_DEFENSE,
    "patriot": UnitType.AIR_DEFENSE,
    "flak": UnitType.AIR_DEFENSE,
    "attack_helo": UnitType.ATTACK_HELO,
    "apache": UnitType.ATTACK_HELO,
    "hind": UnitType.ATTACK_HELO,
    "transport_helo": UnitType.TRANSPORT_HELO,
    "blackhawk": UnitType.TRANSPORT_HELO,
    "mi17": UnitType.TRANSPORT_HELO,
    "aircraft": UnitType.AIRCRAFT,
    "fighter": UnitType.AIRCRAFT,
    "uav": UnitType.UAV,
    "drone": UnitType.UAV,
    "recon": UnitType.RECON,
    "support": UnitType.SUPPORT,
    "supply": UnitType.SUPPORT,
}


def normalize_unit_type(unit_type: str) -> str:
    """Normalize any unit type string to canonical form"""
    if not unit_type:
        return "infantry"  # Default fallback

    unit_type_lower = unit_type.lower()

    # Check exact match in legacy map
    if unit_type_lower in LEGACY_UNIT_TYPE_MAP:
        return LEGACY_UNIT_TYPE_MAP[unit_type_lower].value

    # Try partial matching for specific weapons (check longer patterns first)
    # Artillery first (m109, pzh2000 are self-propelled artillery)
    if "m109" in unit_type_lower or "pzh" in unit_type_lower or "howitzer" in unit_type_lower or \
       "mlrs" in unit_type_lower or "grad" in unit_type_lower:
        return UnitType.ARTILLERY.value

    # Aircraft types
    if "aircraft" in unit_type_lower or "fighter" in unit_type_lower or "f15" in unit_type_lower or \
       "f16" in unit_type_lower or "mig" in unit_type_lower or "tornado" in unit_type_lower or \
       "su25" in unit_type_lower or "f4" in unit_type_lower or "f5" in unit_type_lower:
        return UnitType.AIRCRAFT.value

    # UAV types
    if "uav" in unit_type_lower or "drone" in unit_type_lower or "reaper" in unit_type_lower or \
       "shadow" in unit_type_lower or "forpost" in unit_type_lower:
        return UnitType.UAV.value

    # Attack helicopter
    if "attack" in unit_type_lower and "helo" in unit_type_lower or "apache" in unit_type_lower or \
       "hind" in unit_type_lower:
        return UnitType.ATTACK_HELO.value

    # Transport helicopter
    if "transport" in unit_type_lower and "helo" in unit_type_lower or "blackhawk" in unit_type_lower or \
       "mi17" in unit_type_lower or "hip" in unit_type_lower:
        return UnitType.TRANSPORT_HELO.value

    # Air defense
    if "air_defense" in unit_type_lower or "sam" in unit_type_lower or "patriot" in unit_type_lower or \
       "flak" in unit_type_lower or "gepard" in unit_type_lower or "stinger" in unit_type_lower or \
       "sa6" in unit_type_lower or "sa11" in unit_type_lower:
        return UnitType.AIR_DEFENSE.value

    # Armor (check after artillery since some have "tank" but also numbers)
    if "tank" in unit_type_lower or "m1" in unit_type_lower or "leopard" in unit_type_lower or \
       "t72" in unit_type_lower or "t80" in unit_type_lower or "bradley" in unit_type_lower or \
       "bmp" in unit_type_lower or "marder" in unit_type_lower:
        return UnitType.ARMOR.value

    # Default to infantry
    return UnitType.INFANTRY.value


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


class OrderLevel(enum.Enum):
    TACTICAL = "tactical"  # Tactical: recon, defensive positions, urban combat, special ops
    OPERATIONAL = "operational"  # Operational: division movement, air ops, missile, EW, air defense
    STRATEGIC = "strategic"  # Strategic: mobilization, war start, deterrence, info warfare


class InfantrySubtype(enum.Enum):
    STANDARD = "standard"  # Standard infantry, no special bonuses
    ATGM = "atgm"  # Anti-tank missile infantry, +0.3 vs armor
    SNIPER = "sniper"  # Sniper teams, +2 range, higher hit probability
    SCOUT = "scout"  # Scout infantry, +0.2 recon, provides recon support


# Infantry subtype bonuses and attributes
INFANTRY_SUBTYPE_ATTRIBUTES = {
    InfantrySubtype.STANDARD: {
        "name": "標準歩兵",
        "combat_bonus": 0.0,
        "recon_bonus": 0.0,
        "range_bonus": 0,
    },
    InfantrySubtype.ATGM: {
        "name": "対戦車导弹兵",
        "combat_bonus": 0.3,  # vs armor
        "recon_bonus": 0.0,
        "range_bonus": 1,
    },
    InfantrySubtype.SNIPER: {
        "name": "狙撃手",
        "combat_bonus": 0.2,  # vs infantry (higher hit rate)
        "recon_bonus": 0.1,
        "range_bonus": 2,
    },
    InfantrySubtype.SCOUT: {
        "name": "偵察兵",
        "combat_bonus": 0.0,
        "recon_bonus": 0.2,
        "range_bonus": 0,
    },
}


# Extended reconnaissance confidence levels
class ReconConfidence(enum.Enum):
    CONFIRMED = "confirmed"     # Precisely located, type verified
    ESTIMATED = "estimated"    # Approximate position, type uncertain
    UNKNOWN = "unknown"        # Presence unknown
    FALSE = "false"            # Known to be false


class GameMode(enum.Enum):
    SIMULATION = "simulation"  # Full rule engine
    ARCADE = "arcade"  # Simplified 2D6 rules
    REPLAY = "replay"  # Replay mode from logs


# =============================================================================
# CPX-CYCLES: Cycle Management Enums
# =============================================================================

class CycleType(enum.Enum):
    PLANNING = "planning"
    AIR_TASKING = "air_tasking"
    LOGISTICS = "logistics"


class CyclePhase(enum.Enum):
    PLANNING = "planning"
    EXECUTION = "execution"


class CycleStatus(enum.Enum):
    ON_TRACK = "on_track"
    DELAYED = "delayed"
    FAILED = "failed"


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    current_turn = Column(Integer, default=1)
    current_date = Column(String, default="2026-03-06")  # Default scenario date
    current_time = Column(String, default="05:40")
    weather = Column(String, default="clear")
    phase = Column(String, default="orders")  # orders, adjudication, sitrep
    is_active = Column(Boolean, default=True)
    scenario_id = Column(String, nullable=True)  # Scenario ID for this game
    game_mode = Column(Enum(GameMode, values_callable=lambda e: [m.value for m in e]), default=GameMode.SIMULATION)  # simulation or arcade

    # Terrain data - stored as JSON to persist across turns
    terrain_data = Column(JSON, nullable=True)

    # Map configuration from scenario
    map_width = Column(Integer, default=50)
    map_height = Column(Integer, default=50)

    # Arcade mode scoring (VP - Victory Points)
    player_score = Column(Integer, default=0)
    enemy_score = Column(Integer, default=0)

    # CCIR/PIR/ROE data for Arcade mode (stored as JSON)
    ccir_data = Column(JSON, nullable=True)

    # CPX-CYCLES: Cycle management (stored as JSON)
    # Each cycle: {"phase": "planning|execution", "deadline_turn": int, "status": "on_track|delayed|failed", "last_updated": "YYYY-MM-DD"}
    planning_cycle = Column(JSON, nullable=True)
    air_tasking_cycle = Column(JSON, nullable=True)
    logistics_cycle = Column(JSON, nullable=True)

    units = relationship("Unit", back_populates="game", cascade="all, delete-orphan")
    turns = relationship("Turn", back_populates="game", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="game", cascade="all, delete-orphan")
    player_knowledge = relationship("PlayerKnowledge", back_populates="game", cascade="all, delete-orphan")
    enemy_knowledge = relationship("EnemyKnowledge", back_populates="game", cascade="all, delete-orphan")
    commander_orders = relationship("CommanderOrder", back_populates="game", cascade="all, delete-orphan")


# Arcade-specific simplified unit data (lightweight version)
class ArcadeUnit(Base):
    __tablename__ = "arcade_units"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"))
    name = Column(String, nullable=False)
    unit_type = Column(String, nullable=False)  # infantry, armor, artillery
    side = Column(String, nullable=False)  # player, enemy
    x = Column(Integer, nullable=False)  # Grid position (0-11)
    y = Column(Integer, nullable=False)  # Grid position (0-7)
    strength = Column(Integer, default=10)  # 0-10 (simplified from 0-100)
    can_move = Column(Boolean, default=True)
    can_attack = Column(Boolean, default=True)
    has_supplied = Column(Boolean, default=False)  # Supply action used

    # STRIKE command specific fields
    strike_remaining = Column(Integer, default=3)  # Starting 3 strikes per game
    strike_used_this_turn = Column(Boolean, default=False)  # Cannot use consecutively
    strike_next_attack_blocked = Column(Boolean, default=False)  # Next turn attack blocked

    game = relationship("Game")


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

    # Infantry subtype for specialized infantry units
    infantry_subtype = Column(String, nullable=True)  # standard, atgm, sniper, scout
    # Unit reconnaissance and visibility attributes
    recon_value = Column(Float, default=1.0)  # Base reconnaissance value
    visibility_range = Column(Integer, default=3)  # Base visibility range in cells
    # Observation tracking (for Fog of War)
    observation_confidence = Column(String, nullable=True)  # confirmed, estimated, unknown
    last_observed_turn = Column(Integer, nullable=True)

    # Extended reconnaissance tracking (new fields)
    # Detailed confidence score (0-100)
    confidence_score = Column(Integer, nullable=True)
    # Estimated position (for estimated/unknown)
    estimated_x = Column(Float, nullable=True)
    estimated_y = Column(Float, nullable=True)
    # Position accuracy in cells (higher = less accurate)
    position_accuracy = Column(Integer, default=0)
    # Last known type (may be different from actual)
    last_known_type = Column(String, nullable=True)
    # Observation sources (which unit observed)
    observation_sources = Column(JSON, nullable=True)

    # Extended resources (for advanced resource management)
    interceptors = Column(Integer, default=0)  # Air defense missiles
    precision_munitions = Column(Integer, default=0)  # Guided munitions

    # C2: Multi-national support fields
    faction = Column(String, nullable=True)  # National faction (US, GER, UK, OPFOR)
    echelon = Column(String, nullable=True)  # Unit echelon (platoon, company, battalion)
    callsign = Column(String, nullable=True)  # Radio callsign (ALPHA, BRAVO, 1-1)

    game = relationship("Game", back_populates="units")
    orders = relationship("Order", back_populates="unit", cascade="all, delete-orphan")  # 1:N for turn history
    player_knowledge = relationship("PlayerKnowledge", back_populates="unit", viewonly=True)
    enemy_knowledge = relationship("EnemyKnowledge", back_populates="player_unit", viewonly=True)


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
    enemy_results = Column(JSON)  # Enemy AI decision results

    game = relationship("Game", back_populates="turns")
    orders = relationship("Order", back_populates="turn", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="turn", cascade="all, delete-orphan")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"))
    unit_id = Column(Integer, ForeignKey("units.id"))
    turn_id = Column(Integer, ForeignKey("turns.id"))

    order_type = Column(Enum(OrderType), nullable=False)
    order_level = Column(Enum(OrderLevel), default=OrderLevel.TACTICAL)
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
    unit = relationship("Unit", back_populates="orders")  # cascade handled on Unit side
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
    game_id = Column(Integer, ForeignKey("games.id", ondelete="CASCADE"))

    # What the player knows
    unit_id = Column(Integer, ForeignKey("units.id", ondelete="SET NULL"), nullable=True)
    x = Column(Float)
    y = Column(Float)
    area_name = Column(String)

    # Knowledge level
    confidence = Column(String)  # confirmed, estimated, unknown
    confidence_score = Column(Integer, default=0)  # 0-100 percentage
    last_observed_turn = Column(Integer)

    # Player's interpretation
    interpreted_type = Column(String)
    interpreted_side = Column(String)

    # Position accuracy
    position_accuracy = Column(Integer, default=0)  # cells of error

    # Relationships
    game = relationship("Game", back_populates="player_knowledge")
    unit = relationship("Unit", back_populates="player_knowledge")


# Enemy Knowledge - What enemy knows about player units
# This tracks enemy reconnaissance and information control
class EnemyKnowledge(Base):
    __tablename__ = "enemy_knowledge"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id", ondelete="CASCADE"))

    # What the enemy knows about player unit
    player_unit_id = Column(Integer, ForeignKey("units.id", ondelete="SET NULL"), nullable=True)

    # Known position (may be different from true position due to fog of war)
    known_x = Column(Float, nullable=True)
    known_y = Column(Float, nullable=True)
    area_name = Column(String, nullable=True)

    # Knowledge level
    confidence = Column(String)  # confirmed, estimated, unknown
    confidence_score = Column(Integer, default=0)  # 0-100 percentage
    last_observed_turn = Column(Integer)

    # Enemy's interpretation (may be wrong)
    interpreted_type = Column(String, nullable=True)
    is_deceptive = Column(Boolean, default=False)  # Player has set a decoy

    # Position accuracy
    position_accuracy = Column(Integer, default=0)  # cells of error

    # Relationships
    game = relationship("Game", back_populates="enemy_knowledge")
    player_unit = relationship("Unit", back_populates="enemy_knowledge")


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

    game = relationship("Game", back_populates="commander_orders")


# =============================================================================
# CPX-4: MEL/MIL (Inject) System Models
# =============================================================================

class Inject(Base):
    """Master Events List / Inject List entry"""
    __tablename__ = "injects"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"))

    # Inject identification
    name = Column(String, nullable=False)
    description = Column(Text)
    inject_type = Column(String, nullable=False)  # communications_outage, ew_interference, etc.

    # Timing and status
    timing = Column(String, nullable=False)  # immediate, conditional, scheduled
    status = Column(String, default="available")  # available, triggered, expired, cancelled

    # Conditions for conditional triggers
    conditions = Column(JSON)  # List of condition dicts
    scheduled_turn = Column(Integer, nullable=True)  # For scheduled injects

    # Effects when triggered
    effects = Column(JSON)  # List of effect dicts
    observations = Column(JSON)  # List of observation items

    # Evaluation
    evaluation_points = Column(Integer, default=10)
    difficulty = Column(String, default="medium")  # easy, medium, hard

    # Tracking
    triggered_turn = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    game = relationship("Game")


class InjectLog(Base):
    """Audit log for inject triggers and effects"""
    __tablename__ = "inject_logs"

    id = Column(Integer, primary_key=True, index=True)
    inject_id = Column(Integer, ForeignKey("injects.id"))
    game_id = Column(Integer, ForeignKey("games.id"))
    turn = Column(Integer, nullable=False)

    # Trigger information
    timestamp = Column(DateTime, default=datetime.utcnow)
    trigger_type = Column(String, nullable=False)  # immediate, condition_met, scheduled

    # What was applied
    effects_applied = Column(JSON)  # List of effect dicts applied
    results = Column(JSON)  # Result of the inject

    inject = relationship("Inject")
    game = relationship("Game")


# =============================================================================
# Arcade Model Conversion Utilities
# =============================================================================

# Arcade map size (fixed 12x8 grid)
ARCADE_MAP_WIDTH = 12
ARCADE_MAP_HEIGHT = 8

# Unit type mapping: simulation -> arcade
# Infantry types -> infantry
# Armor types -> armor
# Artillery types -> artillery
# Air/Air Defense -> simplified to basic types
ARCADE_UNIT_TYPE_MAP: dict[str, str] = {
    "infantry": "infantry",
    "armor": "armor",
    "atgm": "infantry",
    "sniper": "infantry",
    "scout": "infantry",
    "recon": "infantry",
    "artillery": "artillery",
    "air_defense": "armor",  # Simplified
    "attack_helo": "armor",  # Simplified
    "transport_helo": "armor",  # Simplified
    "aircraft": "armor",  # Simplified
    "uav": "infantry",  # Simplified
    "support": "infantry",
}


def to_arcade_position(x: float, y: float, map_width: int = 50, map_height: int = 30) -> tuple[int, int]:
    """Convert simulation coordinates to arcade grid (12x8).

    Args:
        x: Simulation x coordinate
        y: Simulation y coordinate
        map_width: Original map width (default 50)
        map_height: Original map height (default 30)

    Returns:
        Tuple of (arcade_x, arcade_y) in range (0-11, 0-7)
    """
    arcade_x = min(int(x / map_width * ARCADE_MAP_WIDTH), ARCADE_MAP_WIDTH - 1)
    arcade_y = min(int(y / map_height * ARCADE_MAP_HEIGHT), ARCADE_MAP_HEIGHT - 1)
    return (arcade_x, arcade_y)


def to_simulation_position(arcade_x: int, arcade_y: int, map_width: int = 50, map_height: int = 30) -> tuple[float, float]:
    """Convert arcade grid to simulation coordinates.

    Args:
        arcade_x: Arcade grid x (0-11)
        arcade_y: Arcade grid y (0-7)
        map_width: Target map width (default 50)
        map_height: Target map height (default 30)

    Returns:
        Tuple of (sim_x, sim_y)
    """
    sim_x = (arcade_x + 0.5) / ARCADE_MAP_WIDTH * map_width
    sim_y = (arcade_y + 0.5) / ARCADE_MAP_HEIGHT * map_height
    return (sim_x, sim_y)


def arcade_unit_type(unit_type: str) -> str:
    """Convert simulation unit type to arcade simplified type.

    Args:
        unit_type: Simulation unit type string

    Returns:
        Arcade unit type: "infantry", "armor", or "artillery"
    """
    normalized = normalize_unit_type(unit_type)
    return ARCADE_UNIT_TYPE_MAP.get(normalized, "infantry")


def to_arcade_strength(strength: int) -> int:
    """Convert simulation strength (0-100) to arcade (0-10).

    Args:
        strength: Simulation strength value (0-100)

    Returns:
        Arcade strength (0-10)
    """
    return max(0, min(10, int(strength / 10)))


def from_arcade_strength(arcade_strength: int) -> int:
    """Convert arcade strength (0-10) to simulation (0-100).

    Args:
        arcade_strength: Arcade strength value (0-10)

    Returns:
        Simulation strength (0-100)
    """
    return arcade_strength * 10


def is_arcade_game(game_mode: GameMode | str) -> bool:
    """Check if game mode is arcade.

    Args:
        game_mode: GameMode enum or string

    Returns:
        True if arcade mode
    """
    if isinstance(game_mode, str):
        return game_mode == "arcade"
    return game_mode == GameMode.ARCADE


# =============================================================================
# RBAC Models
# =============================================================================

class UserRole(enum.Enum):
    BLUE = "blue"      # Player forces (NATO/Western)
    RED = "red"         # Enemy forces
    WHITE = "white"    # Umpire/Admin/Observer with full visibility
    OBSERVER = "observer"  # Read-only observer
    ADMIN = "admin"     # Full system admin


class User(Base):
    """User account for multi-role access"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.OBSERVER)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)


class GamePlayer(Base):
    """Association table for users assigned to games with specific roles"""
    __tablename__ = "game_players"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    is_ready = Column(Boolean, default=False)  # Player ready signal
    joined_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    game = relationship("Game")


# =============================================================================
# CPX-OPORD: OPORD/FRAGO Persistence Models
# =============================================================================

class Opord(Base):
    """OPORD (Operations Order) - Versioned"""
    __tablename__ = "opords"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"))
    version = Column(Integer, default=1)
    status = Column(String, default="draft")  # draft, issued, superseded, archived

    # SMESC sections as JSON
    situation = Column(JSON)  # Situation data
    mission = Column(JSON)   # Mission data
    execution = Column(JSON) # Execution data
    coordination = Column(JSON) # Coordination data
    service_support = Column(JSON) # Service support data
    command_signal = Column(JSON) # Command and signal data

    # Metadata
    issued_by = Column(String, nullable=True)  # Username
    issued_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Chain
    superseded_by_id = Column(Integer, ForeignKey("opords.id"), nullable=True)
    previous_version_id = Column(Integer, ForeignKey("opords.id"), nullable=True)

    game = relationship("Game")
    supersedes = relationship("Opord", remote_side=[id], foreign_keys=[superseded_by_id])
    previous_version = relationship("Opord", remote_side=[id], foreign_keys=[previous_version_id])
    fragos = relationship("Frago", back_populates="opord")


class Frago(Base):
    """FRAGO (Fragmentary Order) - Quick changes to OPORD"""
    __tablename__ = "fragos"

    id = Column(Integer, primary_key=True, index=True)
    opord_id = Column(Integer, ForeignKey("opords.id"))
    game_id = Column(Integer, ForeignKey("games.id"))
    version = Column(Integer, default=1)
    frago_number = Column(String, nullable=False)  # e.g., "FRAGO-001"
    status = Column(String, default="draft")  # draft, issued, superseded, archived

    # Change data (partial update)
    changes = Column(JSON)  # Dict of changed fields
    summary = Column(Text, nullable=True)  # Brief summary of changes

    # Metadata
    issued_by = Column(String, nullable=True)
    issued_at = Column(DateTime, nullable=True)
    effective_time = Column(String, nullable=True)  # When changes take effect
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Chain
    superseded_by_id = Column(Integer, ForeignKey("fragos.id"), nullable=True)

    game = relationship("Game")
    opord = relationship("Opord", back_populates="fragos")
    supersedes = relationship("Frago", remote_side=[id], foreign_keys=[superseded_by_id])


class FragoLink(Base):
    """Links FRAGOs in a chain"""
    __tablename__ = "frago_links"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"))
    chain_name = Column(String, nullable=False)  # e.g., "alpha-company"
    order_index = Column(Integer, nullable=False)  # 0 = original OPORD, 1 = FRAGO-001, etc.

    opord_id = Column(Integer, ForeignKey("opords.id"), nullable=True)
    frago_id = Column(Integer, ForeignKey("fragos.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    game = relationship("Game")
    opord = relationship("Opord")
    frago = relationship("Frago")


# =============================================================================
# CPX-CM: Control Measures (PL/Boundary/Airspace) Models
# =============================================================================

class ControlMeasureType(enum.Enum):
    PHASE_LINE = "phase_line"
    BOUNDARY = "boundary"
    AIRSPACE = "airspace"


class ControlMeasure(Base):
    """Generic control measure (Phase Line, Boundary, Airspace)"""
    __tablename__ = "control_measures"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"))

    # Control measure type
    measure_type = Column(String, nullable=False)  # phase_line, boundary, airspace

    # Identification
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    # Geometry - stored as JSON list of [x, y] coordinates
    points = Column(JSON, nullable=False)  # [[x1, y1], [x2, y2], ...]

    # Styling
    color = Column(String, default="#ff0000")
    line_style = Column(String, default="solid")  # solid, dashed, dotted

    # Type-specific data
    owning_side = Column(String, nullable=True)  # For boundary: player, enemy, neutral
    airspace_type = Column(String, nullable=True)  # For airspace: air_corridor, restricted, ada_zone, no_fly
    altitude_low = Column(Integer, nullable=True)  # For airspace (feet)
    altitude_high = Column(Integer, nullable=True)  # For airspace (feet)
    status = Column(String, default="active")  # For phase_line: reported, contact, lost

    # Metadata
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    game = relationship("Game")


# =============================================================================
# CPX-ATO/ACO: Air Mission (ATO) and Air Control (ACO) Models
# =============================================================================

class AirMissionType(enum.Enum):
    CAS = "cas"      # Close Air Support
    BAI = "bai"      # Battlefield Air Interdiction
    SEAD = "sead"    # Suppression of Enemy Air Defense
    ISR = "isr"      # Intelligence, Surveillance, Reconnaissance
    AIRLIFT = "airlift"
    RECON = "recon"


class AirMissionStatus(enum.Enum):
    PLANNED = "planned"
    BRIEFED = "briefed"
    SORTIED = "sortied"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class AirMission(Base):
    """Air Mission (ATO entry)"""
    __tablename__ = "air_missions"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"))

    # Mission identification
    mission_number = Column(String, nullable=False)  # e.g., "CAS-01"
    mission_type = Column(String, nullable=False)  # cas, bai, sead, isr, airlift

    # Timing
    scheduled_turn = Column(Integer, nullable=False)
    tot = Column(String, nullable=True)  # Time on Target (e.g., "0800")

    # Package composition
    aircraft_type = Column(String, nullable=True)  # e.g., "F-16", "A-10"
    aircraft_count = Column(Integer, default=1)

    # Target
    target_x = Column(Float, nullable=True)
    target_y = Column(Float, nullable=True)
    target_description = Column(String, nullable=True)

    # Status
    status = Column(String, default="planned")  # planned, briefed, sortied, completed, cancelled, failed

    # Results (filled after execution)
    results = Column(JSON, nullable=True)

    # Metadata
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    game = relationship("Game")


class AirCorridor(Base):
    """Air Corridor for ACO (Air Control Order)"""
    __tablename__ = "air_corridors"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"))

    # Corridor identification
    name = Column(String, nullable=False)  # e.g., "CORRIDOR RED"
    corridor_type = Column(String, default="transit")  # transit, approach, departure

    # Geometry - center line
    waypoints = Column(JSON, nullable=False)  # List of [x, y] points

    # Altitude constraints
    altitude_min = Column(Integer, nullable=True)  # feet AGL
    altitude_max = Column(Integer, nullable=True)  # feet AGL

    # Status
    status = Column(String, default="active")  # active, suspended, closed

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    game = relationship("Game")


# =============================================================================
# CPX-SYNC: Synchronization Matrix Model
# =============================================================================

class SyncMatrix(Base):
    """Sync Matrix for time x effect synchronization planning"""
    __tablename__ = "sync_matrices"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)

    # Matrix configuration
    name = Column(String, nullable=False, default="Default Sync Matrix")
    description = Column(String, nullable=True)

    # Timeline configuration (phases)
    phases = Column(JSON, nullable=False, default=list)  # List of phase names
    # Effect categories
    effects = Column(JSON, nullable=False, default=list)  # List of effect types
    # Resolution (time units)
    resolution = Column(String, default="turn")  # turn, hour, day

    # Matrix data: 2D array of entries
    # Each entry: {phase, effect, value, notes, linked_items}
    matrix_data = Column(JSON, nullable=False, default=dict)

    # Status
    status = Column(String, default="draft")  # draft, active, archived

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String, nullable=True)

    game = relationship("Game")


class SyncMatrixEntry(Base):
    """Individual entry in sync matrix"""
    __tablename__ = "sync_matrix_entries"

    id = Column(Integer, primary_key=True, index=True)
    sync_matrix_id = Column(Integer, ForeignKey("sync_matrices.id"), nullable=False)

    # Entry identification
    phase = Column(String, nullable=False)
    effect = Column(String, nullable=False)

    # Entry data
    value = Column(String, nullable=True)  # intensity, priority, status
    notes = Column(Text, nullable=True)
    start_time = Column(String, nullable=True)  # Turn/hour/day
    end_time = Column(String, nullable=True)
    linked_opord_id = Column(Integer, ForeignKey("opords.id"), nullable=True)
    linked_ato_mission_id = Column(Integer, nullable=True)
    linked_inject_id = Column(String, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    sync_matrix = relationship("SyncMatrix")


# =============================================================================
# CPX-CHAT: Chat/EXCON Channel Models
# =============================================================================

class ChatMessage(Base):
    """Chat message for role-based channels"""
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)

    # Sender information
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    username = Column(String, nullable=False)  # Denormalized for display

    # Message content
    content = Column(Text, nullable=False)

    # Channel targeting (role-based visibility)
    # "all" - visible to everyone
    # "blue" - only blue side
    # "red" - only red side
    # "white" - only white/umpire
    # "observer" - only observers
    channel = Column(String, default="all")

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)

    # Read tracking (JSON: {user_id: timestamp})
    read_by = Column(JSON, default={})

    # Metadata
    turn = Column(Integer, nullable=True)  # Current turn when sent

    game = relationship("Game")
    user = relationship("User")
