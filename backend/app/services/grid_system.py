# Grid System Service - MGRS/APP-6 Coordinate Utilities
# Provides conversion between internal XY coordinates and MGRS grid references
# Also manages control measures (phase lines, boundaries, airspace)

from dataclasses import dataclass
from typing import Optional
from enum import Enum


class GridSystemType(Enum):
    XY = "XY"
    MGRS = "MGRS"


# MGRS Grid Zone Descriptor (GZD) - UTM zones
MGRS_GZD = {
    # Northern hemisphere examples
    "31T": {"zone": 31, "letter": "T"},
    "32T": {"zone": 32, "letter": "T"},
    "33T": {"zone": 33, "letter": "T"},
    "34T": {"zone": 34, "letter": "T"},
    "35T": {"zone": 35, "letter": "T"},
    "36T": {"zone": 36, "letter": "T"},
    "37T": {"zone": 37, "letter": "T"},
    "38T": {"zone": 38, "letter": "T"},
    "31S": {"zone": 31, "letter": "S"},
    "32S": {"zone": 32, "letter": "S"},
    "33S": {"zone": 33, "letter": "S"},
    "34S": {"zone": 34, "letter": "S"},
    "35S": {"zone": 35, "letter": "S"},
    "36S": {"zone": 36, "letter": "S"},
    "37S": {"zone": 37, "letter": "S"},
    "38S": {"zone": 38, "letter": "S"},
}

# Default GZD for operational scenarios (Central Europe)
DEFAULT_GZD = "34S"


@dataclass
class MGRSPrecision:
    """MGRS precision levels"""
    METERS_1: str = "1m"
    METERS_10: str = "10m"
    METERS_100: str = "100m"
    KILOMETER_1: str = "1km"
    KILOMETER_10: str = "10km"
    KILOMETER_100: str = "100km"


class GridSystemService:
    """
    Service for managing grid coordinates (XY <-> MGRS conversion)
    and control measures (phase lines, boundaries, airspace).
    """

    def __init__(
        self,
        map_width: int = 50,
        map_height: int = 50,
        gzd: str = DEFAULT_GZD,
        origin_lat: float = 52.0,  # Default: Central Europe
        origin_lon: float = 10.0,
        meters_per_cell: int = 1000  # 1km per cell
    ):
        self.map_width = map_width
        self.map_height = map_height
        self.gzd = gzd
        self.origin_lat = origin_lat
        self.origin_lon = origin_lon
        self.meters_per_cell = meters_per_cell

    def xy_to_mgrs(self, x: int, y: int, precision: str = "1km") -> str:
        """
        Convert internal XY coordinates to MGRS grid reference.

        Args:
            x: X coordinate (0 = west)
            y: Y coordinate (0 = south)
            precision: Precision level ("1m", "10m", "100m", "1km", "10km", "100km")

        Returns:
            MGRS grid reference string (e.g., "34S 12345 67890")
        """
        # Calculate real-world coordinates
        easting = x * self.meters_per_cell + 500  # Add offset for false easting
        northing = y * self.meters_per_cell + 500  # Add offset for false northing

        # Determine precision components
        precision_map = {
            "100km": (2, ""),
            "10km": (3, ""),
            "1km": (5, ""),
            "100m": (7, ""),
            "10m": (8, ""),
            "1m": (10, ""),
        }
        digits, _ = precision_map.get(precision, (5, ""))

        # Format MGRS string
        easting_str = str(easting).zfill(digits)[:digits]
        northing_str = str(northing).zfill(digits)[:digits]

        # 100km grid square (simplified - would need full UTM conversion for accuracy)
        grid_square = self._get_grid_square(x, y)

        if digits <= 2:
            return f"{self.gzd} {grid_square}"
        elif digits <= 3:
            return f"{self.gzd} {grid_square} {easting_str[:1]}{northing_str[:1]}"
        elif digits <= 5:
            return f"{self.gzd} {grid_square} {easting_str[:3]} {northing_str[:3]}"
        else:
            return f"{self.gzd} {grid_square} {easting_str} {northing_str}"

    def mgrs_to_xy(self, mgrs_ref: str) -> Optional[tuple[int, int]]:
        """
        Convert MGRS grid reference to internal XY coordinates.

        Args:
            mgrs_ref: MGRS grid reference (e.g., "34S 123 456")

        Returns:
            Tuple of (x, y) coordinates, or None if invalid
        """
        parts = mgrs_ref.strip().split()

        if len(parts) < 2:
            return None

        # Parse GZD
        gzd = parts[0]
        if gzd not in MGRS_GZD:
            return None

        # Parse grid square and coordinates
        if len(parts) == 2:
            # Just 100km square
            return None  # Need more precision

        grid_square = parts[1]
        coord_part = parts[2] if len(parts) > 2 else ""

        # Determine precision
        if len(coord_part) <= 1:
            # 10km precision
            x = int(coord_part) * 10
            y = 0
        elif len(coord_part) <= 3:
            # 1km precision
            x = int(coord_part.ljust(3, '0'))
            y = int(coord_part.ljust(3, '0'))
        else:
            # Higher precision
            half = len(coord_part) // 2
            easting = int(coord_part[:half].lstrip('0') or '0')
            northing = int(coord_part[half:].lstrip('0') or '0')
            x = easting // self.meters_per_cell
            y = northing // self.meters_per_cell

        # Clamp to map bounds
        x = max(0, min(self.map_width - 1, x))
        y = max(0, min(self.map_height - 1, y))

        return (x, y)

    def _get_grid_square(self, x: int, y: int) -> str:
        """
        Get 100km grid square letter pair.
        Simplified implementation - would need full UTM conversion.
        """
        # Simplified: Use letter offset based on position
        letters = "ABCDEFGHJKLMNPQRSTUVWXYZ"
        col = x // 10 % 20
        row = y // 10 % 20

        if col < 20 and row < 20:
            return f"{letters[col]}{letters[row]}"
        return "XX"

    def get_grid_reference(self, x: int, y: int, include_coordinates: bool = True) -> dict:
        """
        Get complete grid reference for a position.

        Args:
            x: X coordinate
            y: Y coordinate
            include_coordinates: Include numeric coordinates

        Returns:
            Dict with MGRS string and components
        """
        mgrs_100km = self.xy_to_mgrs(x, y, "100km")
        mgrs_1km = self.xy_to_mgrs(x, y, "1km")

        result = {
            "grid_reference": mgrs_1km,
            "gzd": self.gzd,
            "grid_square": self._get_grid_square(x, y),
        }

        if include_coordinates:
            result["easting"] = x * self.meters_per_cell + 500
            result["northing"] = y * self.meters_per_cell + 500
            result["x"] = x
            result["y"] = y

        return result


