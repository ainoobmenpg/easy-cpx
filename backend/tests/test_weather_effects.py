# Tests for Weather Effects Service
import pytest
from app.services.weather_effects import WeatherType, TimeOfDay, WeatherEffects


class TestWeatherEffects:
    def test_set_weather(self):
        """Test setting weather"""
        effects = WeatherEffects()
        effects.set_weather("rain")
        assert effects._current_weather == WeatherType.RAIN

    def test_set_time(self):
        """Test setting time"""
        effects = WeatherEffects()
        effects.set_time("14:00")
        assert effects._current_time == "14:00"

    def test_get_time_of_day_day(self):
        """Test time of day is DAY"""
        effects = WeatherEffects()
        effects.set_time("12:00")
        assert effects.get_time_of_day() == TimeOfDay.DAY

    def test_get_time_of_day_night(self):
        """Test time of day is NIGHT"""
        effects = WeatherEffects()
        effects.set_time("20:00")
        assert effects.get_time_of_day() == TimeOfDay.NIGHT

    def test_get_time_of_day_dawn(self):
        """Test time of day is DAWN"""
        effects = WeatherEffects()
        effects.set_time("06:00")
        assert effects.get_time_of_day() == TimeOfDay.DAWN

    def test_get_time_of_day_dusk(self):
        """Test time of day is DUSK"""
        effects = WeatherEffects()
        effects.set_time("18:00")
        assert effects.get_time_of_day() == TimeOfDay.DUSK

    def test_combined_reconnaissance_modifier_clear(self):
        """Test reconnaissance modifier in clear weather"""
        effects = WeatherEffects()
        effects.set_weather("clear")
        effects.set_time("12:00")
        modifier = effects.get_combined_reconnaissance_modifier()
        assert modifier == 1.0

    def test_combined_reconnaissance_modifier_rain(self):
        """Test reconnaissance modifier in rain"""
        effects = WeatherEffects()
        effects.set_weather("rain")
        effects.set_time("12:00")
        modifier = effects.get_combined_reconnaissance_modifier()
        assert modifier < 1.0

    def test_combined_reconnaissance_modifier_night(self):
        """Test reconnaissance modifier at night without NOD"""
        effects = WeatherEffects()
        effects.set_weather("clear")
        effects.set_time("22:00")
        # Clear weather dominates, so modifier is 1.0
        modifier = effects.get_combined_reconnaissance_modifier(has_nod=False)
        assert modifier == 1.0

    def test_combined_combat_modifier(self):
        """Test combat modifier calculation"""
        effects = WeatherEffects()
        effects.set_weather("clear")
        effects.set_time("12:00")
        modifier = effects.get_combined_combat_modifier()
        assert modifier > 0

    def test_combined_movement_modifier(self):
        """Test movement modifier calculation"""
        effects = WeatherEffects()
        effects.set_weather("clear")
        effects.set_time("12:00")
        modifier = effects.get_combined_movement_modifier()
        assert modifier > 0

    def test_artillery_observation_modifier(self):
        """Test artillery observation modifier"""
        effects = WeatherEffects()
        effects.set_weather("fog")
        modifier = effects.get_artillery_observation_modifier()
        assert modifier < 1.0

    def test_air_operation_modifier(self):
        """Test air operation modifier"""
        effects = WeatherEffects()
        effects.set_weather("storm")
        modifier = effects.get_air_operation_modifier()
        assert modifier < 1.0

    def test_effects_summary(self):
        """Test getting effects summary"""
        effects = WeatherEffects()
        effects.set_weather("clear")
        effects.set_time("12:00")
        summary = effects.get_current_effects_summary()
        assert "weather" in summary
        assert "time" in summary
        assert "reconnaissance_modifier" in summary


class TestWeatherTypes:
    def test_clear_weather(self):
        """Test clear weather effects"""
        effect = WeatherEffects.WEATHER_EFFECTS[WeatherType.CLEAR]
        assert effect.reconnaissance_modifier == 1.0

    def test_rain_weather(self):
        """Test rain weather effects"""
        effect = WeatherEffects.WEATHER_EFFECTS[WeatherType.RAIN]
        assert effect.reconnaissance_modifier == 0.6
        assert effect.movement_modifier == 0.8

    def test_fog_weather(self):
        """Test fog weather effects"""
        effect = WeatherEffects.WEATHER_EFFECTS[WeatherType.FOG]
        assert effect.reconnaissance_modifier == 0.4

    def test_storm_weather(self):
        """Test storm weather effects"""
        effect = WeatherEffects.WEATHER_EFFECTS[WeatherType.STORM]
        assert effect.air_operation_modifier == 0.4


class TestTimeEffects:
    def test_day_time(self):
        """Test daytime effects"""
        effect = WeatherEffects.TIME_EFFECTS[TimeOfDay.DAY]
        assert effect.visibility_modifier == 1.0
        assert effect.requires_nod is False

    def test_night_time(self):
        """Test nighttime effects"""
        effect = WeatherEffects.TIME_EFFECTS[TimeOfDay.NIGHT]
        assert effect.visibility_modifier == 0.3
        assert effect.requires_nod is True
