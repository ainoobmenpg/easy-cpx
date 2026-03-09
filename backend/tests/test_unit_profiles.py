# Unit Profiles Tests

import pytest
from app.data.unit_profiles import (
    get_unit_profile,
    get_compatibility_bonus,
    UNIT_BEHAVIOR_PROFILES,
    UnitBehaviorProfile,
)
from app.models import normalize_unit_type


class TestGetUnitProfile:
    """Tests for get_unit_profile function"""

    def test_get_armor_profile(self):
        profile = get_unit_profile("armor")
        assert isinstance(profile, UnitBehaviorProfile)
        assert profile.preferred_range == 2
        assert profile.should_advance is True
        assert profile.max_advance_when_low_ammo is True

    def test_get_infantry_profile(self):
        profile = get_unit_profile("infantry")
        assert isinstance(profile, UnitBehaviorProfile)
        assert profile.preferred_range == 1
        assert profile.should_advance is True

    def test_get_atgm_profile(self):
        profile = get_unit_profile("atgm")
        assert isinstance(profile, UnitBehaviorProfile)
        assert profile.preferred_range == 4
        assert profile.should_advance is False
        assert profile.stay_at_range is True

    def test_get_sniper_profile(self):
        profile = get_unit_profile("sniper")
        assert isinstance(profile, UnitBehaviorProfile)
        assert profile.preferred_range == 3
        assert profile.should_advance is False

    def test_get_scout_profile(self):
        profile = get_unit_profile("scout")
        assert isinstance(profile, UnitBehaviorProfile)
        assert profile.preferred_range == 2
        assert profile.should_advance is True

    def test_get_artillery_profile(self):
        profile = get_unit_profile("artillery")
        assert isinstance(profile, UnitBehaviorProfile)
        assert profile.preferred_range == 10
        assert profile.should_advance is False
        assert profile.stay_rear is True

    def test_get_air_defense_profile(self):
        profile = get_unit_profile("air_defense")
        assert isinstance(profile, UnitBehaviorProfile)
        assert profile.preferred_range == 8
        assert profile.target_air is True
        assert profile.should_advance is False

    def test_get_attack_helo_profile(self):
        profile = get_unit_profile("attack_helo")
        assert isinstance(profile, UnitBehaviorProfile)
        assert profile.preferred_range == 3
        assert profile.should_advance is True

    def test_get_transport_helo_profile(self):
        profile = get_unit_profile("transport_helo")
        assert isinstance(profile, UnitBehaviorProfile)
        assert profile.preferred_range == 5
        assert profile.should_advance is False
        assert profile.avoid_combat is True

    def test_get_aircraft_profile(self):
        profile = get_unit_profile("aircraft")
        assert isinstance(profile, UnitBehaviorProfile)
        assert profile.preferred_range == 5
        assert profile.should_advance is True

    def test_get_uav_profile(self):
        profile = get_unit_profile("uav")
        assert isinstance(profile, UnitBehaviorProfile)
        assert profile.preferred_range == 15
        assert profile.should_advance is False
        assert profile.recon_only is True

    def test_get_recon_profile(self):
        profile = get_unit_profile("recon")
        assert isinstance(profile, UnitBehaviorProfile)
        assert profile.preferred_range == 5
        assert profile.should_advance is True

    def test_get_support_profile(self):
        profile = get_unit_profile("support")
        assert isinstance(profile, UnitBehaviorProfile)
        assert profile.preferred_range == 3
        assert profile.should_advance is False
        assert profile.stay_rear is True

    def test_get_default_profile(self):
        # Unknown types fall back to infantry profile
        profile = get_unit_profile("unknown_type")
        assert isinstance(profile, UnitBehaviorProfile)
        assert profile.preferred_range == 1
        assert profile.should_advance is True

    def test_case_insensitive(self):
        profile1 = get_unit_profile("ARMOR")
        profile2 = get_unit_profile("Armor")
        profile3 = get_unit_profile("armor")
        assert profile1.preferred_range == profile2.preferred_range == profile3.preferred_range

    def test_partial_match_tank(self):
        profile = get_unit_profile("main_battle_tank")
        assert isinstance(profile, UnitBehaviorProfile)
        assert profile.preferred_range == 2

    def test_partial_match_infantry(self):
        profile = get_unit_profile("motorized_infantry")
        assert isinstance(profile, UnitBehaviorProfile)
        assert profile.should_advance is True


class TestGetCompatibilityBonus:
    """Tests for get_compatibility_bonus function"""

    def test_armor_vs_armor(self):
        bonus = get_compatibility_bonus("armor", "armor")
        assert bonus == 0.0

    def test_armor_vs_infantry(self):
        bonus = get_compatibility_bonus("armor", "infantry")
        assert bonus == 0.3

    def test_atgm_vs_armor(self):
        bonus = get_compatibility_bonus("atgm", "armor")
        assert bonus == 0.4

    def test_infantry_vs_armor(self):
        bonus = get_compatibility_bonus("infantry", "armor")
        assert bonus == -0.3

    def test_sniper_vs_infantry(self):
        bonus = get_compatibility_bonus("sniper", "infantry")
        assert bonus == 0.3

    def test_air_defense_vs_aircraft(self):
        bonus = get_compatibility_bonus("air_defense", "aircraft")
        assert bonus == 0.4

    def test_air_defense_vs_helo(self):
        bonus = get_compatibility_bonus("air_defense", "attack_helo")
        assert bonus == 0.4

    def test_attack_helo_vs_armor(self):
        bonus = get_compatibility_bonus("attack_helo", "armor")
        assert bonus == 0.3

    def test_aircraft_vs_armor(self):
        bonus = get_compatibility_bonus("aircraft", "armor")
        assert bonus == 0.3

    def test_artillery_vs_infantry(self):
        bonus = get_compatibility_bonus("artillery", "infantry")
        assert bonus == 0.2

    def test_unknown_attacker(self):
        # Unknown maps to infantry
        bonus = get_compatibility_bonus("unknown", "armor")
        assert bonus == -0.3

    def test_unknown_defender(self):
        # Unknown maps to infantry
        bonus = get_compatibility_bonus("armor", "unknown")
        assert bonus == 0.3

    def test_case_insensitive_compatibility(self):
        bonus1 = get_compatibility_bonus("ARMOR", "INFANTRY")
        bonus2 = get_compatibility_bonus("armor", "infantry")
        assert bonus1 == bonus2

    def test_transport_helo_normalization(self):
        bonus = get_compatibility_bonus("transport_helo", "infantry")
        # transport_helo not in matrix, returns 0
        assert bonus == 0.0