# Control Measures Classes

@dataclass
class PhaseLineData:
    """Phase Line control measure"""
    id: str
    name: str
    points: list[tuple[int, int]]  # List of (x, y) coordinates
    color: str = "#ff0000"
    line_style: str = "solid"  # solid, dashed, dotted
    status: str = "reported"   # reported, contact, lost


@dataclass
class BoundaryData:
    """Boundary control measure"""
    id: str
    name: str
    owning_side: str  # player, enemy, neutral
    points: list[tuple[int, int]]
    color: str = "#0000ff"
    line_style: str = "solid"


@dataclass
class AirspaceData:
    """Airspace control measure"""
    id: str
    name: str
    type: str  # air_corridor, restricted, ada_zone, no_fly
    points: list[tuple[int, int]]
    altitude_low: Optional[int] = None
    altitude_high: Optional[int] = None
    color: str = "#ffff00"
    status: str = "active"


class ControlMeasuresService:
    """Service for managing control measures"""

    def __init__(self):
        self.phase_lines: dict[str, PhaseLineData] = {}
        self.boundaries: dict[str, BoundaryData] = {}
        self.airspaces: dict[str, AirspaceData] = {}

    def add_phase_line(
        self,
        id: str,
        name: str,
        points: list[tuple[int, int]],
        color: str = "#ff0000",
        line_style: str = "solid",
        status: str = "reported"
    ) -> PhaseLineData:
        """Add a phase line"""
        phase_line = PhaseLineData(
            id=id,
            name=name,
            points=points,
            color=color,
            line_style=line_style,
            status=status
        )
        self.phase_lines[id] = phase_line
        return phase_line

    def add_boundary(
        self,
        id: str,
        name: str,
        owning_side: str,
        points: list[tuple[int, int]],
        color: str = "#0000ff",
        line_style: str = "solid"
    ) -> BoundaryData:
        """Add a boundary"""
        boundary = BoundaryData(
            id=id,
            name=name,
            owning_side=owning_side,
            points=points,
            color=color,
            line_style=line_style
        )
        self.boundaries[id] = boundary
        return boundary

    def add_airspace(
        self,
        id: str,
        name: str,
        type: str,
        points: list[tuple[int, int]],
        altitude_low: Optional[int] = None,
        altitude_high: Optional[int] = None,
        color: str = "#ffff00",
        status: str = "active"
    ) -> AirspaceData:
        """Add an airspace"""
        airspace = AirspaceData(
            id=id,
            name=name,
            type=type,
            points=points,
            altitude_low=altitude_low,
            altitude_high=altitude_high,
            color=color,
            status=status
        )
        self.airspaces[id] = airspace
        return airspace

    def get_all_control_measures(self) -> dict:
        """Get all control measures for serialization"""
        return {
            "phase_lines": [
                {
                    "id": pl.id,
                    "name": pl.name,
                    "points": [{"x": p[0], "y": p[1]} for p in pl.points],
                    "color": pl.color,
                    "line_style": pl.line_style,
                    "status": pl.status
                }
                for pl in self.phase_lines.values()
            ],
            "boundaries": [
                {
                    "id": b.id,
                    "name": b.name,
                    "owning_side": b.owning_side,
                    "points": [{"x": p[0], "y": p[1]} for p in b.points],
                    "color": b.color,
                    "line_style": b.line_style
                }
                for b in self.boundaries.values()
            ],
            "airspaces": [
                {
                    "id": a.id,
                    "name": a.name,
                    "type": a.type,
                    "points": [{"x": p[0], "y": p[1]} for p in a.points],
                    "altitude_low": a.altitude_low,
                    "altitude_high": a.altitude_high,
                    "color": a.color,
                    "status": a.status
                }
                for a in self.airspaces.values()
            ]
        }

    def clear_all(self):
        """Clear all control measures"""
        self.phase_lines.clear()
        self.boundaries.clear()
        self.airspaces.clear()


