# Initial Setup Service
# Handles initial deployment, enemy concealment, and date/time initialization
import random
from typing import Optional
from datetime import datetime, timedelta
from enum import Enum

from app.data.weapons import EquipmentDatabase, Side, UnitCategory


class DeploymentZone(Enum):
    FRONT_LINE = "front_line"  # 前線
    SECOND_LINE = "second_line"  # 第二線
    RESERVE = "reserve"  # 予備
    REAR = "rear"  # 後方
    FLANK = "flank"  # 側面


class InitialSetupService:
    """Service for managing initial deployment and game setup"""

    # Default scenario date (Cold War crisis simulation)
    DEFAULT_START_DATE = "1985-11-22"  # Near Thanksgiving 1985
    DEFAULT_START_TIME = "06:00"  # Dawn
    DEFAULT_SCENARIO_DURATION_HOURS = 72  # 3 days

    # Time progression per turn (minutes)
    TIME_ADVANCE_NORMAL = 15
    TIME_ADVANCE_URGENT = 5
    TIME_ADVANCE_EXTENDED = 60

    def __init__(self, random_seed: Optional[int] = None):
        if random_seed is not None:
            random.seed(random_seed)

    def initialize_game_date(self, start_date: str = None, start_time: str = None) -> dict:
        """Initialize game date and time"""
        return {
            "date": start_date or self.DEFAULT_START_DATE,
            "time": start_time or self.DEFAULT_START_TIME,
            "scenario_duration_hours": self.DEFAULT_SCENARIO_DURATION_HOURS,
        }

    def calculate_turn_time_advance(self, turn_type: str = "normal") -> int:
        """Calculate time advance per turn"""
        if turn_type == "urgent":
            return self.TIME_ADVANCE_URGENT
        elif turn_type == "extended":
            return self.TIME_ADVANCE_EXTENDED
        else:
            return self.TIME_ADVANCE_NORMAL

    def advance_time(self, current_date: str, current_time: str, turn_type: str = "normal") -> dict:
        """Advance game time by turn"""
        minutes_to_add = self.calculate_turn_time_advance(turn_type)

        # Parse current time
        hour, minute = map(int, current_time.split(":"))

        # Create datetime
        base_date = datetime.fromisoformat(current_date)
        current_datetime = base_date.replace(hour=hour, minute=minute)

        # Add time
        new_datetime = current_datetime + timedelta(minutes=minutes_to_add)

        return {
            "date": new_datetime.strftime("%Y-%m-%d"),
            "time": new_datetime.strftime("%H:%M"),
            "minutes_elapsed": minutes_to_add,
        }

    def create_player_deployment(
        self,
        map_width: float,
        map_height: float,
        side: str = "player"
    ) -> list:
        """Create initial player deployment"""
        # Player starts on the western (left) side
        units = []

        # Main defensive line
        defensive_line_y = map_height * 0.3

        # Armor units
        units.extend([
            {
                "name": "Alpha Company",
                "unit_type": "nato_armor",
                "side": side,
                "x": 2 + random.uniform(-0.5, 0.5),
                "y": defensive_line_y + random.uniform(-1, 1),
                "status": "intact",
                "strength": 100,
                "ammo": "full",
                "fuel": "full",
                "readiness": "full",
                "deployment_zone": DeploymentZone.FRONT_LINE.value,
            },
            {
                "name": "Bravo Company",
                "unit_type": "nato_armor",
                "side": side,
                "x": 4 + random.uniform(-0.5, 0.5),
                "y": defensive_line_y + random.uniform(-1, 1),
                "status": "intact",
                "strength": 100,
                "ammo": "full",
                "fuel": "full",
                "readiness": "full",
                "deployment_zone": DeploymentZone.FRONT_LINE.value,
            },
        ])

        # Infantry
        units.extend([
            {
                "name": "1st Battalion",
                "unit_type": "nato_infantry",
                "side": side,
                "x": 3 + random.uniform(-0.5, 0.5),
                "y": defensive_line_y + random.uniform(-2, 2),
                "status": "intact",
                "strength": 100,
                "ammo": "full",
                "fuel": "full",
                "readiness": "full",
                "deployment_zone": DeploymentZone.FRONT_LINE.value,
            },
            {
                "name": "2nd Battalion",
                "unit_type": "nato_infantry",
                "side": side,
                "x": 5 + random.uniform(-0.5, 0.5),
                "y": defensive_line_y + random.uniform(-2, 2),
                "status": "intact",
                "strength": 100,
                "ammo": "full",
                "fuel": "full",
                "readiness": "full",
                "deployment_zone": DeploymentZone.SECOND_LINE.value,
            },
        ])

        # Artillery
        units.extend([
            {
                "name": "Artillery Battery A",
                "unit_type": "nato_artillery",
                "side": side,
                "x": 1 + random.uniform(-0.3, 0.3),
                "y": defensive_line_y + random.uniform(-1, 1),
                "status": "intact",
                "strength": 100,
                "ammo": "full",
                "fuel": "full",
                "readiness": "full",
                "deployment_zone": DeploymentZone.SECOND_LINE.value,
            },
        ])

        # Air defense
        units.extend([
            {
                "name": "Air Defense Platoon",
                "unit_type": "nato_air_defense",
                "side": side,
                "x": 0.5,
                "y": defensive_line_y,
                "status": "intact",
                "strength": 100,
                "ammo": "full",
                "fuel": "full",
                "readiness": "full",
                "deployment_zone": DeploymentZone.REAR.value,
            },
        ])

        # Recon units
        units.extend([
            {
                "name": "Recon Platoon",
                "unit_type": "nato_multirole",
                "side": side,
                "x": 6,
                "y": defensive_line_y + random.uniform(-3, 3),
                "status": "intact",
                "strength": 100,
                "ammo": "full",
                "fuel": "full",
                "readiness": "full",
                "deployment_zone": DeploymentZone.FRONT_LINE.value,
                "recon_range": 4,
            },
        ])

        return units

    def create_enemy_deployment(
        self,
        map_width: float,
        map_height: float,
        reveal_level: int = 0
    ) -> list:
        """Create enemy deployment with concealment rules

        reveal_level: 0-100, how much info is available to player
        """
        # Enemy starts on the eastern (right) side
        units = []

        # Concealment zone - enemies start further east
        base_x = map_width * 0.7  # Start at 70% of map

        # Randomize exact positions within concealment zone
        for _ in range(3):
            # Armor in concealed positions
            unit = {
                "name": f"Enemy Tank Company {random.randint(1,9)}",
                "unit_type": "wp_armor",
                "side": "enemy",
                "x": base_x + random.uniform(2, 6),
                "y": map_height * 0.2 + random.uniform(0, map_height * 0.6),
                "status": "intact",
                "strength": 100,
                "ammo": "full",
                "fuel": "full",
                "readiness": "full",
                "deployment_zone": DeploymentZone.RESERVE.value,
                # Concealment data
                "is_concealed": True,
                "detection_difficulty": random.randint(30, 70),
            }
            units.append(unit)

        # Infantry
        for _ in range(2):
            unit = {
                "name": f"Enemy Motor Rifle {random.randint(1,9)}",
                "unit_type": "wp_infantry",
                "side": "enemy",
                "x": base_x + random.uniform(1, 5),
                "y": map_height * 0.2 + random.uniform(0, map_height * 0.6),
                "status": "intact",
                "strength": 100,
                "ammo": "full",
                "fuel": "full",
                "readiness": "full",
                "deployment_zone": DeploymentZone.SECOND_LINE.value,
                "is_concealed": True,
                "detection_difficulty": random.randint(20, 50),
            }
            units.append(unit)

        # Artillery
        unit = {
            "name": "Enemy Artillery Regiment",
            "unit_type": "wp_artillery",
            "side": "enemy",
            "x": base_x + random.uniform(3, 7),
            "y": map_height * 0.5,
            "status": "intact",
            "strength": 100,
            "ammo": "full",
            "fuel": "full",
            "readiness": "full",
            "deployment_zone": DeploymentZone.RESERVE.value,
            "is_concealed": True,
            "detection_difficulty": 60,
        }
        units.append(unit)

        # Air defense
        for _ in range(2):
            unit = {
                "name": f"Enemy SAM {random.randint(1,3)}",
                "unit_type": "wp_air_defense",
                "side": "enemy",
                "x": base_x + random.uniform(2, 8),
                "y": map_height * 0.3 + random.uniform(0, map_height * 0.4),
                "status": "intact",
                "strength": 100,
                "ammo": "full",
                "fuel": "full",
                "readiness": "full",
                "deployment_zone": DeploymentZone.REAR.value,
                "is_concealed": True,
                "detection_difficulty": 50,
            }
            units.append(unit)

        # Apply concealment based on reveal level
        if reveal_level > 0:
            for unit in units:
                # Higher reveal_level = less concealment
                detection_chance = (100 - unit.get("detection_difficulty", 50)) * (reveal_level / 100)
                if random.random() * 100 < detection_chance:
                    unit["is_concealed"] = False

        return units

    def generate_initial_intel(
        self,
        enemy_units: list,
        intel_level: int = 20
    ) -> list:
        """Generate initial intelligence report on enemy

        intel_level: 0-100, player's initial intel quality
        """
        intel_reports = []

        for enemy in enemy_units:
            # Random chance of detection based on intel level
            if random.random() * 100 < intel_level:
                # Generate report with uncertainty
                confidence = "estimated"
                if random.random() * 100 < intel_level * 0.5:
                    confidence = "confirmed"

                report = {
                    "unit_id": enemy.get("id"),
                    "detected": True,
                    "confidence": confidence,
                    "estimated_position": {
                        "x": enemy.get("x", 0) + random.uniform(-2, 2),
                        "y": enemy.get("y", 0) + random.uniform(-2, 2),
                    },
                    "estimated_type": enemy.get("unit_type", "unknown"),
                    "estimated_strength": enemy.get("strength", 100) + random.randint(-20, 20),
                    "freshness": "stale",  # Initial intel is usually old
                    "source": "initial_intel",
                }
                intel_reports.append(report)
            else:
                report = {
                    "unit_id": enemy.get("id"),
                    "detected": False,
                    "confidence": "unknown",
                }
                intel_reports.append(report)

        return intel_reports

    def create_initial_weather(self) -> dict:
        """Generate initial weather conditions"""
        weather_types = [
            "clear",
            "light_rain",
            "heavy_rain",
            "fog",
            "overcast",
        ]

        # Winter scenario -倾向 to fog and overcast
        weights = [0.2, 0.2, 0.1, 0.3, 0.2]

        weather = random.choices(weather_types, weights=weights)[0]

        return {
            "type": weather,
            "temperature": random.randint(-5, 10),  # Celsius, November
            "visibility_km": {
                "clear": 20,
                "light_rain": 10,
                "heavy_rain": 5,
                "fog": 1,
                "overcast": 15,
            }.get(weather, 10),
            "affects": {
                "recon": weather in ["fog", "heavy_rain"],
                "air_ops": weather in ["fog", "heavy_rain", "light_rain"],
                "artillery": weather == "heavy_rain",
                "movement": weather == "heavy_rain",
            },
        }

    def setup_game(
        self,
        map_width: float = 20,
        map_height: float = 15,
        reveal_level: int = 0,
        intel_level: int = 20
    ) -> dict:
        """Complete game setup"""
        # Initialize date/time
        date_time = self.initialize_game_date()

        # Create deployments
        player_units = self.create_player_deployment(map_width, map_height, "player")
        enemy_units = self.create_enemy_deployment(map_width, map_height, reveal_level)

        # Generate initial intel
        initial_intel = self.generate_initial_intel(enemy_units, intel_level)

        # Generate initial weather
        weather = self.create_initial_weather()

        return {
            "date_time": date_time,
            "player_units": player_units,
            "enemy_units": enemy_units,
            "initial_intel": initial_intel,
            "weather": weather,
            "map_dimensions": {
                "width": map_width,
                "height": map_height,
            },
        }


# Service instance factory
def create_initial_setup_service(seed: Optional[int] = None) -> InitialSetupService:
    return InitialSetupService(random_seed=seed)
