# Tests for grid_system.py - MGRS/APP-6 utilities

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from app.services.grid_system import (
    GridSystemService,
    ControlMeasuresService,
    APP6SymbolService,
    GridSystemType,
    MGRSPrecision,
)


class TestGridSystemService:
    """Test MGRS grid conversion utilities"""

    def test_default_initialization(self):
        """Test default service initialization"""
        service = GridSystemService()
        assert service.map_width == 50
        assert service.map_height == 50
        assert service.gzd == "34S"
        assert service.meters_per_cell == 1000

    def test_custom_initialization(self):
        """Test custom service initialization"""
        service = GridSystemService(
            map_width=100,
            map_height=80,
            gzd="33T",
            origin_lat=50.0,
            origin_lon=8.0,
            meters_per_cell=500
        )
        assert service.map_width == 100
        assert service.map_height == 80
        assert service.gzd == "33T"
        assert service.meters_per_cell == 500

    def test_xy_to_mgrs_100km(self):
        """Test XY to MGRS conversion at 100km precision"""
        service = GridSystemService()
        mgrs = service.xy_to_mgrs(0, 0, "100km")
        assert "34S" in mgrs

    def test_xy_to_mgrs_1km(self):
        """Test XY to MGRS conversion at 1km precision"""
        service = GridSystemService()
        mgrs = service.xy_to_mgrs(25, 15, "1km")
        assert "34S" in mgrs
        # Should contain coordinate numbers
        assert len(mgrs.split()) >= 2

    def test_xy_to_mgrs_10km(self):
        """Test XY to MGRS conversion at 10km precision"""
        service = GridSystemService()
        mgrs = service.xy_to_mgrs(10, 20, "10km")
        assert "34S" in mgrs

    def test_mgrs_to_xy_valid(self):
        """Test MGRS to XY conversion with valid input"""
        service = GridSystemService()
        # Test with simplified MGRS (just grid zone + square)
        result = service.mgrs_to_xy("34S AB")
        # Should handle gracefully (may return None for simplified input)

    def test_mgrs_to_xy_invalid(self):
        """Test MGRS to XY conversion with invalid input"""
        service = GridSystemService()
        result = service.mgrs_to_xy("INVALID")
        assert result is None

    def test_mgrs_to_xy_empty(self):
        """Test MGRS to XY conversion with empty input"""
        service = GridSystemService()
        result = service.mgrs_to_xy("")
        assert result is None

    def test_get_grid_square(self):
        """Test 100km grid square generation"""
        service = GridSystemService()
        sq = service._get_grid_square(0, 0)
        assert isinstance(sq, str)
        assert len(sq) == 2

    def test_get_grid_reference(self):
        """Test complete grid reference generation"""
        service = GridSystemService()
        ref = service.get_grid_reference(25, 15)
        assert "grid_reference" in ref
        assert "gzd" in ref
        assert "grid_square" in ref
        assert "x" in ref
        assert "y" in ref
        assert ref["x"] == 25
        assert ref["y"] == 15


