# Event Deck Service
# Handles strategic event deck for Operational CPX
# Each turn, there is a chance to draw and inject one event
import random
from typing import Optional, List, Dict, Any
from datetime import datetime


class EventDeckType:
    """Event deck type identifiers"""
    REINFORCEMENTS = "reinforcements"  # 増援
    ENEMY_REINFORCEMENTS = "enemy_reinforcements"  # 敵増援
    AMMO_SHORTAGE = "ammo_shortage"  # 弾薬不足
    WEATHER_CHANGE = "weather_change"  # 天候変化
    INTEL_LEAK = "intel_leak"  # 情報漏洩
    SUPPLY_INTERRUPTION = "supply_interruption"  # 補給途絶
    MORALE_BOOST = "morale_boost"  # 士気高揚
    ENEMY_MORALE_LOW = "enemy_morale_low"  # 敵士気低下
    ARTILLERY_AVAILABLE = "artillery_available"  # 砲兵火力 available
    AIR_SUPPORT_AVAILABLE = "air_support_available"  # 航空支援 available


class EventDeckService:
    """Service for managing the event deck system"""

    # Base probability of drawing an event each turn
    BASE_DRAW_CHANCE = 0.4  # 40% chance per turn

    def __init__(self, random_seed: Optional[int] = None):
        if random_seed is not None:
            random.seed(random_seed)
        self._deck: List[Dict[str, Any]] = []
        self._discard_pile: List[Dict[str, Any]] = []
        self._initialize_deck()

    def _initialize_deck(self) -> None:
        """Initialize the event deck with 10 characteristic events"""
        self._deck = [
            # 1. 増援 - Reinforcements arrive
            {
                "type": EventDeckType.REINFORCEMENTS,
                "name": "増援部隊到着",
                "description": "後方待機していた増援部隊が戦場に到着しました。",
                "presentation": "後方待機部隊より第{X}増援戦력이到着。戦力増強完了。",
                "conditions": {"min_turn": 2},
                "effects": {
                    "2d6_modifier": "+2",
                    "target": "combat",
                    "duration": 1
                },
                "rarity": "common"
            },
            # 2. 敵増援 - Enemy reinforcements
            {
                "type": EventDeckType.ENEMY_REINFORCEMENTS,
                "name": "敵増援確認",
                "description": "偵察部隊より敵増援戦力の接近が報告されました。",
                "presentation": "要注意。敵増援戦力={count}個大隊が{Z}方面から接近中。",
                "conditions": {"min_turn": 3},
                "effects": {
                    "2d6_modifier": "-1",
                    "target": "defense",
                    "duration": 1
                },
                "rarity": "common"
            },
            # 3. 弾薬不足 - Ammunition shortage
            {
                "type": EventDeckType.AMMO_SHORTAGE,
                "name": "弾薬消費率高騰",
                "description": "前三日の戦闘で弾薬の消費量が予想を上回っています。",
                "presentation": "弾薬消費率 {rate}% 超過。残弾状況要注意。",
                "conditions": {"min_turn": 2},
                "effects": {
                    "action_restriction": "artillery_limited",
                    "description": "砲兵射撃のみ1ターン制約",
                    "duration": 1
                },
                "rarity": "uncommon"
            },
            # 4. 天候変化 - Weather change
            {
                "type": EventDeckType.WEATHER_CHANGE,
                "name": "天候急変",
                "description": "気象観測により天候の急変が予測されます。",
                "presentation": "気象情報：{weather}接近中。視界・機動に影響あり。",
                "conditions": {},
                "effects": {
                    "2d6_modifier": "-1",
                    "target": "movement",
                    "duration": 1
                },
                "rarity": "common"
            },
            # 5. 情報漏洩 - Intelligence leak
            {
                "type": EventDeckType.INTEL_LEAK,
                "name": "情報漏洩の可能性",
                "description": "通信傍受により、情報漏洩の懸念があります。",
                "presentation": "通信傍受あり。機密情報伝達方法は要確認。",
                "conditions": {"min_turn": 4},
                "effects": {
                    "movement_restriction": "defensive_posture",
                    "description": "防御態勢下令、侵攻見合わせ",
                    "duration": 1
                },
                "rarity": "rare"
            },
            # 6. 補給途絶 - Supply interruption
            {
                "type": EventDeckType.SUPPLY_INTERRUPTION,
                "name": "補給線途絶",
                "description": "敵の機動により、主要補給線が遮断されました。",
                "presentation": "主要補給線{L}方面、遮断確認。代替経路確保急務。",
                "conditions": {"min_turn": 3},
                "effects": {
                    "action_restriction": "supply_priority",
                    "description": "補給が最優先事項となる",
                    "duration": 2
                },
                "rarity": "uncommon"
            },
            # 7. 士気高揚 - Morale boost
            {
                "type": EventDeckType.MORALE_BOOST,
                "name": "士気高揚",
                "description": "指揮官の激励と戦果報告により、部隊の士気が向上しました。",
                "presentation": "全隊表扬。本日の戦果は戦史に刻まれる。",
                "conditions": {"after_combat": True},
                "effects": {
                    "2d6_modifier": "+1",
                    "target": "combat",
                    "duration": 1
                },
                "rarity": "uncommon"
            },
            # 8. 敵士気低下 - Enemy morale low
            {
                "type": EventDeckType.ENEMY_MORALE_LOW,
                "name": "敵部隊動揺",
                "description": "敵部隊の間で士気低下の兆候が見られます。",
                "presentation": "敵{Z}方面部隊、指揮系統混乱の兆候。追撃の好機。",
                "conditions": {"min_turn": 3},
                "effects": {
                    "2d6_modifier": "+2",
                    "target": "attack",
                    "duration": 1
                },
                "rarity": "rare"
            },
            # 9. 砲兵火力 available - Artillery available
            {
                "type": EventDeckType.ARTILLERY_AVAILABLE,
                "name": "砲兵火力遮断解除",
                "description": "敵防空網の突破口が開き、砲兵射撃が可能になりました。",
                "presentation": "砲兵射撃可能命令下达。火力支援準備完了。",
                "conditions": {"min_turn": 2},
                "effects": {
                    "2d6_modifier": "+1",
                    "target": "artillery",
                    "duration": 1
                },
                "rarity": "common"
            },
            # 10. 航空支援 available - Air support available
            {
                "type": EventDeckType.AIR_SUPPORT_AVAILABLE,
                "name": "航空火力使用可能",
                "description": "航空友軍との連絡が確立し、近接航空支援が利用可能になりました。",
                "presentation": "CAS任務可能。第{CAS}攻撃航空隊接近中。",
                "conditions": {"min_turn": 3},
                "effects": {
                    "2d6_modifier": "+2",
                    "target": "air_strike",
                    "duration": 1
                },
                "rarity": "rare"
            },
        ]
        # Shuffle the deck initially
        random.shuffle(self._deck)

    def should_draw_event(self, turn_number: int, conditions: Optional[Dict[str, Any]] = None) -> bool:
        """Determine if an event should be drawn this turn"""
        chance = self.BASE_DRAW_CHANCE

        # Adjust based on conditions
        if conditions:
            if conditions.get("early_game"):
                chance -= 0.15  # Less events early
            if conditions.get("high_intensity"):
                chance += 0.1
            if conditions.get("player_ahead"):
                chance += 0.1  # More events when player is winning

        return random.random() < chance

    def draw_event(self, turn_number: int, context: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Draw an event from the deck if conditions are met"""
        if not self._deck:
            # Reshuffle discard pile if deck is empty
            if self._discard_pile:
                self._deck = self._discard_pile.copy()
                self._discard_pile = []
                random.shuffle(self._deck)
            else:
                return None  # No events left

        # Check conditions for each event and find the first valid one
        random.shuffle(self._deck)  # Randomize draw order

        for i, event in enumerate(self._deck):
            if self._check_event_conditions(event, turn_number, context):
                # Remove from deck and add to discard
                drawn_event = self._deck.pop(i)
                self._discard_pile.append(drawn_event)
                return self._format_event(drawn_event, context)

        return None

    def _check_event_conditions(self, event: Dict[str, Any], turn_number: int, context: Optional[Dict[str, Any]] = None) -> bool:
        """Check if event conditions are met"""
        conditions = event.get("conditions", {})

        # Check minimum turn
        min_turn = conditions.get("min_turn", 1)
        if turn_number < min_turn:
            return False

        # Check after_combat condition
        if conditions.get("after_combat") and context:
            if not context.get("combat_occurred", False):
                return False

        return True

    def _format_event(self, event: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Format event with context-specific details"""
        formatted = event.copy()
        formatted["turn"] = context.get("turn_number", 0) if context else 0
        formatted["timestamp"] = datetime.utcnow().isoformat()

        # Add specific context details to presentation
        presentation = formatted.get("presentation", "")

        # Replace placeholders with context
        if context:
            replacements = {
                "{X}": str(context.get("reinforcement_number", "X")),
                "{count}": str(context.get("enemy_count", "数個")),
                "{Z}": str(context.get("direction", "方面")),
                "{L}": str(context.get("location", "地域")),
                "{weather}": str(context.get("weather_type", "悪天候")),
                "{CAS}": str(context.get("cas_squadron", "")),
            }
            for placeholder, value in replacements.items():
                presentation = presentation.replace(placeholder, value)

        formatted["presentation_text"] = presentation

        return formatted

    def get_event_description(self, event: Dict[str, Any]) -> str:
        """Get the description of an event"""
        return event.get("description", "")

    def get_event_effects(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Get the effects of an event"""
        return event.get("effects", {})

    def apply_event_to_game_state(self, game_state: Dict[str, Any], event: Dict[str, Any]) -> Dict[str, Any]:
        """Apply event effects to game state"""
        effects = event.get("effects", {})
        modified_state = game_state.copy()

        # Initialize event history if not exists
        if "event_deck_events" not in modified_state:
            modified_state["event_deck_events"] = []

        # Add event to history
        modified_state["event_deck_events"].append({
            "type": event.get("type"),
            "name": event.get("name"),
            "turn": event.get("turn"),
            "effects": effects,
            "applied": True
        })

        # Apply 2D6 modifier effects
        if "2d6_modifier" in effects:
            modifier_key = f"event_{effects['target']}_modifier"
            modifier_value = int(effects["2d6_modifier"])
            current_modifier = modified_state.get(modifier_key, 0)
            modified_state[modifier_key] = current_modifier + modifier_value
            modified_state[f"{modifier_key}_turns"] = effects.get("duration", 1)

        # Apply action restrictions
        if "action_restriction" in effects:
            if "action_restrictions" not in modified_state:
                modified_state["action_restrictions"] = []
            modified_state["action_restrictions"].append({
                "type": effects["action_restriction"],
                "description": effects.get("description", ""),
                "duration": effects.get("duration", 1)
            })

        # Apply movement restrictions
        if "movement_restriction" in effects:
            if "movement_restrictions" not in modified_state:
                modified_state["movement_restrictions"] = []
            modified_state["movement_restrictions"].append({
                "type": effects["movement_restriction"],
                "description": effects.get("description", ""),
                "duration": effects.get("duration", 1)
            })

        return modified_state

    def decrement_effect_duration(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """Decrement duration of active event effects"""
        modified_state = game_state.copy()

        # Decrement 2D6 modifiers
        for key in ["event_combat_modifier", "event_defense_modifier", "event_attack_modifier",
                    "event_movement_modifier", "event_artillery_modifier", "event_air_strike_modifier"]:
            turns_key = f"{key}_turns"
            if modified_state.get(turns_key, 0) > 0:
                modified_state[turns_key] = modified_state[turns_key] - 1
                if modified_state[turns_key] == 0:
                    modified_state[key] = 0  # Reset modifier

        # Decrement action restrictions
        if "action_restrictions" in modified_state:
            for restriction in modified_state["action_restrictions"]:
                restriction["duration"] = max(0, restriction.get("duration", 1) - 1)
            modified_state["action_restrictions"] = [
                r for r in modified_state["action_restrictions"] if r.get("duration", 0) > 0
            ]

        # Decrement movement restrictions
        if "movement_restrictions" in modified_state:
            for restriction in modified_state["movement_restrictions"]:
                restriction["duration"] = max(0, restriction.get("duration", 1) - 1)
            modified_state["movement_restrictions"] = [
                r for r in modified_state["movement_restrictions"] if r.get("duration", 0) > 0
            ]

        return modified_state

    def get_active_modifiers(self, game_state: Dict[str, Any]) -> Dict[str, int]:
        """Get currently active event modifiers"""
        modifiers = {}
        for key in ["event_combat_modifier", "event_defense_modifier", "event_attack_modifier",
                    "event_movement_modifier", "event_artillery_modifier", "event_air_strike_modifier"]:
            if key in game_state and game_state.get(f"{key}_turns", 0) > 0:
                # Extract target name from key
                target = key.replace("event_", "").replace("_modifier", "")
                modifiers[target] = game_state[key]
        return modifiers

    def get_deck_count(self) -> int:
        """Get number of cards remaining in deck"""
        return len(self._deck)

    def get_discard_count(self) -> int:
        """Get number of cards in discard pile"""
        return len(self._discard_pile)


# Service instance factory
def create_event_deck_service(seed: Optional[int] = None) -> EventDeckService:
    """Create an event deck service instance"""
    return EventDeckService(random_seed=seed)
