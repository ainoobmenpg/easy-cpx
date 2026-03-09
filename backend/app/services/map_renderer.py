# Text Map Renderer for Operational CPX
# Generates ASCII-based tactical maps from game state
from typing import Optional
from enum import Enum


class TerrainType(Enum):
    PLAIN = "plain"
    URBAN = "urban"
    HIGH_GROUND = "high_ground"
    FOREST = "forest"
    WATER = "water"
    MOUNTAIN = "mountain"


class UnitSymbol(Enum):
    FRIENDLY = "[F]"
    ENEMY_CONFIRMED = "[E]"
    ENEMY_UNKNOWN = "[?]"
    HEADQUARTERS = "★"
    RECON = "[R]"
    SUPPLY = "[S]"


# Terrain symbol mapping
TERRAIN_SYMBOLS = {
    TerrainType.PLAIN: ".",
    TerrainType.URBAN: "█",
    TerrainType.HIGH_GROUND: "▲",
    TerrainType.FOREST: "▓",
    TerrainType.WATER: "≈",
    TerrainType.MOUNTAIN: "△"
}

# Terrain movement cost multipliers
TERRAIN_COSTS = {
    TerrainType.PLAIN: 1.0,
    TerrainType.URBAN: 1.5,
    TerrainType.HIGH_GROUND: 1.2,
    TerrainType.FOREST: 1.3,
    TerrainType.WATER: 999,  # Impassable
    TerrainType.MOUNTAIN: 2.0
}


