# Weather and Night Effects for Operational CPX
# Implements environmental effects on combat, reconnaissance, and movement
from enum import Enum
from dataclasses import dataclass
from typing import Optional


class WeatherType(Enum):
    """Weather conditions"""
    CLEAR = "clear"
    CLOUDY = "cloudy"
    RAIN = "rain"
    STORM = "storm"
    FOG = "fog"
    SANDSTORM = "sandstorm"
    SNOW = "snow"


class TimeOfDay(Enum):
    """Time of day categories"""
    DAY = "day"           # 06:00 - 18:00
    NIGHT = "night"       # 18:00 - 06:00
    DAWN = "dawn"         # 05:00 - 07:00
    DUSK = "dusk"         # 17:00 - 19:00


@dataclass
class WeatherEffect:
    """Effects of weather on various operations"""
    reconnaissance_modifier: float  # 0.0 - 1.0
    air_operation_modifier: float
    artillery_observation_modifier: float
    movement_modifier: float
    combat_modifier: float
    description: str


@dataclass
class TimeEffect:
    """Effects of time of day"""
    visibility_modifier: float  # 0.0 - 1.0
    movement_modifier: float
    combat_modifier: float
    requires_nod: bool  # NOD (Night Observation Device) required
    description: str


class WeatherEffects:
    """
    Manages weather and time-of-day effects on operations

    Effects:
    - Night: NOD devices affect effectiveness
    - Rain/Fog/Sandstorm: Affects reconnaissance, air ops, artillery
    """

    # Weather effect modifiers
    WEATHER_EFFECTS = {
        WeatherType.CLEAR: WeatherEffect(
            reconnaissance_modifier=1.0,
            air_operation_modifier=1.0,
            artillery_observation_modifier=1.0,
            movement_modifier=1.0,
            combat_modifier=1.0,
            description="快晴 - すべての作戦に有利"
        ),
        WeatherType.CLOUDY: WeatherEffect(
            reconnaissance_modifier=0.9,
            air_operation_modifier=0.95,
            artillery_observation_modifier=0.9,
            movement_modifier=1.0,
            combat_modifier=0.95,
            description="曇天 - 偵察精度が若干低下"
        ),
        WeatherType.RAIN: WeatherEffect(
            reconnaissance_modifier=0.6,
            air_operation_modifier=0.7,
            artillery_observation_modifier=0.5,
            movement_modifier=0.8,
            combat_modifier=0.85,
            description="降雨 - 偵察と砲兵観測が大きく低下"
        ),
        WeatherType.STORM: WeatherEffect(
            reconnaissance_modifier=0.3,
            air_operation_modifier=0.4,
            artillery_observation_modifier=0.3,
            movement_modifier=0.5,
            combat_modifier=0.6,
            description="嵐 - 航空運用と偵察に大きく影響"
        ),
        WeatherType.FOG: WeatherEffect(
            reconnaissance_modifier=0.4,
            air_operation_modifier=0.5,
            artillery_observation_modifier=0.4,
            movement_modifier=0.9,
            combat_modifier=0.7,
            description="霧 - 視界と偵察に大きく影響"
        ),
        WeatherType.SANDSTORM: WeatherEffect(
            reconnaissance_modifier=0.3,
            air_operation_modifier=0.3,
            artillery_observation_modifier=0.3,
            movement_modifier=0.6,
            combat_modifier=0.6,
            description="砂塵嵐 - すべての作戦に大幅に影響"
        ),
        WeatherType.SNOW: WeatherEffect(
            reconnaissance_modifier=0.5,
            air_operation_modifier=0.6,
            artillery_observation_modifier=0.5,
            movement_modifier=0.7,
            combat_modifier=0.7,
            description="降雪 - 機動力と偵察に影響"
        )
    }

    # Time of day effects
    TIME_EFFECTS = {
        TimeOfDay.DAY: TimeEffect(
            visibility_modifier=1.0,
            movement_modifier=1.0,
            combat_modifier=1.0,
            requires_nod=False,
            description="日中 - 通常の作戦行動が可能"
        ),
        TimeOfDay.DAWN: TimeEffect(
            visibility_modifier=0.8,
            movement_modifier=0.95,
            combat_modifier=0.9,
            requires_nod=False,
            description="薄明 - 偵察に若干の不利"
        ),
        TimeOfDay.DUSK: TimeEffect(
            visibility_modifier=0.7,
            movement_modifier=0.9,
            combat_modifier=0.85,
            requires_nod=False,
            description="薄暮 - 敵の奇襲に 주의"
        ),
        TimeOfDay.NIGHT: TimeEffect(
            visibility_modifier=0.3,
            movement_modifier=0.7,
            combat_modifier=0.6,
            requires_nod=True,
            description="夜間 - NOD装置なしでは戦力大幅低下"
        )
    }

    def __init__(self):
        self._current_weather = WeatherType.CLEAR
        self._current_time = "12:00"

    def set_weather(self, weather: str):
        """Set current weather"""
        try:
            self._current_weather = WeatherType(weather.lower())
        except ValueError:
            self._current_weather = WeatherType.CLEAR

    def set_time(self, time_str: str):
        """Set current time"""
        self._current_time = time_str

    def get_time_of_day(self) -> TimeOfDay:
        """Determine time of day from time string"""
        hour = int(self._current_time.split(":")[0])

        if 5 <= hour < 7:
            return TimeOfDay.DAWN
        elif 7 <= hour < 17:
            return TimeOfDay.DAY
        elif 17 <= hour < 19:
            return TimeOfDay.DUSK
        else:
            return TimeOfDay.NIGHT

    def get_combined_reconnaissance_modifier(
        self,
        has_nod: bool = False,
        is_airborne: bool = False
    ) -> float:
        """
        Get combined reconnaissance modifier

        Args:
            has_nod: Unit has night observation device
            is_airborne: Unit is aircraft

        Returns:
            Modifier from 0.0 to 1.0
        """
        weather_effect = self.WEATHER_EFFECTS[self._current_weather]
        time_effect = self.TIME_EFFECTS[self.get_time_of_day()]

        # Base modifier from weather
        modifier = weather_effect.reconnaissance_modifier

        # Airborne units less affected by some weather
        if is_airborne:
            modifier = max(modifier, 0.7)

        # NOD helps at night
        if time_effect.requires_nod and has_nod:
            modifier = max(modifier, 0.7)

        return modifier

    def get_combined_combat_modifier(
        self,
        has_nod: bool = False,
        is_airborne: bool = False
    ) -> float:
        """Get combined combat modifier"""
        weather_effect = self.WEATHER_EFFECTS[self._current_weather]
        time_effect = self.TIME_EFFECTS[self.get_time_of_day()]

        # Base modifier from weather
        modifier = weather_effect.combat_modifier

        # Time of day effect
        if time_effect.requires_nod:
            if has_nod:
                modifier *= 0.9  # NOD helps but not perfect
            else:
                modifier *= time_effect.combat_modifier

        # Airborne units affected by weather
        if is_airborne:
            modifier *= weather_effect.air_operation_modifier

        return modifier

    def get_combined_movement_modifier(
        self,
        has_nod: bool = False,
        is_airborne: bool = False
    ) -> float:
        """Get combined movement modifier"""
        weather_effect = self.WEATHER_EFFECTS[self._current_weather]
        time_effect = self.TIME_EFFECTS[self.get_time_of_day()]

        modifier = weather_effect.movement_modifier * time_effect.movement_modifier

        return modifier

    def get_artillery_observation_modifier(self) -> float:
        """Get artillery observation modifier"""
        weather_effect = self.WEATHER_EFFECTS[self._current_weather]
        return weather_effect.artillery_observation_modifier

    def get_air_operation_modifier(self) -> float:
        """Get air operation modifier"""
        weather_effect = self.WEATHER_EFFECTS[self._current_weather]
        return weather_effect.air_operation_modifier

    def get_current_effects_summary(self) -> dict:
        """Get summary of current effects"""
        weather = self.WEATHER_EFFECTS[self._current_weather]
        time = self.TIME_EFFECTS[self.get_time_of_day()]

        return {
            "weather": self._current_weather.value,
            "time": self._current_time,
            "time_of_day": self.get_time_of_day().value,
            "weather_description": weather.description,
            "time_description": time.description,
            "reconnaissance_modifier": self.get_combined_reconnaissance_modifier(),
            "combat_modifier": self.get_combined_combat_modifier(),
            "movement_modifier": self.get_combined_movement_modifier(),
            "air_operation_modifier": self.get_air_operation_modifier(),
            "artillery_observation_modifier": self.get_artillery_observation_modifier()
        }

    def apply_to_attack(
        self,
        base_success_chance: float,
        has_nod: bool = False,
        is_airborne: bool = False
    ) -> float:
        """Apply environmental effects to attack success chance"""
        modifier = self.get_combined_combat_modifier(has_nod, is_airborne)
        return base_success_chance * modifier

    def apply_to_recon(
        self,
        base_recon_chance: float,
        has_nod: bool = False,
        is_airborne: bool = False
    ) -> float:
        """Apply environmental effects to reconnaissance"""
        modifier = self.get_combined_reconnaissance_modifier(has_nod, is_airborne)
        return base_recon_chance * modifier


# Global instance
_weather_effects = WeatherEffects()


def get_weather_effects() -> WeatherEffects:
    """Get the global weather effects system"""
    return _weather_effects
