# Unit Behavior Profiles for Operational CPX
# Defines how different unit types should behave in combat

from typing import Optional
from enum import Enum


class UnitBehaviorProfile:
    """Defines how a unit type should behave"""

    def __init__(
        self,
        preferred_range: int = 2,
        min_range: int = 0,
        max_range: int = 5,
        should_advance: bool = True,
        stay_at_range: bool = False,
        stay_rear: bool = False,
        avoid_combat: bool = False,
        recon_only: bool = False,
        target_air: bool = False,
        max_advance_when_low_ammo: bool = False,
    ):
        self.preferred_range = preferred_range
        self.min_range = min_range
        self.max_range = max_range
        self.should_advance = should_advance
        self.stay_at_range = stay_at_range  # Maintain distance from enemy
        self.stay_rear = stay_rear  # Stay behind front lines
        self.avoid_combat = avoid_combat  # Avoid direct combat
        self.recon_only = recon_only  # Only for reconnaissance
        self.target_air = target_air  # Prioritize air targets
        self.max_advance_when_low_ammo = max_advance_when_low_ammo


# Complete unit behavior profiles
UNIT_BEHAVIOR_PROFILES: dict[str, UnitBehaviorProfile] = {
    # Armor - Main battle tanks
    "armor": UnitBehaviorProfile(
        preferred_range=2,
        min_range=0,
        max_range=5,
        should_advance=True,
        max_advance_when_low_ammo=True,
    ),
    # Standard infantry
    "infantry": UnitBehaviorProfile(
        preferred_range=1,
        min_range=0,
        max_range=3,
        should_advance=True,
    ),
    # ATGM - Anti-tank missile infantry
    "atgm": UnitBehaviorProfile(
        preferred_range=4,
        min_range=2,
        max_range=8,
        should_advance=False,
        stay_at_range=True,
    ),
    # Sniper infantry
    "sniper": UnitBehaviorProfile(
        preferred_range=3,
        min_range=1,
        max_range=6,
        should_advance=False,
        stay_at_range=True,
    ),
    # Scout infantry
    "scout": UnitBehaviorProfile(
        preferred_range=2,
        min_range=0,
        max_range=5,
        should_advance=True,
    ),
    # Artillery
    "artillery": UnitBehaviorProfile(
        preferred_range=10,
        min_range=5,
        max_range=20,
        should_advance=False,
        stay_rear=True,
    ),
    # Air Defense
    "air_defense": UnitBehaviorProfile(
        preferred_range=8,
        min_range=2,
        max_range=15,
        should_advance=False,
        target_air=True,
    ),
    # Attack Helicopter
    "attack_helo": UnitBehaviorProfile(
        preferred_range=3,
        min_range=1,
        max_range=8,
        should_advance=True,
    ),
    # Transport Helicopter
    "transport_helo": UnitBehaviorProfile(
        preferred_range=5,
        min_range=0,
        max_range=10,
        should_advance=False,
        avoid_combat=True,
    ),
    # Aircraft
    "aircraft": UnitBehaviorProfile(
        preferred_range=5,
        min_range=0,
        max_range=15,
        should_advance=True,
        avoid_combat=False,
    ),
    # UAV - reconnaissance only
    "uav": UnitBehaviorProfile(
        preferred_range=15,
        min_range=5,
        max_range=25,
        should_advance=False,
        avoid_combat=True,
        recon_only=True,
    ),
    # Recon units
    "recon": UnitBehaviorProfile(
        preferred_range=5,
        min_range=0,
        max_range=10,
        should_advance=True,
        avoid_combat=True,
    ),
    # Support units
    "support": UnitBehaviorProfile(
        preferred_range=3,
        min_range=0,
        max_range=5,
        should_advance=False,
        stay_rear=True,
        avoid_combat=True,
    ),
    # Default fallback
    "default": UnitBehaviorProfile(
        preferred_range=2,
        min_range=0,
        max_range=5,
        should_advance=True,
    ),
}