# APP-6 Symbol Utilities

class APP6SymbolService:
    """
    Service for APP-6 symbol generation and configuration.
    Maps unit types to APP-6 symbol codes.
    """

    # APP-6 symbol codes for ground units
    SYMBOL_CODES = {
        # Infantry
        "infantry": "S-",
        # Armor/Mechanized
        "armor": "G-",
        # Artillery
        "artillery": "F-",
        # Air Defense
        "air_defense": "A-",
        # Reconnaissance
        "recon": "R-",
        # UAV
        "uav": "Z-",
        # Supply/Support
        "support": "S--P",
        # Headquarters
        "hq": "E-",
        # Anti-Tank
        "atgm": "S--AT",
    }

    # Affiliation mappings
    AFFILIATION_MAP = {
        "player": "friend",
        "enemy": "enemy",
        "neutral": "neutral",
    }

    # Status mappings
    STATUS_MAP = {
        "intact": "present",
        "light_damage": "present",
        "medium_damage": "present",
        "heavy_damage": "anticipated",
        "destroyed": "reimbursed",
    }

    # Echelon codes
    ECHELON_CODES = {
        "platoon": "P",
        "company": "C",
        "battalion": "B",
        "regiment": "R",
        "division": "D",
    }

    def get_symbol_code(self, unit_type: str) -> str:
        """Get APP-6 symbol code for unit type"""
        return self.SYMBOL_CODES.get(unit_type, "S-")

    def get_affiliation(self, side: str) -> str:
        """Get affiliation from unit side"""
        return self.AFFILIATION_MAP.get(side, "unknown")

    def get_status(self, unit_status: str) -> str:
        """Get APP-6 status from unit status"""
        return self.STATUS_MAP.get(unit_status, "present")

    def get_symbol_config(
        self,
        unit_type: str,
        side: str,
        status: str = "intact",
        echelon: str = "company",
        modifier: str = ""
    ) -> dict:
        """
        Get complete APP-6 symbol configuration for a unit.

        Args:
            unit_type: Unit type (infantry, armor, etc.)
            side: Unit side (player, enemy, neutral)
            status: Unit status (intact, light_damage, etc.)
            echelon: Unit echelon (platoon, company, battalion, etc.)
            modifier: Additional modifiers (task force, reinforced, etc.)

        Returns:
            Dict with APP-6 symbol configuration
        """
        return {
            "symbol": self.get_symbol_code(unit_type),
            "affiliation": self.AFFILIATION_MAP.get(side, "unknown"),
            "status": self.STATUS_MAP.get(status, "present"),
            "echelon": self.ECHELON_CODES.get(echelon, "C"),
            "modifier": modifier,
        }

    def get_color_for_affiliation(self, affiliation: str) -> str:
        """Get standard APP-6 color for affiliation"""
        colors = {
            "friend": "#3b82f6",  # Blue
            "enemy": "#ef4444",    # Red
            "neutral": "#22c55e",  # Green
            "unknown": "#a855f7",  # Purple
        }
        return colors.get(affiliation, "#ffffff")