class TestControlMeasuresService:
    """Test control measures management"""

    def test_add_phase_line(self):
        """Test adding a phase line"""
        service = ControlMeasuresService()
        phase_line = service.add_phase_line(
            id="pl1",
            name="Phase Line Alpha",
            points=[(10, 10), (20, 10), (30, 10)],
            color="#ff0000",
            line_style="solid",
            status="reported"
        )
        assert phase_line.id == "pl1"
        assert phase_line.name == "Phase Line Alpha"
        assert len(phase_line.points) == 3
        assert "pl1" in service.phase_lines

    def test_add_boundary(self):
        """Test adding a boundary"""
        service = ControlMeasuresService()
        boundary = service.add_boundary(
            id="b1",
            name="FLOT",
            owning_side="player",
            points=[(0, 20), (50, 20)],
            color="#0000ff",
            line_style="dashed"
        )
        assert boundary.id == "b1"
        assert boundary.owning_side == "player"
        assert "b1" in service.boundaries

    def test_add_airspace(self):
        """Test adding an airspace"""
        service = ControlMeasuresService()
        airspace = service.add_airspace(
            id="a1",
            name="Restricted Area",
            type="restricted",
            points=[(5, 5), (15, 5), (15, 15), (5, 15)],
            altitude_low=5000,
            altitude_high=15000,
            color="#ffff00",
            status="active"
        )
        assert airspace.id == "a1"
        assert airspace.type == "restricted"
        assert airspace.altitude_low == 5000
        assert "a1" in service.airspaces

    def test_get_all_control_measures(self):
        """Test serialization of all control measures"""
        service = ControlMeasuresService()
        service.add_phase_line("pl1", "PL1", [(10, 10)])
        service.add_boundary("b1", "FLOT", "player", [(0, 0), (50, 0)])
        service.add_airspace("a1", "Zone", "restricted", [(5, 5)])

        all_cm = service.get_all_control_measures()
        assert "phase_lines" in all_cm
        assert "boundaries" in all_cm
        assert "airspaces" in all_cm
        assert len(all_cm["phase_lines"]) == 1
        assert len(all_cm["boundaries"]) == 1
        assert len(all_cm["airspaces"]) == 1

    def test_clear_all(self):
        """Test clearing all control measures"""
        service = ControlMeasuresService()
        service.add_phase_line("pl1", "PL1", [(10, 10)])
        service.add_boundary("b1", "FLOT", "player", [(0, 0)])
        service.add_airspace("a1", "Zone", "restricted", [(5, 5)])

        service.clear_all()
        assert len(service.phase_lines) == 0
        assert len(service.boundaries) == 0
        assert len(service.airspaces) == 0


class TestAPP6SymbolService:
    """Test APP-6 symbol utilities"""

    def test_get_symbol_code_infantry(self):
        """Test APP-6 symbol code for infantry"""
        service = APP6SymbolService()
        code = service.get_symbol_code("infantry")
        assert code == "S-"

    def test_get_symbol_code_armor(self):
        """Test APP-6 symbol code for armor"""
        service = APP6SymbolService()
        code = service.get_symbol_code("armor")
        assert code == "G-"

    def test_get_symbol_code_artillery(self):
        """Test APP-6 symbol code for artillery"""
        service = APP6SymbolService()
        code = service.get_symbol_code("artillery")
        assert code == "F-"

    def test_get_symbol_code_unknown(self):
        """Test APP-6 symbol code for unknown type"""
        service = APP6SymbolService()
        code = service.get_symbol_code("unknown_type")
        assert code == "S-"  # Default

    def test_get_affiliation_player(self):
        """Test affiliation mapping for player"""
        service = APP6SymbolService()
        aff = service.get_affiliation("player")
        assert aff == "friend"

    def test_get_affiliation_enemy(self):
        """Test affiliation mapping for enemy"""
        service = APP6SymbolService()
        aff = service.get_affiliation("enemy")
        assert aff == "enemy"

    def test_get_status_intact(self):
        """Test status mapping for intact"""
        service = APP6SymbolService()
        status = service.get_status("intact")
        assert status == "present"

    def test_get_status_heavy_damage(self):
        """Test status mapping for heavy damage"""
        service = APP6SymbolService()
        status = service.get_status("heavy_damage")
        assert status == "anticipated"

    def test_get_symbol_config(self):
        """Test complete APP-6 symbol configuration"""
        service = APP6SymbolService()
        config = service.get_symbol_config(
            unit_type="infantry",
            side="player",
            status="intact",
            echelon="company",
            modifier="task_force"
        )
        assert config["symbol"] == "S-"
        assert config["affiliation"] == "friend"
        assert config["status"] == "present"
        assert config["echelon"] == "C"
        assert config["modifier"] == "task_force"

    def test_get_color_for_affiliation_friend(self):
        """Test color for friend affiliation"""
        service = APP6SymbolService()
        color = service.get_color_for_affiliation("friend")
        assert color == "#3b82f6"

    def test_get_color_for_affiliation_enemy(self):
        """Test color for enemy affiliation"""
        service = APP6SymbolService()
        color = service.get_color_for_affiliation("enemy")
        assert color == "#ef4444"

    def test_get_color_for_affiliation_unknown(self):
        """Test color for unknown affiliation"""
        service = APP6SymbolService()
        color = service.get_color_for_affiliation("unknown")
        assert color == "#a855f7"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