def get_unit_profile(unit_type: str) -> UnitBehaviorProfile:
    """Get behavior profile for a unit type"""
    unit_type_lower = unit_type.lower()

    # Try exact match first
    if unit_type_lower in UNIT_BEHAVIOR_PROFILES:
        return UNIT_BEHAVIOR_PROFILES[unit_type_lower]

    # Try partial matches
    for profile_type, profile in UNIT_BEHAVIOR_PROFILES.items():
        if profile_type in unit_type_lower:
            return profile

    return UNIT_BEHAVIOR_PROFILES["default"]


# Rock-Paper-Scissors Combat Compatibility Matrix
# Values represent bonus (positive) or penalty (negative) to attack effectiveness
# Format: ATTACKER vs DEFENDER
UNIT_COMPATIBILITY_MATRIX: dict[str, dict[str, float]] = {
    # Armor attacks
    "armor": {
        "armor": 0.0,      # Tank vs Tank - even match
        "infantry": 0.3,   # Tank crushes infantry
        "artillery": -0.2, # Tank vulnerable to artillery
        "air_defense": -0.3,
        "aircraft": 0.0,
        "helo": 0.0,
        "uav": 0.0,
        "recon": 0.1,
        "support": 0.2,
    },
    # Standard infantry attacks
    "infantry": {
        "armor": -0.3,     # Infantry vulnerable to tanks
        "infantry": 0.0,   # Even match
        "artillery": -0.2,
        "air_defense": 0.0,
        "aircraft": 0.0,
        "helo": 0.0,
        "uav": 0.0,
        "recon": 0.0,
        "support": 0.1,
    },
    # ATGM infantry attacks
    "atgm": {
        "armor": 0.4,      # ATGM very effective vs armor
        "infantry": -0.1,  # Less effective vs infantry
        "artillery": -0.1,
        "air_defense": 0.0,
        "aircraft": 0.0,
        "helo": 0.1,
        "uav": 0.0,
        "recon": 0.0,
        "support": 0.0,
    },
    # Sniper attacks
    "sniper": {
        "armor": -0.3,
        "infantry": 0.3,   # Snipers effective vs infantry
        "artillery": 0.0,
        "air_defense": 0.0,
        "aircraft": 0.0,
        "helo": 0.1,
        "uav": 0.0,
        "recon": 0.2,
        "support": 0.1,
    },
    # Scout attacks
    "scout": {
        "armor": -0.2,
        "infantry": 0.1,
        "artillery": 0.0,
        "air_defense": 0.0,
        "aircraft": 0.0,
        "helo": 0.0,
        "uav": 0.0,
        "recon": 0.1,
        "support": 0.0,
    },
    # Artillery attacks
    "artillery": {
        "armor": -0.1,
        "infantry": 0.2,   # Artillery effective vs infantry
        "artillery": 0.0,
        "air_defense": -0.2,
        "aircraft": -0.1,
        "helo": 0.1,
        "uav": 0.2,        # Can target UAVs
        "recon": 0.1,
        "support": 0.1,
    },
    # Air Defense attacks
    "air_defense": {
        "armor": 0.0,
        "infantry": 0.0,
        "artillery": -0.1,
        "air_defense": 0.0,
        "aircraft": 0.4,   # Very effective vs aircraft
        "helo": 0.4,       # Very effective vs helicopters
        "uav": 0.3,        # Can target UAVs
        "recon": 0.0,
        "support": 0.0,
    },
    # Attack Helicopter attacks
    "attack_helo": {
        "armor": 0.3,      # Hellfire effective vs tanks
        "infantry": 0.3,   # Also effective vs infantry
        "artillery": 0.1,
        "air_defense": -0.2,
        "aircraft": 0.0,
        "helo": 0.0,
        "uav": 0.1,
        "recon": 0.2,
        "support": 0.2,
    },
    # Aircraft attacks
    "aircraft": {
        "armor": 0.3,      # Air-to-ground effective
        "infantry": 0.3,
        "artillery": 0.3,
        "air_defense": 0.2,
        "aircraft": 0.0,   # Dogfight - even
        "helo": 0.2,
        "uav": 0.2,
        "recon": 0.2,
        "support": 0.2,
    },
    # UAV attacks (limited)
    "uav": {
        "armor": 0.1,
        "infantry": 0.1,
        "artillery": 0.1,
        "air_defense": 0.0,
        "aircraft": 0.0,
        "helo": 0.0,
        "uav": 0.0,
        "recon": 0.0,
        "support": 0.1,
    },
    # Recon attacks
    "recon": {
        "armor": -0.2,
        "infantry": 0.0,
        "artillery": 0.0,
        "air_defense": 0.0,
        "aircraft": 0.0,
        "helo": 0.0,
        "uav": 0.0,
        "recon": 0.0,
        "support": 0.0,
    },
    # Support attacks
    "support": {
        "armor": -0.3,
        "infantry": -0.1,
        "artillery": -0.1,
        "air_defense": -0.1,
        "aircraft": 0.0,
        "helo": 0.0,
        "uav": 0.0,
        "recon": 0.0,
        "support": 0.0,
    },
}


