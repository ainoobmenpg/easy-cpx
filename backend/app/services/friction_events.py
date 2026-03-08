# Friction Events Service
# Handles random friction events that affect operations
import random
from typing import Optional
from datetime import datetime


class FrictionEventType:
    MISFIRE = "misfire"  # 誤射
    COMMUNICATION_FAILURE = "communication_failure"  # 通信障害
    MAINTENANCE_ISSUE = "maintenance_issue"  # 整備不良
    WEATHER_DETERIORATION = "weather_deterioration"  # 天候悪化
    UNIT_ERROR = "unit_error"  # 部隊錯誤
    SUPPLY_DELAY = "supply_delay"  # 補給遅延
    UNEXPECTED_CONTACT = "unexpected_contact"  # 計画外接触


class FrictionEventService:
    """Service for generating and managing friction events"""

    # Base probability per turn (can be modified by conditions)
    BASE_PROBABILITY = 0.15

    def __init__(self, random_seed: Optional[int] = None):
        if random_seed is not None:
            random.seed(random_seed)

    def should_generate_event(self, turn_number: int, conditions: dict = None) -> bool:
        """Determine if a friction event should occur this turn"""
        base_chance = self.BASE_PROBABILITY

        # Modify probability based on conditions
        if conditions:
            if conditions.get("night"):
                base_chance += 0.05
            if conditions.get("bad_weather"):
                base_chance += 0.1
            if conditions.get("high_intensity"):
                base_chance += 0.1
            if conditions.get("urban_terrain"):
                base_chance += 0.05
            if conditions.get("first_turn"):
                base_chance -= 0.1  # Less friction at start

        return random.random() < base_chance

    def generate_event(self, game_state: dict) -> dict:
        """Generate a random friction event"""
        event_types = [
            FrictionEventType.MISFIRE,
            FrictionEventType.COMMUNICATION_FAILURE,
            FrictionEventType.MAINTENANCE_ISSUE,
            FrictionEventType.WEATHER_DETERIORATION,
            FrictionEventType.UNIT_ERROR,
            FrictionEventType.SUPPLY_DELAY,
            FrictionEventType.UNEXPECTED_CONTACT,
        ]

        event_type = random.choice(event_types)
        return self._create_event(event_type, game_state)

    def _create_event(self, event_type: str, game_state: dict) -> dict:
        """Create a specific friction event with details"""
        event_templates = {
            FrictionEventType.MISFIRE: {
                "title": "誤射事件",
                "description": "視界不良のため、味方部隊が味方を誤射しました。",
                "severity": random.choice(["low", "medium", "high"]),
                "effects": {
                    "unit_damage": random.randint(10, 30),
                    "morale_impact": random.randint(5, 15),
                },
                "requires_report": True,
            },
            FrictionEventType.COMMUNICATION_FAILURE: {
                "title": "通信障害",
                "description": "電子戦妨害により、通信が遮断されました。",
                "severity": random.choice(["low", "medium"]),
                "effects": {
                    "command_delay": random.randint(1, 3),
                    "recon_penalty": random.randint(10, 20),
                },
                "requires_report": True,
            },
            FrictionEventType.MAINTENANCE_ISSUE: {
                "title": "整備不良",
                "description": "複数の車両で整備不良が発生しました。",
                "severity": random.choice(["low", "medium", "high"]),
                "effects": {
                    "unit_strength_loss": random.randint(5, 20),
                    "readiness_decrease": random.choice([True, False]),
                },
                "requires_report": False,
            },
            FrictionEventType.WEATHER_DETERIORATION: {
                "title": "天候悪化",
                "description": "天候が急変し、作戦行動が困難になっています。",
                "severity": random.choice(["medium", "high"]),
                "effects": {
                    "visibility_reduction": random.randint(20, 40),
                    "movement_penalty": random.randint(10, 30),
                },
                "requires_report": True,
            },
            FrictionEventType.UNIT_ERROR: {
                "title": "部隊錯誤",
                "description": "部隊が誤った位置に移動していました。",
                "severity": random.choice(["low", "medium"]),
                "effects": {
                    "delay_turns": random.randint(1, 2),
                    "position_exposed": random.choice([True, False]),
                },
                "requires_report": False,
            },
            FrictionEventType.SUPPLY_DELAY: {
                "title": "補給遅延",
                "description": "補給隊が道路状況で到着が遅れています。",
                "severity": random.choice(["low", "medium"]),
                "effects": {
                    "supply_delay_turns": random.randint(1, 3),
                    "fuel_decrease": random.choice([True, False]),
                },
                "requires_report": True,
            },
            FrictionEventType.UNEXPECTED_CONTACT: {
                "title": "計画外接触",
                "description": "敵と予期せぬ場所で接触しました。",
                "severity": random.choice(["medium", "high"]),
                "effects": {
                    "combat_initiated": True,
                    "position_revealed": True,
                },
                "requires_report": True,
            },
        }

        event = event_templates[event_type].copy()
        event["type"] = event_type
        event["turn"] = game_state.get("current_turn", 1)
        event["timestamp"] = datetime.utcnow().isoformat()

        return event

    def apply_event_effects(self, game_state: dict, event: dict) -> dict:
        """Apply friction event effects to game state"""
        effects = event.get("effects", {})
        modified_state = game_state.copy()

        # Apply effects based on event type
        if event["type"] == FrictionEventType.MISFIRE:
            # Apply damage to a random friendly unit
            if "units" in modified_state:
                friendly_units = [u for u in modified_state["units"] if u.get("side") == "player"]
                if friendly_units:
                    unit = random.choice(friendly_units)
                    unit["strength"] = max(0, unit.get("strength", 100) - effects.get("unit_damage", 0))

        elif event["type"] == FrictionEventType.COMMUNICATION_FAILURE:
            # Reduce command efficiency
            modified_state["command_efficiency"] = modified_state.get("command_efficiency", 100) - effects.get("recon_penalty", 0)

        elif event["type"] == FrictionEventType.MAINTENANCE_ISSUE:
            # Reduce unit strength
            if "units" in modified_state:
                friendly_units = [u for u in modified_state["units"] if u.get("side") == "player"]
                if friendly_units:
                    unit = random.choice(friendly_units)
                    unit["strength"] = max(0, unit.get("strength", 100) - effects.get("unit_strength_loss", 0))

        elif event["type"] == FrictionEventType.WEATHER_DETERIORATION:
            # Worsen weather
            weather_order = ["clear", "light_rain", "heavy_rain", "fog", "snow"]
            current_weather = modified_state.get("weather", "clear")
            if current_weather in weather_order:
                idx = weather_order.index(current_weather)
                if idx < len(weather_order) - 1:
                    modified_state["weather"] = weather_order[idx + 1]

        elif event["type"] == FrictionEventType.SUPPLY_DELAY:
            # Reduce supply levels
            if "units" in modified_state:
                friendly_units = [u for u in modified_state["units"] if u.get("side") == "player"]
                if friendly_units:
                    unit = random.choice(friendly_units)
                    if effects.get("fuel_decrease"):
                        unit["fuel"] = "depleted"

        # Add event to game log
        if "friction_events" not in modified_state:
            modified_state["friction_events"] = []
        modified_state["friction_events"].append(event)

        return modified_state


# Service instance factory
def create_friction_event_service(seed: Optional[int] = None) -> FrictionEventService:
    return FrictionEventService(random_seed=seed)
