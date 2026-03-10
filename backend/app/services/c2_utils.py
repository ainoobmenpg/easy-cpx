# C2 Utilities - Multi-national Unit Management
# Helper functions for faction, echelon, and callsign management

import random
from typing import Optional


# NATO Faction Codes
FACTION_CODES = {
    "US": "United States",
    "UK": "United Kingdom",
    "GER": "Germany",
    "FR": "France",
    "NL": "Netherlands",
    "BEL": "Belgium",
    "CAN": "Canada",
    "POL": "Poland",
    "OPFOR": "Opposing Force",
    "RED": "Red Force",
    "BLUE": "Blue Force",
}

# Echelon Codes (Military Hierarchy)
ECHELON_CODES = {
    "squad": "Squad",
    "platoon": "Platoon",
    "company": "Company",
    "battalion": "Battalion",
    "regiment": "Regiment",
    "brigade": "Brigade",
    "division": "Division",
    "corps": "Corps",
    "army": "Army",
}

# Callsign Generators
CALLSIGN_PREFIXES = [
    "ALPHA", "BRAVO", "CHARLIE", "DELTA", "ECHO", "FOXTROT",
    "GOLF", "HOTEL", "INDIA", "JULIET", "KILO", "LIMA",
    "MIKE", "NOVEMBER", "OSCAR", "PAPA", "QUEBEC", "ROMEO",
    "SIERRA", "TANGO", "UNIFORM", "VICTOR", "WHISKEY", "XRAY",
    "YANKEE", "ZULU",
]

CALLSIGN_NUMBERS = [
    "1", "2", "3", "4", "5", "6", "7", "8", "9", "0",
    "1-1", "1-2", "1-3", "2-1", "2-2", "2-3",
    "3-1", "3-2", "3-3", "4-1", "4-2",
]


def get_faction_name(code: str) -> str:
    """Get faction name from code"""
    return FACTION_CODES.get(code.upper(), code)


def get_echelon_name(code: str) -> str:
    """Get echelon name from code"""
    return ECHELON_CODES.get(code.lower(), code)


def generate_callsign(unit_index: int = 0, use_prefix: bool = True) -> str:
    """
    Generate a unique callsign for a unit.

    Args:
        unit_index: Unit index for deterministic generation
        use_prefix: Use NATO phonetics (True) or numbers (False)

    Returns:
        Callsign string (e.g., "ALPHA-1" or "1-1")
    """
    if use_prefix:
        prefix = CALLSIGN_PREFIXES[unit_index % len(CALLSIGN_PREFIXES)]
        number = CALLSIGN_NUMBERS[unit_index // len(CALLSIGN_PREFIXES)]
        return f"{prefix}-{number}"
    else:
        return CALLSIGN_NUMBERS[unit_index % len(CALLSIGN_NUMBERS)]


def generate_unit_c2_data(
    faction: Optional[str] = None,
    echelon: Optional[str] = None,
    callsign: Optional[str] = None,
    unit_index: int = 0
) -> dict:
    """
    Generate complete C2 data for a unit.

    Args:
        faction: Specific faction code
        echelon: Specific echelon
        callsign: Specific callsign
        unit_index: Index for generating defaults

    Returns:
        Dict with faction, echelon, callsign
    """
    return {
        "faction": faction or "BLUE",
        "echelon": echelon or "company",
        "callsign": callsign or generate_callsign(unit_index),
    }


def get_callsign_color(callsign_prefix: str) -> str:
    """Get color for callsign prefix (for UI display)"""
    colors = {
        "ALPHA": "#3b82f6",   # Blue
        "BRAVO": "#ef4444",    # Red
        "CHARLIE": "#22c55e",  # Green
        "DELTA": "#f59e0b",    # Amber
        "ECHO": "#8b5cf6",     # Purple
        "FOXTROT": "#06b6d4",  # Cyan
        "GOLF": "#ec4899",     # Pink
        "HOTEL": "#84cc16",    # Lime
    }
    return colors.get(callsign_prefix.upper(), "#6b7280")


def format_unit_c2_display(faction: str, echelon: str, callsign: str) -> str:
    """
    Format C2 data for display.

    Args:
        faction: Faction code
        echelon: Echelon level
        callsign: Radio callsign

    Returns:
        Formatted string (e.g., "US/Company/ALPHA-1")
    """
    return f"{faction}/{echelon}/{callsign}"