class MapRenderer:
    """Generates text-based tactical maps from game state"""

    def __init__(self, width: int = 50, height: int = 30):
        self.width = width
        self.height = height
        self._terrain: dict[tuple[int, int], TerrainType] = {}

    def set_terrain(self, x: int, y: int, terrain: TerrainType):
        """Set terrain at a specific coordinate"""
        if 0 <= x < self.width and 0 <= y < self.height:
            self._terrain[(x, y)] = terrain

    def generate_random_terrain(self, seed: Optional[int] = None):
        """Generate random terrain for the map"""
        import random
        if seed is not None:
            random.seed(seed)

        for y in range(self.height):
            for x in range(self.width):
                # Simple terrain generation based on position
                # Higher y = more mountains/high ground
                # Lower y = more water/plains
                rand_val = random.random()
                base_height = y / self.height

                if base_height < 0.2:
                    terrain = TerrainType.WATER if rand_val < 0.3 else TerrainType.PLAIN
                elif base_height < 0.5:
                    terrain = TerrainType.PLAIN if rand_val < 0.5 else TerrainType.FOREST
                elif base_height < 0.7:
                    terrain = TerrainType.FOREST if rand_val < 0.4 else TerrainType.URBAN
                elif base_height < 0.9:
                    terrain = TerrainType.HIGH_GROUND if rand_val < 0.5 else TerrainType.URBAN
                else:
                    terrain = TerrainType.MOUNTAIN if rand_val < 0.6 else TerrainType.HIGH_GROUND

                self._terrain[(x, y)] = terrain

    def render_map(
        self,
        units: list[dict],
        player_knowledge: Optional[dict[int, str]] = None,
        show_terrain: bool = True
    ) -> str:
        """
        Render the map as a text grid

        Args:
            units: List of unit dicts with keys: id, name, side, x, y, type
            player_knowledge: Dict mapping unit_id to confidence level ("confirmed", "estimated", "unknown")
            show_terrain: Whether to show terrain symbols

        Returns:
            Multi-line string representing the tactical map
        """
        if player_knowledge is None:
            player_knowledge = {}

        # Create empty grid
        grid = [[" " for _ in range(self.width)] for _ in range(self.height)]

        # Place terrain
        if show_terrain:
            for (x, y), terrain in self._terrain.items():
                if 0 <= x < self.width and 0 <= y < self.height:
                    grid[y][x] = TERRAIN_SYMBOLS.get(terrain, ".")

        # Place units
        for unit in units:
            x, y = int(unit.get("x", 0)), int(unit.get("y", 0))
            if 0 <= x < self.width and 0 <= y < self.height:
                side = unit.get("side", "unknown")
                unit_type = unit.get("type", "")

                # Determine symbol based on player knowledge
                unit_id = unit.get("id")
                confidence = player_knowledge.get(unit_id, "confirmed")

                if side == "player":
                    if "hq" in unit_type.lower():
                        symbol = UnitSymbol.HEADQUARTERS.value
                    elif "recon" in unit_type.lower():
                        symbol = UnitSymbol.RECON.value
                    elif "supply" in unit_type.lower():
                        symbol = UnitSymbol.SUPPLY.value
                    else:
                        symbol = UnitSymbol.FRIENDLY.value
                elif side == "enemy":
                    if confidence == "confirmed":
                        symbol = UnitSymbol.ENEMY_CONFIRMED.value
                    elif confidence == "estimated":
                        # Show as unknown with question mark
                        symbol = "[~]"
                    else:
                        symbol = UnitSymbol.ENEMY_UNKNOWN.value
                else:
                    symbol = "[?]"

                grid[y][x] = symbol

        # Convert to string
        lines = []
        # Header with coordinates
        lines.append("    " + "".join(f"{i % 10}" for i in range(self.width)))
        lines.append("    " + "-" * self.width)

        for y in range(self.height):
            row_str = "".join(grid[y])
            lines.append(f"{y:02d} |{row_str}|")

        lines.append("    " + "-" * self.width)

        return "\n".join(lines)

    def render_mini_map(
        self,
        units: list[dict],
        player_knowledge: Optional[dict[int, str]] = None
    ) -> str:
        """Render a compact mini-map for SITREP (half size)"""
        mini_width = self.width // 2
        mini_height = self.height // 2

        if player_knowledge is None:
            player_knowledge = {}

        # Create empty grid
        grid = [["." for _ in range(mini_width)] for _ in range(mini_height)]

        # Place terrain (scaled down)
        for (x, y), terrain in self._terrain.items():
            mx, my = x // 2, y // 2
            if 0 <= mx < mini_width and 0 <= my < mini_height:
                grid[my][mx] = TERRAIN_SYMBOLS.get(terrain, ".")

        # Place units (scaled down)
        for unit in units:
            x, y = int(unit.get("x", 0)) // 2, int(unit.get("y", 0)) // 2
            if 0 <= x < mini_width and 0 <= y < mini_height:
                side = unit.get("side", "unknown")
                if side == "player":
                    grid[y][x] = "F"
                elif side == "enemy":
                    unit_id = unit.get("id")
                    confidence = player_knowledge.get(unit_id, "confirmed")
                    if confidence == "confirmed":
                        grid[y][x] = "E"
                    else:
                        grid[y][x] = "?"

        # Convert to string
        return "\n".join("".join(row) for row in grid)


class FogOfWar:
    """Manages fog of war and player knowledge"""

    def __init__(self, map_width: int = 50, map_height: int = 50):
        self.width = map_width
        self.height = map_height
        self._known_areas: set[tuple[int, int]] = set()
        self._observed_enemy_positions: dict[int, tuple[int, int]] = {}

    def add_observed_area(self, x: int, y: int, radius: int = 3):
        """Mark an area as observed by player"""
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if dx * dx + dy * dy <= radius * radius:
                    self._known_areas.add((x + dx, y + dy))

    def add_observed_enemy(self, unit_id: int, x: int, y: int, confidence: str = "confirmed"):
        """Record observed enemy position"""
        self._observed_enemy_positions[unit_id] = (x, y, confidence)

    def is_known(self, x: int, y: int) -> bool:
        """Check if a position is within player knowledge"""
        return (x, y) in self._known_areas

    def get_enemy_knowledge(self) -> dict[int, str]:
        """Get player knowledge level for each enemy unit"""
        return {
            unit_id: conf
            for unit_id, (_, _, conf) in self._observed_enemy_positions.items()
        }

    def update_from_recon(self, recon_units: list[dict]):
        """Update fog of war based on recon unit positions"""
        for unit in recon_units:
            if unit.get("side") == "player":
                x, y = int(unit.get("x", 0)), int(unit.get("y", 0))
                self.add_observed_area(x, y, radius=4)
