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
  "target_units": ["unit_id_or_name"],
  "intent": "what the player wants to accomplish",
  "location": {{"x": 0-50, "y": 0-50, "area_name": "optional"}},
  "parameters": {{"priority": "high|normal|low"}},
  "assumptions": ["any ambiguities assumed"]
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

Generate simple tactical orders for enemy units. Be aggressive but realistic.

Output ONLY valid JSON:
{{
  "orders": [
    {{"unit_id": "id", "order_type": "move|attack|defend|retreat", "target": {{"x": 0-50, "y": 0-50}}}}
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
        enemy_units = [u for u in game_state.get('units', []) if u.get('side') == 'enemy']

        orders = []
        for unit in enemy_units[:3]:  # Limit to 3 units
            orders.append({
                "unit_id": unit.get("id"),
                "order_type": "move",
                "target": {
                    "x": unit.get("x", 25) + 5,
                    "y": unit.get("y", 25)
                }
            })

        return {"orders": orders}
