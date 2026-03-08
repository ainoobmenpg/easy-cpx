# Equipment Database
# Cold War era (1985) Central European scenario equipment
from enum import Enum
from typing import Optional


class UnitCategory(Enum):
    INFANTRY = "infantry"
    ARMOR = "armor"
    ARTILLERY = "artillery"
    AIR_DEFENSE = "air_defense"
    HELICOPTER = "helicopter"
    AIRCRAFT = "aircraft"
    RECON = "recon"
    SUPPORT = "support"


class Side(Enum):
    NATO = "nato"
    WP = "wp"  # Warsaw Pact


class EquipmentDatabase:
    """Database of Cold War era equipment"""

    # NATO Equipment
    NATO_EQUIPMENT = {
        # Main Battle Tanks
        "m1_abrams": {
            "name": "M1 Abrams",
            "category": UnitCategory.ARMOR,
            "side": Side.NATO,
            "nation": "USA",
            "year": 1985,
            "combat_strength": 100,
            "armor_front": 950,
            "armor_side": 450,
            "primary_weapon": "105mm M68A1",
            "ammo_capacity": 55,
            "speed_road": 67,
            "speed_offroad": 40,
            "crew": 4,
            "notes": "Gas turbine engine, Chobham armor",
        },
        "leopard_2": {
            "name": "Leopard 2",
            "category": UnitCategory.ARMOR,
            "side": Side.NATO,
            "nation": "FRG",
            "year": 1985,
            "combat_strength": 100,
            "armor_front": 1000,
            "armor_side": 500,
            "primary_weapon": "120mm L44",
            "ammo_capacity": 42,
            "speed_road": 68,
            "speed_offroad": 45,
            "crew": 4,
            "notes": "Excellent fire control system",
        },
        "leopard_1": {
            "name": "Leopard 1",
            "category": UnitCategory.ARMOR,
            "side": Side.NATO,
            "nation": "FRG",
            "year": 1985,
            "combat_strength": 75,
            "armor_front": 500,
            "armor_side": 350,
            "primary_weapon": "105mm L7",
            "ammo_capacity": 42,
            "speed_road": 65,
            "speed_offroad": 35,
            "crew": 4,
            "notes": "Older but reliable",
        },

        # Infantry Fighting Vehicles
        "m2_bradley": {
            "name": "M2 Bradley",
            "category": UnitCategory.ARMOR,
            "side": Side.NATO,
            "nation": "USA",
            "year": 1985,
            "combat_strength": 60,
            "armor_front": 300,
            "armor_side": 150,
            "primary_weapon": "25mm M242 Bushmaster",
            "ammo_capacity": 600,
            "speed_road": 66,
            "speed_offroad": 30,
            "crew": 3,
            "passengers": 6,
            "notes": "TOW missile launcher",
        },
        "marder": {
            "name": "Marder 1",
            "category": UnitCategory.ARMOR,
            "side": Side.NATO,
            "nation": "FRG",
            "year": 1985,
            "combat_strength": 55,
            "armor_front": 250,
            "armor_side": 150,
            "primary_weapon": "20mm Rh202",
            "ammo_capacity": 500,
            "speed_road": 70,
            "speed_offroad": 32,
            "crew": 3,
            "passengers": 5,
            "notes": "MILAN missile launcher",
        },

        # Artillery
        "m109": {
            "name": "M109A2",
            "category": UnitCategory.ARTILLERY,
            "side": Side.NATO,
            "nation": "USA",
            "year": 1985,
            "combat_strength": 35,
            "armor": 15,
            "primary_weapon": "155mm M126",
            "ammo_capacity": 36,
            "range_km": 18,
            "speed_road": 56,
            "crew": 6,
            "notes": "Self-propelled howitzer",
        },
        "pzh2000": {
            "name": "PzH 2000",
            "category": UnitCategory.ARTILLERY,
            "side": Side.NATO,
            "nation": "FRG",
            "year": 1985,  # Pre-production
            "combat_strength": 50,
            "armor": 20,
            "primary_weapon": "155mm L52",
            "ammo_capacity": 60,
            "range_km": 30,
            "speed_road": 60,
            "crew": 5,
            "notes": "Advanced self-propelled howitzer",
        },
        "mlrs": {
            "name": "M270 MLRS",
            "category": UnitCategory.ARTILLERY,
            "side": Side.NATO,
            "nation": "USA",
            "year": 1985,
            "combat_strength": 45,
            "armor": 10,
            "primary_weapon": "227mm rocket",
            "ammo_capacity": 12,
            "range_km": 32,
            "speed_road": 64,
            "crew": 3,
            "notes": "Multiple Launch Rocket System",
        },

        # Air Defense
        "patriot": {
            "name": "Patriot MIM-104",
            "category": UnitCategory.AIR_DEFENSE,
            "side": Side.NATO,
            "nation": "USA",
            "year": 1985,
            "combat_strength": 80,
            "armor": 10,
            "primary_weapon": "MIM-104 missiles",
            "missiles": 8,
            "range_km": 80,
            "speed_road": 65,
            "crew": 8,
            "notes": "Long-range surface-to-air missile",
        },
        "flakpanzer": {
            "name": "Gepard",
            "category": UnitCategory.AIR_DEFENSE,
            "side": Side.NATO,
            "nation": "FRG",
            "year": 1985,
            "combat_strength": 40,
            "armor": 40,
            "primary_weapon": "35mm twin cannon",
            "ammo_capacity": 320,
            "range_km": 4,
            "speed_road": 70,
            "crew": 3,
            "notes": "Self-propelled anti-aircraft",
        },
        "stinger": {
            "name": "M2 Stinger",
            "category": UnitCategory.AIR_DEFENSE,
            "side": Side.NATO,
            "nation": "USA",
            "year": 1985,
            "combat_strength": 30,
            "primary_weapon": "FIM-92 missile",
            "missiles": 4,
            "range_km": 5,
            "crew": 2,
            "notes": "Man-portable air defense",
        },

        # Helicopters
        "ah64_apache": {
            "name": "AH-64 Apache",
            "category": UnitCategory.HELICOPTER,
            "side": Side.NATO,
            "nation": "USA",
            "year": 1985,
            "combat_strength": 85,
            "armor": 50,
            "primary_weapon": "30mm chain gun",
            "secondary_weapon": "AGM-114 Hellfire x16",
            "speed_kmh": 293,
            "range_km": 476,
            "crew": 2,
            "notes": "Attack helicopter",
        },
        "uh60_blackhawk": {
            "name": "UH-60 Black Hawk",
            "category": UnitCategory.HELICOPTER,
            "side": Side.NATO,
            "nation": "USA",
            "year": 1985,
            "combat_strength": 25,
            "armor": 25,
            "primary_weapon": "M134 minigun",
            "speed_kmh": 282,
            "range_km": 600,
            "crew": 4,
            "passengers": 11,
            "notes": "Utility helicopter",
        },

        # Aircraft
        "f16_fighting_falcon": {
            "name": "F-16 Fighting Falcon",
            "category": UnitCategory.AIRCRAFT,
            "side": Side.NATO,
            "nation": "USA",
            "year": 1985,
            "combat_strength": 90,
            "primary_weapon": "M61 Vulcan 20mm",
            "missiles": "AIM-9 x2, AIM-7 x2",
            "speed_kmh": 2120,
            "range_km": 3890,
            "crew": 1,
            "notes": "Multi-role fighter",
        },
        "f15_eagle": {
            "name": "F-15C Eagle",
            "category": UnitCategory.AIRCRAFT,
            "side": Side.NATO,
            "nation": "USA",
            "year": 1985,
            "combat_strength": 100,
            "primary_weapon": "M61 Vulcan 20mm",
            "missiles": "AIM-9 x4, AIM-7 x4",
            "speed_kmh": 2650,
            "range_km": 4620,
            "crew": 1,
            "notes": "Air superiority fighter",
        },
        "tornado": {
            "name": "Panavia Tornado",
            "category": UnitCategory.AIRCRAFT,
            "side": Side.NATO,
            "nation": "NATO",
            "year": 1985,
            "combat_strength": 95,
            "primary_weapon": "Mauser BK-27 27mm",
            "missiles": "AIM-9 x2",
            "speed_kmh": 2230,
            "range_km": 2900,
            "crew": 2,
            "notes": "Ground attack & air superiority",
        },
    }

    # Warsaw Pact Equipment
    WP_EQUIPMENT = {
        # Main Battle Tanks
        "t72": {
            "name": "T-72",
            "category": UnitCategory.ARMOR,
            "side": Side.WP,
            "nation": "USSR",
            "year": 1985,
            "combat_strength": 80,
            "armor_front": 800,
            "armor_side": 400,
            "primary_weapon": "125mm 2A46",
            "ammo_capacity": 44,
            "speed_road": 60,
            "speed_offroad": 35,
            "crew": 3,
            "notes": "Auto-loader system",
        },
        "t80": {
            "name": "T-80",
            "category": UnitCategory.ARMOR,
            "side": Side.WP,
            "nation": "USSR",
            "year": 1985,
            "combat_strength": 95,
            "armor_front": 900,
            "armor_side": 450,
            "primary_weapon": "125mm 2A46",
            "ammo_capacity": 40,
            "speed_road": 70,
            "speed_offroad": 40,
            "crew": 3,
            "notes": "Gas turbine engine",
        },
        "t64": {
            "name": "T-64",
            "category": UnitCategory.ARMOR,
            "side": Side.WP,
            "nation": "USSR",
            "year": 1985,
            "combat_strength": 85,
            "armor_front": 850,
            "armor_side": 420,
            "primary_weapon": "125mm 2A46",
            "ammo_capacity": 36,
            "speed_road": 60,
            "speed_offroad": 35,
            "crew": 3,
            "notes": "Composite armor",
        },

        # Infantry Fighting Vehicles
        "bmp2": {
            "name": "BMP-2",
            "category": UnitCategory.ARMOR,
            "side": Side.WP,
            "nation": "USSR",
            "year": 1985,
            "combat_strength": 55,
            "armor_front": 200,
            "armor_side": 100,
            "primary_weapon": "30mm 2A42",
            "secondary_weapon": "AT-5 Spandrel",
            "ammo_capacity": 500,
            "speed_road": 65,
            "speed_offroad": 30,
            "crew": 3,
            "passengers": 7,
            "notes": "Improved firing ports",
        },
        "bmp1": {
            "name": "BMP-1",
            "category": UnitCategory.ARMOR,
            "side": Side.WP,
            "nation": "USSR",
            "year": 1985,
            "combat_strength": 40,
            "armor_front": 150,
            "armor_side": 80,
            "primary_weapon": "73mm gun",
            "secondary_weapon": "AT-3 Sagger",
            "ammo_capacity": 300,
            "speed_road": 65,
            "speed_offroad": 28,
            "crew": 3,
            "passengers": 8,
            "notes": "First IFV",
        },

        # Artillery
        "2s19": {
            "name": "2S19 Msta-S",
            "category": UnitCategory.ARTILLERY,
            "side": Side.WP,
            "nation": "USSR",
            "year": 1985,  # Pre-production
            "combat_strength": 45,
            "armor": 15,
            "primary_weapon": "152mm 2A65",
            "ammo_capacity": 30,
            "range_km": 25,
            "speed_road": 60,
            "crew": 5,
            "notes": "Self-propelled howitzer",
        },
        "bm21": {
            "name": "BM-21 Grad",
            "category": UnitCategory.ARTILLERY,
            "side": Side.WP,
            "nation": "USSR",
            "year": 1985,
            "combat_strength": 40,
            "armor": 5,
            "primary_weapon": "122mm rocket",
            "ammo_capacity": 40,
            "range_km": 20,
            "speed_road": 75,
            "crew": 6,
            "notes": "Multiple rocket launcher",
        },

        # Air Defense
        "sa11": {
            "name": "Buk-M1",
            "category": UnitCategory.AIR_DEFENSE,
            "side": Side.WP,
            "nation": "USSR",
            "year": 1985,
            "combat_strength": 75,
            "armor": 10,
            "primary_weapon": "9M38 missile",
            "missiles": 4,
            "range_km": 45,
            "speed_road": 60,
            "crew": 4,
            "notes": "Medium-range SAM",
        },
        "sa6": {
            "name": "Kub",
            "category": UnitCategory.AIR_DEFENSE,
            "side": Side.WP,
            "nation": "USSR",
            "year": 1985,
            "combat_strength": 55,
            "armor": 10,
            "primary_weapon": "3M9 missile",
            "missiles": 6,
            "range_km": 25,
            "speed_road": 70,
            "crew": 4,
            "notes": "Self-propelled SAM",
        },
        "sa7": {
            "name": "Strela-2",
            "category": UnitCategory.AIR_DEFENSE,
            "side": Side.WP,
            "nation": "USSR",
            "year": 1985,
            "combat_strength": 20,
            "primary_weapon": "9M32 missile",
            "missiles": 2,
            "range_km": 3.5,
            "crew": 1,
            "notes": "Man-portable SAM",
        },

        # Helicopters
        "mi24_hind": {
            "name": "Mi-24 Hind",
            "category": UnitCategory.HELICOPTER,
            "side": Side.WP,
            "nation": "USSR",
            "year": 1985,
            "combat_strength": 80,
            "armor": 50,
            "primary_weapon": "12.7mm Yak-B",
            "secondary_weapon": "AT-2 Swatter",
            "speed_kmh": 335,
            "range_km": 450,
            "crew": 2,
            "passengers": 8,
            "notes": "Attack transport helicopter",
        },
        "mi17": {
            "name": "Mi-17 Hip",
            "category": UnitCategory.HELICOPTER,
            "side": Side.WP,
            "nation": "USSR",
            "year": 1985,
            "combat_strength": 25,
            "armor": 20,
            "primary_weapon": "12.7mm NSV",
            "speed_kmh": 250,
            "range_km": 600,
            "crew": 2,
            "passengers": 12,
            "notes": "Utility helicopter",
        },

        # Aircraft
        "mig29": {
            "name": "MiG-29 Fulcrum",
            "category": UnitCategory.AIRCRAFT,
            "side": Side.WP,
            "nation": "USSR",
            "year": 1985,
            "combat_strength": 95,
            "primary_weapon": "GSh-30-1 30mm",
            "missiles": "R-60 x2, R-27 x4",
            "speed_kmh": 2440,
            "range_km": 2900,
            "crew": 1,
            "notes": "Air superiority fighter",
        },
        "mig27": {
            "name": "MiG-27 Flogger",
            "category": UnitCategory.AIRCRAFT,
            "side": Side.WP,
            "nation": "USSR",
            "year": 1985,
            "combat_strength": 75,
            "primary_weapon": "GSh-6-30 30mm",
            "missiles": "R-60 x2",
            "speed_kmh": 1850,
            "range_km": 2500,
            "crew": 1,
            "notes": "Ground attack fighter",
        },
        "su25": {
            "name": "Su-25 Frogfoot",
            "category": UnitCategory.AIRCRAFT,
            "side": Side.WP,
            "nation": "USSR",
            "year": 1985,
            "combat_strength": 70,
            "primary_weapon": "GSh-30-2 30mm",
            "missiles": "AS-10 x2",
            "speed_kmh": 950,
            "range_km": 2500,
            "crew": 1,
            "notes": "Close air support",
        },
    }

    @classmethod
    def get_equipment(cls, equipment_id: str, side: Side = None) -> Optional[dict]:
        """Get equipment by ID, optionally filtered by side"""
        all_equipment = {}

        if side is None or side == Side.NATO:
            all_equipment.update(cls.NATO_EQUIPMENT)
        if side is None or side == Side.WP:
            all_equipment.update(cls.WP_EQUIPMENT)

        return all_equipment.get(equipment_id)

    @classmethod
    def get_all_equipment(cls, side: Side = None) -> dict:
        """Get all equipment, optionally filtered by side"""
        if side == Side.NATO:
            return cls.NATO_EQUIPMENT.copy()
        elif side == Side.WP:
            return cls.WP_EQUIPMENT.copy()
        else:
            result = cls.NATO_EQUIPMENT.copy()
            result.update(cls.WP_EQUIPMENT)
            return result

    @classmethod
    def get_by_category(cls, category: UnitCategory, side: Side = None) -> dict:
        """Get equipment by category"""
        result = {}
        all_equipment = cls.get_all_equipment(side)

        for eq_id, eq_data in all_equipment.items():
            if eq_data["category"] == category:
                result[eq_id] = eq_data

        return result


# Unit type mapping to equipment
UNIT_TYPE_EQUIPMENT_MAP = {
    "nato_infantry": ["m1_abrams", "m2_bradley"],
    "nato_armor": ["m1_abrams", "leopard_2"],
    "nato_artillery": ["m109", "mlrs"],
    "nato_air_defense": ["patriot", "flakpanzer"],
    "nato_attack_helo": ["ah64_apache"],
    "nato_transport_helo": ["uh60_blackhawk"],
    "nato_air_superiority": ["f15_eagle"],
    "nato_multirole": ["f16_fighting_falcon", "tornado"],

    "wp_infantry": ["t72", "bmp2"],
    "wp_armor": ["t72", "t80"],
    "wp_artillery": ["bm21", "2s19"],
    "wp_air_defense": ["sa11", "sa6"],
    "wp_attack_helo": ["mi24_hind"],
    "wp_transport_helo": ["mi17"],
    "wp_air_superiority": ["mig29"],
    "wp_ground_attack": ["mig27", "su25"],
}
