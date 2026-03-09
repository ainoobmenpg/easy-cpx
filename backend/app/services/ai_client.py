# AI Client for MiniMax M2.5
import os
import json
import httpx
from typing import Optional


class AIClient:
    """MiniMax M2.5 client for order parsing and SITREP generation"""

    def __init__(self):
        self.api_key = os.getenv("MINIMAX_API_KEY", "")
        self.base_url = os.getenv("MINIMAX_BASE_URL", "https://api.minimax.chat/v1")

    async def parse_order(self, player_input: str, game_context: dict) -> dict:
        """Parse player order from natural language to structured JSON"""
        if not self.api_key:
            return self._fallback_parse(player_input)

        prompt = f"""You are a military order parser for a command simulation game.
Parse the player's order into a strict JSON structure.

Game context:
- Current turn: {game_context.get('turn', 1)}
- Time: {game_context.get('time', '06:00')}
- Weather: {game_context.get('weather', 'clear')}

Player input: {player_input}

Available unit types: infantry, armor, artillery, anti_tank, air_defense, reconnaissance, supply
Order types: move, attack, defend, support, retreat, recon, supply, special

Output ONLY valid JSON (no markdown, no explanation):
{{
  "order_type": "move|attack|defend|support|retreat|recon|supply|special",
  "target_units": [1, 2, 3],  # Use unit IDs (integers) only
  "intent": "what the player wants to accomplish",
  "location": {{"x": 0-50, "y": 0-50, "area_name": "optional"}},
  "parameters": {{"priority": "high|normal|low"}},
  "assumptions": ["any ambiguities assumed"]
}}

IMPORTANT: target_units must be a list of unit IDs (integers), NOT unit names. Do NOT use unit names."""

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/text/chatcompletion_v2",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "MiniMax-M2.5",
                        "messages": [
                            {"role": "system", "content": "You are a military order parser. Output ONLY valid JSON."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.3
                    },
                    timeout=30.0
                )
                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "{}")
                return json.loads(content)
        except Exception as e:
            return self._fallback_parse(player_input)

    async def generate_sitrep(self, game_state: dict, order_results: list) -> dict:
        """Generate SITREP from game state and order results"""
        if not self.api_key:
            return self._fallback_sitrep(game_state, order_results)

        prompt = f"""Generate a military Situation Report (SITREP) from the game state.

Current State:
- Turn: {game_state.get('turn', 1)}
- Time: {game_state.get('time', '06:00')}
- Weather: {game_state.get('weather', 'clear')}

Units:
{json.dumps(game_state.get('units', []), indent=2)}

Order Results:
{json.dumps(order_results, indent=2)}

Generate a SITREP with these sections:
1. overview - General situation summary
2. unit_status - Status of player units
3. enemy_activity - What enemy has done
4. logistics - Ammo, fuel, supply status
5. orders_result - How player orders resolved
6. command - Any new orders from command (if any)

Output ONLY valid JSON:
{{
  "turn": {game_state.get('turn', 1)},
  "timestamp": "ISO8601",
  "sections": [
    {{"type": "overview|unit_status|enemy_activity|logistics|orders_result|command", "content": "text", "confidence": "confirmed|estimated|unknown"}}
  ],
  "map_updates": []
}}"""

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/text/chatcompletion_v2",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "MiniMax-M2.5",
                        "messages": [
                            {"role": "system", "content": "You are a military staff officer generating SITREPs. Output ONLY valid JSON."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.5
                    },
                    timeout=30.0
                )
                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "{}")
                return json.loads(content)
        except Exception as e:
            return self._fallback_sitrep(game_state, order_results)

    async def generate_excon_orders(self, game_state: dict) -> dict:
        """Generate enemy (ExCon) orders for AI-controlled forces"""
        if not self.api_key:
            return self._fallback_excon(game_state)

        prompt = f"""Generate orders for enemy forces based on current game state.

Game State:
- Turn: {game_state.get('turn', 1)}
- Enemy units: {json.dumps([u for u in game_state.get('units', []) if u.get('side') == 'enemy'], indent=2)}
- Player units: {json.dumps([u for u in game_state.get('units', []) if u.get('side') == 'player'], indent=2)}

CRITICAL TACTICAL INSTRUCTIONS:
1. ATTACK: If any enemy unit is within 5 grid cells of a player unit, generate an ATTACK order against that player unit
2. ADVANTAGE: If enemy has numerical superiority (more units than player), generate aggressive ATTACK or MOVE orders toward player positions
3. APPROACH: All enemy units should generally move TOWARD player units (decreasing X distance toward player side at X=0-10)
4. DEFEND: If enemy is outnumbered, some units should DEFEND or RETREAT to safer positions
5. Prioritize attacking player units with LOW strength or DAMAGED status

Tactical priorities (in order):
- If player unit in range (within 5 cells) -> ATTACK
- If numerically superior -> aggressive ATTACK/MOVE toward player
- If approximately equal -> MOVE toward nearest player unit
- If inferior -> DEFEND or RETREAT slightly

Output ONLY valid JSON:
{{
  "orders": [
    {{"unit_id": "id", "order_type": "move|attack|defend|retreat", "target": {{"x": 0-50, "y": 0-50}}, "target_units": ["player_unit_id"], "intent": "tactical reason"}}
  ]
}}"""

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/text/chatcompletion_v2",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "MiniMax-M2.5",
                        "messages": [
                            {"role": "system", "content": "You are an enemy AI commander. Output ONLY valid JSON."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.7
                    },
                    timeout=30.0
                )
                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "{}")
                return json.loads(content)
        except Exception:
            return self._fallback_excon(game_state)

    # Fallback methods when API is not available
    def _fallback_parse(self, player_input: str) -> dict:
        """Simple keyword-based fallback parser"""
        input_lower = player_input.lower()
        order_type = "move"

        if "攻撃" in player_input or "attack" in input_lower:
            order_type = "attack"
        elif "防衛" in player_input or "防御" in player_input or "defend" in input_lower:
            order_type = "defend"
        elif "偵察" in player_input or "recon" in input_lower:
            order_type = "recon"
        elif "撤退" in player_input or "retreat" in input_lower:
            order_type = "retreat"
        elif "補給" in player_input or "supply" in input_lower:
            order_type = "supply"

        return {
            "order_type": order_type,
            "target_units": [],
            "intent": player_input,
            "location": None,
            "parameters": {"priority": "normal"},
            "assumptions": ["Fallback parser used - API not configured"]
        }

    def _fallback_sitrep(self, game_state: dict, order_results: list) -> dict:
        """Generate basic SITREP without AI"""
        from datetime import datetime

        player_units = [u for u in game_state.get('units', []) if u.get('side') == 'player']
        enemy_units = [u for u in game_state.get('units', []) if u.get('side') == 'enemy']

        sections = [
            {
                "type": "overview",
                "content": f"Turn {game_state.get('turn', 1)} - {game_state.get('time', '06:00')}. Weather: {game_state.get('weather', 'clear')}.",
                "confidence": "confirmed"
            },
            {
                "type": "unit_status",
                "content": f"Player forces: {len(player_units)} units. Enemy forces: {len(enemy_units)} units.",
                "confidence": "confirmed"
            },
            {
                "type": "orders_result",
                "content": f"Processed {len(order_results)} orders.",
                "confidence": "confirmed"
            }
        ]

        return {
            "turn": game_state.get('turn', 1),
            "timestamp": datetime.utcnow().isoformat(),
            "sections": sections,
            "map_updates": []
        }

    def _fallback_excon(self, game_state: dict) -> dict:
        """Generate basic enemy orders without AI"""
        import math

        enemy_units = [u for u in game_state.get('units', []) if u.get('side') == 'enemy']
        player_units = [u for u in game_state.get('units', []) if u.get('side') == 'player']

        if not enemy_units:
            return {"orders": []}

        # Calculate numerical advantage
        enemy_count = len(enemy_units)
        player_count = len(player_units)
        enemy_superior = enemy_count > player_count

        orders = []

        for unit in enemy_units:
            unit_x = unit.get("x", 25)
            unit_y = unit.get("y", 25)

            # Find nearest player unit
            nearest_player = None
            min_distance = float('inf')
            for p_unit in player_units:
                dist = math.sqrt((unit_x - p_unit.get("x", 0))**2 + (unit_y - p_unit.get("y", 25))**2)
                if dist < min_distance:
                    min_distance = dist
                    nearest_player = p_unit

            # Tactical decision making
            if nearest_player and min_distance <= 5:
                # Player in range - ATTACK!
                orders.append({
                    "unit_id": unit.get("id"),
                    "order_type": "attack",
                    "target": {
                        "x": nearest_player.get("x", 0),
                        "y": nearest_player.get("y", 25)
                    },
                    "target_units": [nearest_player.get("id")],
                    "intent": f"Attack player unit at distance {min_distance:.1f}"
                })
            elif enemy_superior:
                # Numerically superior - aggressive move toward player
                target_x = max(0, min(50, nearest_player.get("x", 0) + 3 if nearest_player else unit_x + 5))
                target_y = nearest_player.get("y", unit_y) if nearest_player else unit_y
                orders.append({
                    "unit_id": unit.get("id"),
                    "order_type": "move",
                    "target": {"x": target_x, "y": target_y},
                    "intent": "Advance toward player position"
                })
            elif nearest_player:
                # Equal or inferior - approach cautiously
                target_x = max(0, min(50, nearest_player.get("x", 0) + 2))
                orders.append({
                    "unit_id": unit.get("id"),
                    "order_type": "move",
                    "target": {"x": target_x, "y": nearest_player.get("y", unit_y)},
                    "intent": "Approach player position"
                })
            else:
                # No player units found - move forward
                orders.append({
                    "unit_id": unit.get("id"),
                    "order_type": "move",
                    "target": {"x": min(50, unit_x + 3), "y": unit_y},
                    "intent": "Advance"
                })

        return {"orders": orders[:5]}

    async def generate_debriefing_comment(self, summary: dict) -> str:
        """Generate AI commentary for debriefing"""
        if not self.api_key:
            return self._fallback_commentary(summary)

        prompt = f"""Generate a post-exercise debriefing commentary for a military command simulation.

Performance Summary:
- Total Turns: {summary.get('total_turns', 0)}
- Player Casualty Rate: {summary.get('player_casualty_rate', 0)}%
- Enemy Destruction Rate: {summary.get('enemy_destruction_rate', 0)}%
- Mission Status: {summary.get('mission_status', 'unknown')}
- Resource Issues: {summary.get('resource_issues', 0)} units with depleted resources

Generate a brief, professional military debriefing commentary (2-3 paragraphs) in Japanese.
Focus on:
1. Overall assessment of the operation
2. Key factors that influenced the outcome
3. Recommendations for future operations

Output ONLY the commentary text (no JSON, no markdown)."""

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/text/chatcompletion_v2",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "MiniMax-M2.5",
                        "messages": [
                            {"role": "system", "content": "You are a military debriefing officer. Output only commentary text in Japanese."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.5
                    },
                    timeout=30.0
                )
                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                return content if content else self._fallback_commentary(summary)
        except Exception:
            return self._fallback_commentary(summary)

    def _fallback_commentary(self, summary: dict) -> str:
        """Generate fallback commentary when AI is unavailable"""
        status = summary.get("mission_status", "unknown")
        casualties = summary.get("player_casualty_rate", 0)

        if status == "success":
            return "素晴らしい作戦でした。貴方の部隊は高い効率で任務を完遂しました。司令部は結果に満足しています。損害も許容範囲内に抑えられました。"
        elif status == "partial":
            return "作戦は部分的成功に留まりました。一部の目標は達成されましたが、他の目標は未達です。さらなる分析が必要です。"
        else:
            if casualties > 50:
                return "作戦はintended objectiveを達成できませんでした。司令部は計画と執行をreviewします。教訓は将来の作戦に組み込まれます。"
            return "作戦はintended objectiveを達成できませんでした。貴方の部隊の健闘は認められました。次に備えて準備を整えてください。"
