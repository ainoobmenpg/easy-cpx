# Tests for Terrain Service
import pytest
from app.services.terrain import TerrainType, TerrainEffects, generate_map_terrain, get_terrain_display_info


class TestTerrainEffects:
    def test_get_terrain(self):
        """Test terrain retrieval"""
        effects = TerrainEffects()
        effects.set_terrain(5, 5, TerrainType.FOREST)
        assert effects.get_terrain(5, 5) == TerrainType.FOREST

    def test_default_terrain(self):
        """Test default terrain is plain"""
        effects = TerrainEffects()
        assert effects.get_terrain(0, 0) == TerrainType.PLAIN

    def test_terrain_effect(self):
        """Test terrain effect retrieval"""
        effects = TerrainEffects()
        effect = effects.get_terrain_effect(5, 5)
        assert effect.movement_cost >= 1.0

    def test_forest_effects(self):
        """Test forest terrain effects"""
        effects = TerrainEffects()
        effect = effects.TERRAIN_EFFECTS[TerrainType.FOREST]
        assert effect.combat_defense_bonus == 1.2
        assert effect.concealment == 0.5

    def test_urban_effects(self):
        """Test urban terrain effects"""
        effects = TerrainEffects()
        effect = effects.TERRAIN_EFFECTS[TerrainType.URBAN]
        assert effect.combat_defense_bonus == 1.5
        assert effect.movement_cost == 1.5

    def test_mountain_effects(self):
        """Test mountain terrain effects"""
        effects = TerrainEffects()
        effect = effects.TERRAIN_EFFECTS[TerrainType.MOUNTAIN]
        assert effect.combat_defense_bonus == 1.8
        assert effect.movement_cost == 2.0

    def test_water_impassable(self):
        """Test water is impassable"""
        effects = TerrainEffects()
        effects.set_terrain(0, 0, TerrainType.WATER)
        assert not effects.is_passable(0, 0, "infantry")

    def test_movement_cost_calculation(self):
        """Test movement cost calculation"""
        effects = TerrainEffects()
        cost = effects.get_movement_cost(0, 0, 5, 5, "infantry")
        assert cost >= 1.0

    def test_combat_modifier(self):
        """Test combat modifier calculation"""
        effects = TerrainEffects()
        attacker_mod, defender_mod = effects.get_combat_modifier(5, 5, "infantry", "armor")
        assert attacker_mod > 0
        assert defender_mod >= 1.0

    def test_concealment(self):
        """Test concealment calculation"""
        effects = TerrainEffects()
        concealment = effects.get_concealment(5, 5, False)
        assert 0 <= concealment <= 1.0

    def test_can_cross_water(self):
        """Test water crossing rules"""
        effects = TerrainEffects()
        assert not effects.can_cross_water("infantry")
        assert not effects.can_cross_water("armor")


class TestGenerateMapTerrain:
    def test_generate_terrain_dimensions(self):
        """Test terrain map generation dimensions"""
        terrain = generate_map_terrain(10, 10)
        assert len(terrain) == 100

    def test_generate_terrain_keys(self):
        """Test terrain map keys format"""
        terrain = generate_map_terrain(5, 5)
        assert "0,0" in terrain
        assert "4,4" in terrain

    def test_generate_terrain_values(self):
        """Test terrain map contains valid types"""
        terrain = generate_map_terrain(10, 10)
        valid_types = [t.value for t in TerrainType]
        for value in terrain.values():
            assert value in valid_types

    def test_generate_terrain_seed(self):
        """Test terrain generation is deterministic with seed"""
        terrain1 = generate_map_terrain(5, 5, seed=42)
        terrain2 = generate_map_terrain(5, 5, seed=42)
        assert terrain1 == terrain2


class TestGetTerrainDisplayInfo:
    def test_get_display_info(self):
        """Test terrain display info"""
        info = get_terrain_display_info()
        assert "forest" in info
        assert "urban" in info
        assert "mountain" in info
        assert "water" in info

    def test_display_info_contains_symbol(self):
        """Test display info contains symbol"""
        info = get_terrain_display_info()
        assert "symbol" in info["forest"]
        assert "color" in info["forest"]
        assert "name" in info["forest"]

    def test_display_info_names(self):
        """Test display info contains Japanese names"""
        info = get_terrain_display_info()
        assert info["forest"]["name"] == "森林"
        assert info["urban"]["name"] == "市街地"
        assert info["water"]["name"] == "水域"
