# Detailed SITREP Generator for Operational CPX
# Generates comprehensive Situation Reports in the play log format
from typing import Optional
from dataclasses import dataclass
from datetime import datetime
import json


@dataclass
class SITREPData:
    """Structured SITREP data"""
    turn: int
    timestamp: str
    time: str
    weather: str

    # Content sections
    overview: str
    text_map: str
    friendly_forces: list[dict]
    enemy_info: dict  # confirmed, estimated, unknown
    important_events: list[str]
    commander_order: Optional[str]
    logistics: dict

    # Additional metadata
    command_assessment: str  # Command's assessment of situation
    next_objectives: list[str]


class SITREPGenerator:
    """
    Generates detailed SITREP reports in the play log format

    Format:
    【日時】
    【テキストマップ】
    【状況】
    【味方戦力】
    【敵情報】（確認済み / 推定 / 不明）
    【重要イベント】
    【上官命令】
    """

    def __init__(self):
        pass

    def generate_sitrep(
        self,
        game_state: dict,
        order_results: list[dict],
        map_renderer,
        enemy_knowledge: Optional[dict] = None,
        commander_order: Optional[str] = None,
        events: Optional[list[dict]] = None
    ) -> dict:
        """Generate a complete SITREP from game state"""

        if enemy_knowledge is None:
            enemy_knowledge = {"confirmed": [], "estimated": [], "unknown": []}

        # Extract game state
        turn = game_state.get("turn", 1)
        time_str = game_state.get("time", "06:00")
        weather = game_state.get("weather", "clear")
        units = game_state.get("units", [])

        # Separate friendly and enemy units
        friendly_units = [u for u in units if u.get("side") == "player"]
        enemy_units = [u for u in units if u.get("side") == "enemy"]

        # Generate text map
        text_map = self._generate_text_map(map_renderer, units, enemy_knowledge)

        # Generate overview
        overview = self._generate_overview(
            turn, time_str, weather, friendly_units, enemy_units
        )

        # Generate friendly forces summary
        friendly_summary = self._generate_friendly_summary(friendly_units)

        # Generate enemy info
        enemy_info = self._generate_enemy_info(enemy_units, enemy_knowledge)

        # Generate important events
        important_events = self._generate_events(order_results, events)

        # Generate logistics
        logistics = self._generate_logistics(friendly_units)

        # Generate command assessment
        command_assessment = self._generate_command_assessment(
            friendly_units, enemy_units
        )

        # Generate next objectives
        next_objectives = self._generate_next_objectives(
            turn, command_assessment
        )

        sitrep = SITREPData(
            turn=turn,
            timestamp=datetime.utcnow().isoformat(),
            time=time_str,
            weather=weather,
            overview=overview,
            text_map=text_map,
            friendly_forces=friendly_summary,
            enemy_info=enemy_info,
            important_events=important_events,
            commander_order=commander_order,
            logistics=logistics,
            command_assessment=command_assessment,
            next_objectives=next_objectives
        )

        return self._format_sitrep(sitrep)

    def _generate_text_map(
        self,
        map_renderer,
        units: list[dict],
        enemy_knowledge: dict
    ) -> str:
        """Generate the text map section"""
        if map_renderer is None:
            return "Map not available"

        # Create player knowledge mapping
        player_knowledge = {}
        for enemy_id in enemy_knowledge.get("confirmed", []):
            player_knowledge[enemy_id] = "confirmed"
        for enemy_id in enemy_knowledge.get("estimated", []):
            player_knowledge[enemy_id] = "estimated"
        for enemy_id in enemy_knowledge.get("unknown", []):
            player_knowledge[enemy_id] = "unknown"

        return map_renderer.render_map(units, player_knowledge)

    def _generate_overview(
        self,
        turn: int,
        time_str: str,
        weather: str,
        friendly_units: list[dict],
        enemy_units: list[dict]
    ) -> str:
        """Generate the overview section"""
        weather_desc = self._get_weather_description(weather)

        # Count units by status
        friendly_intact = sum(1 for u in friendly_units if u.get("status") == "intact")
        enemy_intact = sum(1 for u in enemy_units if u.get("status") == "intact")

        lines = [
            f"ターン {turn} - {time_str}",
            f"天候: {weather_desc}",
            f"味方は{friendly_intact}/{len(friendly_units)}個師団が作戦可能",
            f"敵は{enemy_intact}/{len(enemy_units)}個師団が行動可能"
        ]

        return "\n".join(lines)

    def _generate_friendly_summary(self, units: list[dict]) -> list[dict]:
        """Generate friendly forces summary"""
        summary = []

        for unit in units:
            status = unit.get("status", "intact")
            ammo = unit.get("ammo", "full")
            fuel = unit.get("fuel", "full")

            summary.append({
                "name": unit.get("name", "Unknown"),
                "type": unit.get("type", "infantry"),
                "status": status,
                "ammo": ammo,
                "fuel": fuel,
                "position": {"x": unit.get("x"), "y": unit.get("y")}
            })

        return summary

    def _generate_enemy_info(self, enemy_units: list[dict], enemy_knowledge: dict) -> dict:
        """Generate enemy information with confidence levels"""
        confirmed = []
        estimated = []
        unknown = []

        for unit in enemy_units:
            unit_id = unit.get("id")
            if unit_id in enemy_knowledge.get("confirmed", []):
                confirmed.append({
                    "name": unit.get("name", "Unknown"),
                    "type": unit.get("type", "enemy"),
                    "position": {"x": unit.get("x"), "y": unit.get("y")},
                    "status": unit.get("status", "unknown")
                })
            elif unit_id in enemy_knowledge.get("estimated", []):
                estimated.append({
                    "type": unit.get("type", "enemy"),
                    "estimated_position": {"x": unit.get("x"), "y": unit.get("y")}
                })
            else:
                unknown.append({
                    "type": "enemy"
                })

        return {
            "confirmed": confirmed,
            "estimated": estimated,
            "unknown": unknown
        }

    def _generate_events(
        self,
        order_results: list[dict],
        events: Optional[list[dict]]
    ) -> list[str]:
        """Generate important events list"""
        important = []

        # Process order results
        for result in order_results:
            outcome = result.get("outcome", "unknown")
            unit_name = result.get("unit_name", "Unknown")

            if outcome == "success":
                important.append(f"{unit_name} 任務成功")
            elif outcome == "partial":
                important.append(f"{unit_name} 部分的成功")
            elif outcome == "failed":
                important.append(f"{unit_name} 任務失敗")

        # Process additional events
        if events:
            for event in events:
                event_type = event.get("type", "unknown")
                if event_type == "enemy_move":
                    important.append("敵部隊移動確認")
                elif event_type == "combat":
                    important.append("戦闘発生")

        return important

    def _generate_logistics(self, units: list[dict]) -> dict:
        """Generate logistics summary"""
        ammo_full = sum(1 for u in units if u.get("ammo") == "full")
        ammo_depleted = sum(1 for u in units if u.get("ammo") == "depleted")
        ammo_exhausted = sum(1 for u in units if u.get("ammo") == "exhausted")

        fuel_full = sum(1 for u in units if u.get("fuel") == "full")
        fuel_depleted = sum(1 for u in units if u.get("fuel") == "depleted")
        fuel_exhausted = sum(1 for u in units if u.get("fuel") == "exhausted")

        return {
            "ammo": {
                "full": ammo_full,
                "depleted": ammo_depleted,
                "exhausted": ammo_exhausted
            },
            "fuel": {
                "full": fuel_full,
                "depleted": fuel_depleted,
                "exhausted": fuel_exhausted
            }
        }

    def _generate_command_assessment(
        self,
        friendly_units: list[dict],
        enemy_units: list[dict]
    ) -> str:
        """Generate command's assessment"""
        friendly_strength = sum(u.get("strength", 0) for u in friendly_units)
        enemy_strength = sum(u.get("strength", 0) for u in enemy_units)

        if friendly_strength > enemy_strength * 1.5:
            return "有利 - 戦力的優位にある"
        elif friendly_strength > enemy_strength:
            return "やや有利 - 概ね戦力的優位"
        elif friendly_strength == enemy_strength:
            return "均衡 - 戦況は五分"
        elif friendly_strength * 1.5 < enemy_strength:
            return "不利 - 敵が戦力的優位にある"
        else:
            return "やや不利 - 敵優位だが対抗可能"

    def _generate_next_objectives(
        self,
        turn: int,
        assessment: str
    ) -> list[str]:
        """Generate next objectives"""
        objectives = []

        if "有利" in assessment:
            objectives.append("敵主力への追撃")
            objectives.append("確保地域の拡大")
        elif "不利" in assessment:
            objectives.append("防線の構築")
            objectives.append("兵力の集結")
        else:
            objectives.append("敵の意図の探知")
            objectives.append("戦術的優位の確立")

        objectives.append("補給線の確保")

        return objectives

    def _get_weather_description(self, weather: str) -> str:
        """Get Japanese weather description"""
        weather_map = {
            "clear": "快晴",
            "cloudy": "曇天",
            "rain": "降雨",
            "storm": "嵐",
            "fog": "霧",
            "snow": "降雪"
        }
        return weather_map.get(weather, weather)

    def _format_sitrep(self, sitrep: SITREPData) -> dict:
        """Format SITREP data as dictionary for storage"""

        # Format enemy info for display
        enemy_lines = []
        enemy_lines.append("【確認済み】")
        for e in sitrep.enemy_info.get("confirmed", []):
            enemy_lines.append(f"  - {e.get('name')}: {e.get('type')} @ ({e.get('position', {}).get('x')}, {e.get('position', {}).get('y')})")

        enemy_lines.append("【推定】")
        for e in sitrep.enemy_info.get("estimated", []):
            enemy_lines.append(f"  - {e.get('type')} @ ({e.get('estimated_position', {}).get('x')}, {e.get('estimated_position', {}).get('y')})")

        enemy_lines.append("【不明】")
        enemy_lines.append(f"  - {len(sitrep.enemy_info.get('unknown', []))} 個大隊")

        # Format friendly forces
        friendly_lines = []
        for f in sitrep.friendly_forces:
            status_icon = {"intact": "○", "light_damage": "△", "medium_damage": "◐", "heavy_damage": "◑", "destroyed": "×"}.get(f.get("status"), "?")
            friendly_lines.append(f"  {status_icon} {f.get('name')}: {f.get('type')} ({f.get('status')})")

        # Format events
        event_lines = [f"  - {e}" for e in sitrep.important_events]

        # Format logistics
        log = sitrep.logistics
        logistics_lines = [
            f"  弾薬: 充足{log['ammo']['full']}, 低下{log['ammo']['depleted']}, 枯渇{log['ammo']['exhausted']}",
            f"  燃料: 充足{log['fuel']['full']}, 低下{log['fuel']['depleted']}, 枯渇{log['fuel']['exhausted']}"
        ]

        # Format objectives
        objective_lines = [f"  {i+1}. {obj}" for i, obj in enumerate(sitrep.next_objectives)]

        # Build full text
        full_text = f"""【日時】
{sitrep.turn}ターン {sitrep.time} 天候: {self._get_weather_description(sitrep.weather)}

【テキストマップ】
{sitrep.text_map}

【状況】
{sitrep.overview}

【味方戦力】
{chr(10).join(friendly_lines)}

【敵情報】
{chr(10).join(enemy_lines)}

【重要イベント】
{chr(10).join(event_lines) if event_lines else '  特記事項なし'}

【上官命令】
{sitrep.commander_order if sitrep.commander_order else 'なし'}

【戦力判定】
{sitrep.command_assessment}

【次ターンの目標】
{chr(10).join(objective_lines)}

【補給状況】
{chr(10).join(logistics_lines)}"""

        return {
            "turn": sitrep.turn,
            "timestamp": sitrep.timestamp,
            "sections": {
                "overview": sitrep.overview,
                "text_map": sitrep.text_map,
                "friendly_forces": sitrep.friendly_forces,
                "enemy_info": sitrep.enemy_info,
                "important_events": sitrep.important_events,
                "commander_order": sitrep.commander_order,
                "logistics": sitrep.logistics,
                "command_assessment": sitrep.command_assessment,
                "next_objectives": sitrep.next_objectives
            },
            "full_text": full_text
        }


# Global instance
_sitrep_generator = SITREPGenerator()


def get_sitrep_generator() -> SITREPGenerator:
    """Get the global SITREP generator"""
    return _sitrep_generator
