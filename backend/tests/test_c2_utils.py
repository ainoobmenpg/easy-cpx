# Tests for CPX-ORG C2 Utilities

import pytest
from app.services.c2_utils import (
    get_faction_name,
    get_echelon_name,
    generate_callsign,
    generate_unit_c2_data,
    get_callsign_color,
    format_unit_c2_display,
    FACTION_CODES,
    ECHELON_CODES,
)


class TestFactionCodes:
    """Test faction code functions"""

    def test_get_faction_name_known(self):
        """Test getting known faction names"""
        assert get_faction_name("US") == "United States"
        assert get_faction_name("UK") == "United Kingdom"
        assert get_faction_name("GER") == "Germany"

    def test_get_faction_name_unknown(self):
        """Test getting unknown faction name returns code"""
        assert get_faction_name("UNKNOWN") == "UNKNOWN"
        assert get_faction_name("XYZ") == "XYZ"


class TestEchelonCodes:
    """Test echelon code functions"""

    def test_get_echelon_name_known(self):
        """Test getting known echelon names"""
        assert get_echelon_name("platoon") == "Platoon"
        assert get_echelon_name("company") == "Company"
        assert get_echelon_name("battalion") == "Battalion"

    def test_get_echelon_name_unknown(self):
        """Test getting unknown echelon name returns code"""
        assert get_echelon_name("UNKNOWN") == "UNKNOWN"


class TestCallsignGeneration:
    """Test callsign generation"""

    def test_generate_callsign_with_prefix(self):
        """Test callsign generation with NATO prefixes"""
        cs = generate_callsign(0, use_prefix=True)
        assert "ALPHA" in cs

    def test_generate_callsign_without_prefix(self):
        """Test callsign generation with numbers only"""
        cs = generate_callsign(0, use_prefix=False)
        assert cs in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"]

    def test_generate_callsign_deterministic(self):
        """Test that callsigns are deterministic by index"""
        cs1 = generate_callsign(5, use_prefix=True)
        cs2 = generate_callsign(5, use_prefix=True)
        assert cs1 == cs2

    def test_generate_callsign_unique(self):
        """Test that different indices produce different callsigns"""
        callsigns = [generate_callsign(i, use_prefix=True) for i in range(30)]
        assert len(set(callsigns)) > 1  # Most should be unique


class TestUnitC2Data:
    """Test unit C2 data generation"""

    def test_generate_unit_c2_data_defaults(self):
        """Test default C2 data generation"""
        data = generate_unit_c2_data()
        assert data["faction"] == "BLUE"
        assert data["echelon"] == "company"
        assert "callsign" in data

    def test_generate_unit_c2_data_custom(self):
        """Test custom C2 data"""
        data = generate_unit_c2_data(
            faction="US",
            echelon="battalion",
            callsign="ALPHA-1"
        )
        assert data["faction"] == "US"
        assert data["echelon"] == "battalion"
        assert data["callsign"] == "ALPHA-1"

    def test_generate_unit_c2_data_with_index(self):
        """Test C2 data with index"""
        data = generate_unit_c2_data(unit_index=5)
        assert "callsign" in data


class TestCallsighColor:
    """Test callsign color functions"""

    def test_get_callsign_color_known(self):
        """Test getting color for known prefix"""
        assert get_callsign_color("ALPHA") == "#3b82f6"
        assert get_callsign_color("BRAVO") == "#ef4444"
        assert get_callsign_color("ECHO") == "#8b5cf6"

    def test_get_callsign_color_unknown(self):
        """Test getting default color for unknown prefix"""
        color = get_callsign_color("UNKNOWN")
        assert color == "#6b7280"  # Default gray


class TestDisplayFormatting:
    """Test display formatting functions"""

    def test_format_unit_c2_display(self):
        """Test C2 display formatting"""
        display = format_unit_c2_display("US", "company", "ALPHA-1")
        assert display == "US/company/ALPHA-1"

    def test_format_unit_c2_display_all_levels(self):
        """Test C2 display with different echelons"""
        display = format_unit_c2_display("GER", "battalion", "BRAVO-2")
        assert "GER" in display
        assert "battalion" in display
        assert "BRAVO-2" in display
