# Terrain Effects for Operational CPX
# Implements terrain-based combat and movement modifiers
from enum import Enum
from dataclasses import dataclass
from typing import Optional


class TerrainType(Enum):
    """Terrain types"""
    PLAIN = "plain"
    URBAN = "urban"
    HIGH_GROUND = "high_ground"
    FOREST = "forest"
    WATER = "water"
    MOUNTAIN = "mountain"
    DESERT = "desert"
    SWAMP = "swamp"


@dataclass
class TerrainEffect:
    """Effects of terrain on operations"""
    movement_cost: float        # Multiplier for movement cost
    combat_defense_bonus: float # Defense bonus multiplier
    observation_reduction: float # Observation range reduction
    concealment: float          # Concealment bonus
    description: str


class TerrainEffects:
    """
    Manages terrain effects on combat and movement

    Terrain provides:
    - Movement cost modifiers
    - Combat defense bonuses
    - Observation/concealment effects
    """

    # Terrain effect definitions
    TERRAIN_EFFECTS = {
        TerrainType.PLAIN: TerrainEffect(
            movement_cost=1.0,
            combat_defense_bonus=1.0,
            observation_reduction=0.0,
            concealment=0.1,
            description="平坦地 - 機動力に有利"
        ),
        TerrainType.URBAN: TerrainEffect(
            movement_cost=1.5,
            combat_defense_bonus=1.5,
            observation_reduction=0.3,
            concealment=0.4,
            description="市街地 - 防御に非常に有利、機動力低下"
        ),
        TerrainType.HIGH_GROUND: TerrainEffect(
            movement_cost=1.2,
            combat_defense_bonus=1.3,
            observation_reduction=-0.2,  # Better observation
            concealment=0.2,
            description="高地 - 視界と防御に有利"
        ),
        TerrainType.FOREST: TerrainEffect(
            movement_cost=1.3,
            combat_defense_bonus=1.2,
            observation_reduction=0.3,
            concealment=0.5,
            description="森林 - 隠蔽に有利、視界低下"
        ),
        TerrainType.WATER: TerrainEffect(
            movement_cost=999.0,  # Impassable
            combat_defense_bonus=1.0,
            observation_reduction=0.0,
            concealment=0.0,
            description="水域 - 渡河不可"
        ),
        TerrainType.MOUNTAIN: TerrainEffect(
            movement_cost=2.0,
            combat_defense_bonus=1.8,
            observation_reduction=0.4,
            concealment=0.3,
            description="山岳 - 防御に非常に有利、機動力大幅低下"
        ),
        TerrainType.DESERT: TerrainEffect(
            movement_cost=1.4,
            combat_defense_bonus=1.0,
            observation_reduction=0.1,
            concealment=0.1,
            description="砂漠 - 機動力低下"
        ),
        TerrainType.SWAMP: TerrainEffect(
            movement_cost=2.0,
            combat_defense_bonus=1.1,
            observation_reduction=0.2,
            concealment=0.4,
            description="湿地 - 機動力大幅低下"
        )
    }

    # Unit type modifiers against terrain
    UNIT_TERRAIN_MODIFIERS = {
        # Unit type: {terrain: attack bonus}
        "infantry": {
            TerrainType.FOREST: 1.2,
            TerrainType.URBAN: 1.3,
            TerrainType.MOUNTAIN: 1.2,
            TerrainType.SWAMP: 1.1
        },
        "armor": {
            TerrainType.FOREST: 0.8,
            TerrainType.URBAN: 1.1,
            TerrainType.MOUNTAIN: 0.6,
            TerrainType.SWAMP: 0.7
        },
        "artillery": {
            TerrainType.HIGH_GROUND: 1.4,
            TerrainType.PLAIN: 1.2,
            TerrainType.FOREST: 0.8,
            TerrainType.URBAN: 0.7
        },
        "air_defense": {
            TerrainType.HIGH_GROUND: 1.3,
            TerrainType.URBAN: 1.2,
            TerrainType.MOUNTAIN: 1.1
        },
        "reconnaissance": {
            TerrainType.HIGH_GROUND: 1.3,
            TerrainType.FOREST: 0.8,
            TerrainType.PLAIN: 1.2
        }
    }

    def __init__(self):
        self._terrain_map: dict[tuple[int, int], TerrainType] = {}

    def set_terrain(self, x: int, y: int, terrain: TerrainType):
        """Set terrain at a specific coordinate"""
        self._terrain_map[(x, y)] = terrain

    def get_terrain(self, x: int, y: int) -> TerrainType:
        """Get terrain at a coordinate"""
        return self._terrain_map.get((x, y), TerrainType.PLAIN)

    def get_terrain_effect(self, x: int, y: int) -> TerrainEffect:
        """Get terrain effect at a coordinate"""
        terrain = self.get_terrain(x, y)
        return self.TERRAIN_EFFECTS[terrain]

    def get_movement_cost(
        self,
        from_x: int,
        from_y: int,
        to_x: int,
        to_y: int,
        unit_type: str = "infantry"
    ) -> float:
        """Calculate movement cost between two positions"""
        from_terrain = self.get_terrain(from_x, from_y)
        to_terrain = self.get_terrain(to_x, to_y)

        from_effect = self.TERRAIN_EFFECTS[from_terrain]
        to_effect = self.TERRAIN_EFFECTS[to_terrain]

        # Use the higher cost
        base_cost = max(from_effect.movement_cost, to_effect.movement_cost)

        # Apply unit-specific modifiers
        unit_mods = self.UNIT_TERRAIN_MODIFIERS.get(unit_type.lower(), {})

        # Get modifier for destination terrain
        terrain_mod = unit_mods.get(to_terrain, 1.0)

        return base_cost * terrain_mod

    def get_combat_modifier(
        self,
        defender_x: int,
        defender_y: int,
        attacker_unit_type: str = "infantry",
        defender_unit_type: str = "infantry"
    ) -> tuple[float, float]:
        """
        Get combat modifiers for attacker and defender

        Returns:
            (attacker_modifier, defender_modifier)
        """
        terrain = self.get_terrain(defender_x, defender_y)
        terrain_effect = self.TERRAIN_EFFECTS[terrain]

        # Defender gets terrain bonus
        defender_mod = terrain_effect.combat_defense_bonus

        # Attacker gets unit-terrain modifier
        attacker_unit_mods = self.UNIT_TERRAIN_MODIFIERS.get(attacker_unit_type.lower(), {})
        attacker_mod = attacker_unit_mods.get(terrain, 1.0)

        return attacker_mod, defender_mod

    def get_observation_modifier(
        self,
        x: int,
        y: int,
        has_nod: bool = False
    ) -> float:
        """
        Get observation modifier at a position

        Returns:
            Modifier from 0.0 to 1.0 (1.0 = full observation)
        """
        terrain = self.get_terrain(x, y)
        terrain_effect = self.TERRAIN_EFFECTS[terrain]

        # Base observation is reduced by terrain
        observation = 1.0 - terrain_effect.observation_reduction

        # NOD helps overcome some terrain penalties
        if has_nod and observation < 0.8:
            observation = min(1.0, observation + 0.2)

        return max(0.0, observation)

    def get_concealment(
        self,
        x: int,
        y: int,
        is_night: bool = False
    ) -> float:
        """
        Get concealment bonus at a position

        Returns:
            Concealment bonus from 0.0 to 1.0
        """
        terrain = self.get_terrain(x, y)
        terrain_effect = self.TERRAIN_EFFECTS[terrain]

        concealment = terrain_effect.concealment

        # Night gives additional concealment
        if is_night:
            concealment = min(1.0, concealment + 0.3)

        return concealment

    def can_cross_water(self, unit_type: str) -> bool:
        """Check if unit type can cross water"""
        # Default: no units can cross water without bridges
        # Would need bridge-specific logic for full implementation
        return False

    def is_passable(self, x: int, y: int, unit_type: str = "infantry") -> bool:
        """Check if terrain is passable for a unit type"""
        terrain = self.get_terrain(x, y)
        terrain_effect = self.TERRAIN_EFFECTS[terrain]

        # Water is generally impassable
        if terrain == TerrainType.WATER:
            return False

        # Check movement cost
        if terrain_effect.movement_cost >= 999.0:
            return False

        return True

    def get_terrain_description(self, x: int, y: int) -> str:
        """Get terrain description at a coordinate"""
        terrain = self.get_terrain(x, y)
        effect = self.TERRAIN_EFFECTS[terrain]
        return effect.description


# Global instance
_terrain_effects = TerrainEffects()


def get_terrain_effects() -> TerrainEffects:
    """Get the global terrain effects system"""
    return _terrain_effects