def get_compatibility_bonus(attacker_type: str, defender_type: str) -> float:
    """Get combat bonus/penalty based on unit type matchup"""
    attacker = attacker_type.lower()
    defender = defender_type.lower()

    # Normalize types
    attacker = _normalize_unit_type(attacker)
    defender = _normalize_unit_type(defender)

    # Get attacker row
    if attacker not in UNIT_COMPATIBILITY_MATRIX:
        return 0.0

    attacker_row = UNIT_COMPATIBILITY_MATRIX[attacker]

    # Get defender column
    if defender in attacker_row:
        return attacker_row[defender]

    # Try partial match
    for def_type, bonus in attacker_row.items():
        if def_type in defender or defender in def_type:
            return bonus

    return 0.0


def _normalize_unit_type(unit_type: str) -> str:
    """Normalize unit type for compatibility lookup"""
    unit_type = unit_type.lower()

    if "tank" in unit_type or "armor" in unit_type or "m1" in unit_type or "leopard" in unit_type or "t72" in unit_type or "t80" in unit_type or "bradley" in unit_type or "bmp" in unit_type or "marder" in unit_type:
        return "armor"

    if "atgm" in unit_type or "anti-tank" in unit_type:
        return "atgm"

    if "sniper" in unit_type:
        return "sniper"

    if "scout" in unit_type:
        return "scout"

    if "infantry" in unit_type or "inf" in unit_type:
        return "infantry"

    if "artillery" in unit_type or "howitzer" in unit_type or "mlrs" in unit_type or "grad" in unit_type or "m109" in unit_type or "pzh" in unit_type:
        return "artillery"

    if "air_defense" in unit_type or "sam" in unit_type or "patriot" in unit_type or "flak" in unit_type or "gepard" in unit_type or "stinger" in unit_type or "sa6" in unit_type or "sa11" in unit_type:
        return "air_defense"

    if "attack" in unit_type and "helo" in unit_type or "apache" in unit_type or "hind" in unit_type:
        return "attack_helo"

    if "transport" in unit_type and "helo" in unit_type or "blackhawk" in unit_type or "mi17" in unit_type or "hip" in unit_type:
        return "transport_helo"

    if "aircraft" in unit_type or "fighter" in unit_type or "f15" in unit_type or "f16" in unit_type or "mig" in unit_type or "tornado" in unit_type or "su25" in unit_type:
        return "aircraft"

    if "uav" in unit_type or "drone" in unit_type or "reaper" in unit_type or "shadow" in unit_type or "forpost" in unit_type:
        return "uav"

    if "recon" in unit_type:
        return "recon"

    if "support" in unit_type or "supply" in unit_type:
        return "support"

    return "default"
