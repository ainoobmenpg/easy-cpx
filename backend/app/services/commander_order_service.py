# Commander Order Service for Operational CPX
# Manages high-level command intent and orders
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class CommanderOrderData:
    """Data class for commander orders"""
    intent: str
    mission: str
    constraints: str
    roe: str
    priorities: list[str]
    time_limit: str
    available_forces: list[dict]
    reporting_requirements: list[str]


class CommanderOrderService:
    """
    Service for managing commander orders and command hierarchy

    Implements the commander order system from play logs:
    - Intent: Strategic objective
    - Mission: Specific tactical mission
    - Constraints: Operational constraints
    - ROE: Rules of Engagement
    - Priorities: Priority list
    - Time limit: Operational timeframe
    - Available forces: Units under command
    - Reporting requirements: Events that must be reported
    """

    DEFAULT_ROE = """- 敵火力への接触時のみ交戦可
- 民間人被害防止のため無差別火力使用禁止
- 指揮支援拠点への攻撃は上官承認不要
- 浸透した敵兵力への即時反応可"""

    DEFAULT_CONSTRAINTS = """- 民間施設への被害最小化
- 第三国領土侵犯禁止
- 環境被害回避"""

    DEFAULT_PRIORITIES = [
        "自国市民の防護",
        "越境渗透の阻止",
        "戦力的要衝の確保",
        "敵戦力の撃破"
    ]

    def __init__(self):
        self._current_order: Optional[CommanderOrderData] = None

    def create_default_order(self, available_units: list[dict]) -> CommanderOrderData:
        """Create a default commander order"""
        self._current_order = CommanderOrderData(
            intent="北部国境の主導権を回復し、敵渗透部隊を撃破する",
            mission="国境沿い脅威帯を制圧し、安全な国境線を確立する",
            constraints=self.DEFAULT_CONSTRAINTS,
            roe=self.DEFAULT_ROE,
            priorities=self.DEFAULT_PRIORITIES,
            time_limit="初動24時間で戦況を安定化",
            available_forces=available_units,
            reporting_requirements=[
                "越境発生",
                "敵主力接触",
                "民間人被害",
                "指揮系統の断絶",
                "予想外の抵抗"
            ]
        )
        return self._current_order

    def update_order(
        self,
        intent: Optional[str] = None,
        mission: Optional[str] = None,
        constraints: Optional[str] = None,
        roe: Optional[str] = None,
        priorities: Optional[list[str]] = None,
        time_limit: Optional[str] = None,
        available_forces: Optional[list[dict]] = None,
        reporting_requirements: Optional[list[str]] = None
    ) -> CommanderOrderData:
        """Update the current commander order"""
        if self._current_order is None:
            raise ValueError("No current order exists. Call create_default_order first.")

        if intent is not None:
            self._current_order.intent = intent
        if mission is not None:
            self._current_order.mission = mission
        if constraints is not None:
            self._current_order.constraints = constraints
        if roe is not None:
            self._current_order.roe = roe
        if priorities is not None:
            self._current_order.priorities = priorities
        if time_limit is not None:
            self._current_order.time_limit = time_limit
        if available_forces is not None:
            self._current_order.available_forces = available_forces
        if reporting_requirements is not None:
            self._current_order.reporting_requirements = reporting_requirements

        return self._current_order

    def get_current_order(self) -> Optional[CommanderOrderData]:
        """Get the current commander order"""
        return self._current_order

    def format_order_for_display(self) -> str:
        """Format the current order for display in UI"""
        if self._current_order is None:
            return "No active commander order"

        order = self._current_order
        lines = [
            "【司令官命令】",
            "",
            f"| Intent | {order.intent} |",
            f"| Mission | {order.mission} |",
            f"| Constraints | {order.constraints} |",
            f"| ROE | {order.roe} |",
            f"| Priorities | {', '.join(order.priorities)} |",
            f"| Time limit | {order.time_limit} |",
            f"| Available forces | {len(order.available_forces)} units |",
            f"| Reporting | {', '.join(order.reporting_requirements)} |"
        ]

        return "\n".join(lines)

    def get_reporting_requirements(self) -> list[str]:
        """Get reporting requirements"""
        if self._current_order is None:
            return []
        return self._current_order.reporting_requirements

    def check_reporting_requirement(
        self,
        event_type: str,
        event_data: dict
    ) -> tuple[bool, str]:
        """
        Check if an event triggers a reporting requirement

        Returns:
            (should_report, reason)
        """
        if self._current_order is None:
            return False, "No active commander order"

        requirements = self._current_order.reporting_requirements
        event_lower = event_type.lower()

        for req in requirements:
            req_lower = req.lower()
            if req_lower in event_lower:
                return True, f"Reporting requirement triggered: {req}"

        return False, ""

    def format_priority_list(self) -> str:
        """Format priorities as a numbered list"""
        if self._current_order is None:
            return ""

        lines = []
        for i, priority in enumerate(self._current_order.priorities, 1):
            lines.append(f"{i}. {priority}")

        return "\n".join(lines)


# Global instance
_commander_order_service = CommanderOrderService()


def get_commander_order_service() -> CommanderOrderService:
    """Get the global commander order service"""
    return _commander_order_service
