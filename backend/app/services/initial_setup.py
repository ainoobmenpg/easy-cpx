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

    # Default values (used when no scenario is provided)
    DEFAULT_START_DATE = "2026-03-06"
    DEFAULT_START_TIME = "05:40"
    DEFAULT_SCENARIO_DURATION_HOURS = 72

    # Time progression per turn (minutes)
    TIME_ADVANCE_NORMAL = 15
    TIME_ADVANCE_URGENT = 5
    TIME_ADVANCE_EXTENDED = 60

    def __init__(self, random_seed: Optional[int] = None):
        if random_seed is not None:
            random.seed(random_seed)

    def initialize_game_date(
        self,
        start_date: str = None,
        start_time: str = None,
        scenario: dict = None
    ) -> dict:
        """Initialize game date and time

        Args:
            start_date: Override start date (YYYY-MM-DD)
            start_time: Override start time (HH:MM)
            scenario: Scenario dictionary with start_date, start_time, scenario_duration_hours
        """
        # Use scenario values if provided, otherwise use defaults or overrides
        if scenario:
            date = start_date or scenario.get("start_date", self.DEFAULT_START_DATE)
            time = start_time or scenario.get("start_time", self.DEFAULT_START_TIME)
            duration = scenario.get("scenario_duration_hours", self.DEFAULT_SCENARIO_DURATION_HOURS)
        else:
            date = start_date or self.DEFAULT_START_DATE
            time = start_time or self.DEFAULT_START_TIME
            duration = self.DEFAULT_SCENARIO_DURATION_HOURS

        return {
            "date": date,
            "time": time,
            "scenario_duration_hours": duration,
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
        side: str = "player",
        scenario: dict = None
    ) -> list:
        """Create initial player deployment

        Deployment zone is determined by scenario or defaults to defensive positions.

        Args:
            map_width: Width of the map
            map_height: Height of the map
            side: "player" or "enemy"
            scenario: Scenario dictionary with deployment configuration
        """
        units = []

        # Israel northern border deployment zone
        # Main defensive line around Y: 28-32, X: 5-15
        defensive_line_y_base = 30  # Center of deployment area

        # Armor units - forward positions
        units.extend([
            {
                "name": "Alpha Company",
                "unit_type": "nato_armor",
                "side": side,
                "x": 6 + random.uniform(-1, 1),
                "y": 32 + random.uniform(-2, 2),
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
                "x": 10 + random.uniform(-1, 1),
                "y": 28 + random.uniform(-2, 2),
                "status": "intact",
                "strength": 100,
                "ammo": "full",
                "fuel": "full",
                "readiness": "full",
                "deployment_zone": DeploymentZone.FRONT_LINE.value,
            },
        ])

        # Infantry battalions
        units.extend([
            {
                "name": "1st Battalion",
                "unit_type": "nato_infantry",
                "side": side,
                "x": 8 + random.uniform(-1, 1),
                "y": 30 + random.uniform(-2, 2),
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
                "x": 12 + random.uniform(-1, 1),
                "y": 28 + random.uniform(-2, 2),
                "status": "intact",
                "strength": 100,
                "ammo": "full",
                "fuel": "full",
                "readiness": "full",
                "deployment_zone": DeploymentZone.SECOND_LINE.value,
            },
        ])

        # Artillery - rear positions
        units.extend([
            {
                "name": "Artillery Battery A",
                "unit_type": "nato_artillery",
                "side": side,
                "x": 5 + random.uniform(-0.5, 0.5),
                "y": 28 + random.uniform(-1, 1),
                "status": "intact",
                "strength": 100,
                "ammo": "full",
                "fuel": "full",
                "readiness": "full",
                "deployment_zone": DeploymentZone.SECOND_LINE.value,
            },
        ])

        # Air defense - rear protection
        units.extend([
            {
                "name": "Air Defense Platoon",
                "unit_type": "nato_air_defense",
                "side": side,
                "x": 4 + random.uniform(-0.5, 0.5),
                "y": 30 + random.uniform(-1, 1),
                "status": "intact",
                "strength": 100,
                "ammo": "full",
                "fuel": "full",
                "readiness": "full",
                "deployment_zone": DeploymentZone.REAR.value,
            },
        ])

        # Recon units - forward scout positions
        units.extend([
            {
                "name": "Recon Platoon",
                "unit_type": "nato_recon",
                "side": side,
                "x": 14 + random.uniform(-1, 1),
                "y": 30 + random.uniform(-2, 2),
                "status": "intact",
                "strength": 100,
                "ammo": "full",
                "fuel": "full",
                "readiness": "full",
                "deployment_zone": DeploymentZone.FRONT_LINE.value,
                "recon_value": 1.3,
                "visibility_range": 5,
                "infantry_subtype": "scout",
            },
        ])

        return units

    def create_uav_deployment(
        self,
        map_width: float,
        map_height: float,
        side: str = "player",
        scenario: dict = None
    ) -> list:
        """Create UAV units for modern scenarios

        UAVs provide large reconnaissance coverage but have no combat capability

        Args:
            map_width: Width of the map
            map_height: Height of the map
            side: "player" or "enemy"
            scenario: Scenario dictionary for scenario-based configuration
        """
        units = []

        # UAV deployment - operates from rear area but has long range
        if side == "player":
            units.extend([
                {
                    "name": "Shadow UAV",
                    "unit_type": "nato_uav",
                    "side": side,
                    "x": 3 + random.uniform(-0.5, 0.5),
                    "y": 25 + random.uniform(-3, 3),
                    "status": "intact",
                    "strength": 100,
                    "ammo": "full",
                    "fuel": "full",
                    "readiness": "full",
                    "deployment_zone": DeploymentZone.REAR.value,
                    "recon_value": 1.5,
                    "visibility_range": 8,
                    "notes": "Tactical UAV, reconnaissance only",
                },
                {
                    "name": "Reaper UAV",
                    "unit_type": "nato_uav",
                    "side": side,
                    "x": 2 + random.uniform(-0.5, 0.5),
                    "y": 35 + random.uniform(-3, 3),
                    "status": "intact",
                    "strength": 100,
                    "ammo": "full",
                    "fuel": "full",
                    "readiness": "full",
                    "deployment_zone": DeploymentZone.REAR.value,
                    "recon_value": 1.8,
                    "visibility_range": 10,
                    "notes": "Medium-altitude UAV, reconnaissance only",
                },
            ])
        else:
            # Enemy UAV
            units.extend([
                {
                    "name": "Enemy UAV",
                    "unit_type": "wp_uav",
                    "side": side,
                    "x": 45 + random.uniform(-2, 2),
                    "y": 28 + random.uniform(-3, 3),
                    "status": "intact",
                    "strength": 100,
                    "ammo": "full",
                    "fuel": "full",
                    "readiness": "full",
                    "deployment_zone": DeploymentZone.REAR.value,
                    "recon_value": 1.3,
                    "visibility_range": 7,
                    "is_concealed": True,
                    "detection_difficulty": 40,
                },
            ])

        return units

    def create_enemy_deployment(
        self,
        map_width: float,
        map_height: float,
        reveal_level: int = 0,
        scenario: dict = None
    ) -> list:
        """Create enemy deployment with concealment rules

        Enemy deployment zone is based on scenario or defaults to standard positions.

        Args:
            map_width: Width of the map
            map_height: Height of the map
            reveal_level: 0-100, how much info is available to player
            scenario: Scenario dictionary with deployment configuration
        """
        units = []

        # Enemy deployment zone in Lebanon - X: 25-40, Y: 20-35
        base_x_min = 28  # Start of concealment zone
        base_x_max = 40  # End of enemy deployment
        base_y_min = 22
        base_y_max = 34

        # Armor units - main strike force
        for i in range(3):
            unit = {
                "name": f"Enemy Tank Company {i+1}",
                "unit_type": "wp_armor",
                "side": "enemy",
                "x": 30 + random.uniform(0, 8),
                "y": base_y_min + random.uniform(0, base_y_max - base_y_min),
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

        # Infantry - second line
        for i in range(2):
            unit = {
                "name": f"Enemy Motor Rifle {i+1}",
                "unit_type": "wp_infantry",
                "side": "enemy",
                "x": 28 + random.uniform(0, 6),
                "y": base_y_min + random.uniform(0, base_y_max - base_y_min),
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

        # Artillery - rear fire support
        unit = {
            "name": "Enemy Artillery Regiment",
            "unit_type": "wp_artillery",
            "side": "enemy",
            "x": 38 + random.uniform(0, 4),
            "y": 28 + random.uniform(-3, 3),
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

        # Air defense - distributed coverage
        for i in range(2):
            unit = {
                "name": f"Enemy SAM {i+1}",
                "unit_type": "wp_air_defense",
                "side": "enemy",
                "x": 36 + random.uniform(0, 4),
                "y": 26 + random.uniform(-3, 5),
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

    def create_initial_weather(self, scenario: dict = None) -> dict:
        """Generate initial weather conditions

        Args:
            scenario: Scenario dictionary with initial_weather override
        """
        # Use scenario weather if specified
        if scenario and scenario.get("initial_weather"):
            weather = scenario["initial_weather"]
        else:
            weather_types = [
                "clear",
                "light_rain",
                "heavy_rain",
                "fog",
                "overcast",
            ]
            # Default weights - slight bias to fog and overcast
            weights = [0.2, 0.2, 0.1, 0.3, 0.2]
            weather = random.choices(weather_types, weights=weights)[0]

        return {
            "type": weather,
            "temperature": random.randint(-5, 10),
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
        map_width: float = 50,
        map_height: float = 50,
        reveal_level: int = 0,
        intel_level: int = 20,
        include_uav: bool = True,
        scenario: dict = None
    ) -> dict:
        """Complete game setup

        Args:
            map_width: Width of the map
            map_height: Height of the map
            reveal_level: 0-100, how much enemy info is available
            intel_level: 0-100, player's initial intel quality
            include_uav: Whether to include UAV units (modern scenario)
            scenario: Scenario dictionary for scenario-based configuration
        """
        # Initialize date/time (scenario-aware)
        date_time = self.initialize_game_date(scenario=scenario)

        # Create deployments
        player_units = self.create_player_deployment(map_width, map_height, "player")
        enemy_units = self.create_enemy_deployment(map_width, map_height, reveal_level)

        # Add UAV units for modern scenarios
        if include_uav:
            player_uavs = self.create_uav_deployment(map_width, map_height, "player")
            enemy_uavs = self.create_uav_deployment(map_width, map_height, "enemy")
            player_units.extend(player_uavs)
            enemy_units.extend(enemy_uavs)

        # Generate initial intel
        initial_intel = self.generate_initial_intel(enemy_units, intel_level)

        # Generate initial weather (scenario-aware)
        weather = self.create_initial_weather(scenario)

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
            "include_uav": include_uav,
        }


# Service instance factory
def create_initial_setup_service(seed: Optional[int] = None) -> InitialSetupService:
    return InitialSetupService(random_seed=seed)