class TestNormalizeUnitType:
    """Tests for normalize_unit_type function"""

    def test_normalize_tank(self):
        assert normalize_unit_type("tank") == "armor"
        assert normalize_unit_type("m1_abrams") == "armor"
        assert normalize_unit_type("leopard") == "armor"
        assert normalize_unit_type("t72") == "armor"
        assert normalize_unit_type("bradley") == "armor"

    def test_normalize_atgm(self):
        assert normalize_unit_type("atgm") == "atgm"
        # anti-tank should map to atgm
        assert normalize_unit_type("anti-tank") == "atgm"

    def test_normalize_infantry(self):
        assert normalize_unit_type("infantry") == "infantry"
        assert normalize_unit_type("inf") == "infantry"

    def test_normalize_artillery(self):
        assert normalize_unit_type("artillery") == "artillery"
        assert normalize_unit_type("howitzer") == "artillery"
        assert normalize_unit_type("mlrs") == "artillery"
        # m109 is a self-propelled howitzer (artillery)
        assert normalize_unit_type("m109") == "artillery"

    def test_normalize_air_defense(self):
        assert normalize_unit_type("air_defense") == "air_defense"
        assert normalize_unit_type("sam") == "air_defense"
        assert normalize_unit_type("patriot") == "air_defense"
        assert normalize_unit_type("flak") == "air_defense"

    def test_normalize_attack_helo(self):
        assert normalize_unit_type("attack_helo") == "attack_helo"
        assert normalize_unit_type("apache") == "attack_helo"
        assert normalize_unit_type("hind") == "attack_helo"

    def test_normalize_transport_helo(self):
        assert normalize_unit_type("transport_helo") == "transport_helo"
        assert normalize_unit_type("blackhawk") == "transport_helo"

    def test_normalize_aircraft(self):
        assert normalize_unit_type("aircraft") == "aircraft"
        assert normalize_unit_type("fighter") == "aircraft"
        assert normalize_unit_type("f15") == "aircraft"
        assert normalize_unit_type("f16") == "aircraft"

    def test_normalize_uav(self):
        assert normalize_unit_type("uav") == "uav"
        assert normalize_unit_type("drone") == "uav"
        assert normalize_unit_type("reaper") == "uav"

    def test_normalize_recon(self):
        assert normalize_unit_type("recon") == "recon"

    def test_normalize_support(self):
        assert normalize_unit_type("support") == "support"
        assert normalize_unit_type("supply") == "support"

    def test_normalize_default(self):
        # Unknown types fall back to infantry
        assert normalize_unit_type("unknown_type") == "infantry"
        assert normalize_unit_type("medical") == "infantry"

    def test_normalize_case_insensitive(self):
        assert normalize_unit_type("ARMOR") == "armor"
        assert normalize_unit_type("TANK") == "armor"

    def test_normalize_legacy_nato_prefix(self):
        assert normalize_unit_type("nato_armor") == "armor"
        assert normalize_unit_type("nato_infantry") == "infantry"
        assert normalize_unit_type("nato_artillery") == "artillery"

    def test_normalize_legacy_wp_prefix(self):
        assert normalize_unit_type("wp_armor") == "armor"
        assert normalize_unit_type("wp_infantry") == "infantry"
        assert normalize_unit_type("wp_artillery") == "artillery"


class TestUnitBehaviorProfile:
    """Tests for UnitBehaviorProfile class"""

    def test_default_values(self):
        profile = UnitBehaviorProfile()
        assert profile.preferred_range == 2
        assert profile.min_range == 0
        assert profile.max_range == 5
        assert profile.should_advance is True
        assert profile.stay_at_range is False
        assert profile.stay_rear is False
        assert profile.avoid_combat is False
        assert profile.recon_only is False
        assert profile.target_air is False
        assert profile.max_advance_when_low_ammo is False

    def test_custom_values(self):
        profile = UnitBehaviorProfile(
            preferred_range=10,
            min_range=5,
            max_range=20,
            should_advance=False,
            stay_at_range=True,
            stay_rear=True,
            avoid_combat=True,
            recon_only=True,
            target_air=True,
            max_advance_when_low_ammo=True,
        )
        assert profile.preferred_range == 10
        assert profile.min_range == 5
        assert profile.max_range == 20
        assert profile.should_advance is False
        assert profile.stay_at_range is True
        assert profile.stay_rear is True
        assert profile.avoid_combat is True
        assert profile.recon_only is True
        assert profile.target_air is True
        assert profile.max_advance_when_low_ammo is True
