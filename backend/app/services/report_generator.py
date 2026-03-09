# Report Generator for Operational CPX
# Generates standardized military reports: SITREP, INTSUM, OPSUM, LOGSITREP, SALUTE
from typing import Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import json


@dataclass
class ReportMetadata:
    """Common metadata for all report types"""
    report_id: str
    turn: int
    timestamp: str
    period: str = ""


class SALUTEGenerator:
    """Generates SALUTE reports (Size, Activity, Location, Unit, Time, Equipment)"""

    def generate(self, unit_data: dict, game_state: dict, assessment: str = "") -> dict:
        """Generate SALUTE report for a unit"""
        return {
            "report_id": f"SALUTE-{uuid.uuid4().hex[:8]}",
            "turn": game_state.get("turn", 1),
            "timestamp": datetime.utcnow().isoformat(),
            "size": unit_data.get("size", "不明"),
            "activity": unit_data.get("activity", "確認中"),
            "location": unit_data.get("location", "不明"),
            "unit": unit_data.get("unit_name", "不明"),
            "time": game_state.get("time", "00:00"),
            "equipment": unit_data.get("equipment", "確認中"),
            "assessment": assessment
        }


class INTSUMGenerator:
    """Generates Intelligence Summary reports"""

    def generate(
        self,
        game_state: dict,
        enemy_knowledge: dict,
        order_results: list[dict],
        period: str = ""
    ) -> dict:
        """Generate INTSUM report"""
        turn = game_state.get("turn", 1)
        units = game_state.get("units", [])

        # Separate friendly and enemy units
        friendly_units = [u for u in units if u.get("side") == "player"]
        enemy_units = [u for u in units if u.get("side") == "enemy"]

        # Build enemy dispositions based on knowledge
        enemy_dispositions = []
        confirmed_ids = set(enemy_knowledge.get("confirmed", []))
        estimated_ids = set(enemy_knowledge.get("estimated", []))

        for unit in enemy_units:
            unit_id = unit.get("id")
            if unit_id in confirmed_ids:
                enemy_dispositions.append({
                    "unit_name": unit.get("name", "Unknown"),
                    "position": f"({unit.get('x')}, {unit.get('y')})",
                    "strength": unit.get("status", "不明"),
                    "assessment": "confirmed"
                })
            elif unit_id in estimated_ids:
                enemy_dispositions.append({
                    "unit_name": "推定-" + str(unit_id),
                    "position": f"({unit.get('x')}, {unit.get('y')})",
                    "strength": "推定",
                    "assessment": "estimated"
                })

        # Friendly dispositions
        friendly_dispositions = []
        for unit in friendly_units:
            friendly_dispositions.append({
                "unit_name": unit.get("name", "Unknown"),
                "position": f"({unit.get('x')}, {unit.get('y')})",
                "status": unit.get("status", "intact")
            })

        # Intelligence gaps
        unknown_count = len(enemy_knowledge.get("unknown", []))
        intelligence_gaps = []
        if unknown_count > 0:
            intelligence_gaps.append(f"{unknown_count}個の敵大隊の位置が未確認")

        # Recent order outcomes
        recent_outcomes = [r.get("outcome", "unknown") for r in order_results]
        recommendations = []
        if "failed" in recent_outcomes:
            recommendations.append("敵の抵抗が予想以上。慎重に接近することを推奨")
        if len(enemy_dispositions) < len(enemy_units) * 0.5:
            recommendations.append("偵察を強化し、敵配置の把握を拡大せよ")
        if not recommendations:
            recommendations.append("現在の優位をを維持し、敵の隙を狙う")

        return {
            "report_id": f"INTSUM-{uuid.uuid4().hex[:8]}",
            "turn": turn,
            "timestamp": datetime.utcnow().isoformat(),
            "period": period or f"Turn {turn}",
            "summary": self._generate_summary(turn, enemy_dispositions, friendly_dispositions),
            "enemy_dispositions": enemy_dispositions,
            "friendly_dispositions": friendly_dispositions,
            "intelligence_gaps": intelligence_gaps,
            "recommendations": recommendations
        }

    def _generate_summary(self, turn: int, enemy_disp: list, friendly_disp: list) -> str:
        """Generate summary text"""
        confirmed = len([e for e in enemy_disp if e.get("assessment") == "confirmed"])
        estimated = len([e for e in enemy_disp if e.get("assessment") == "estimated"])

        lines = [
            f"ターン{turn}現在、",
            f"、味方は{friendly_disp}個師団が作戦可能",
            f"敵は確認{confirmed}個、推定{estimated}個大隊が行動中"
        ]
        return "".join(lines)


class OPSUMGenerator:
    """Generates Operations Summary reports"""

    def generate(
        self,
        game_state: dict,
        order_results: list[dict],
        current_orders: list[dict],
        planned_orders: list[dict],
        period: str = ""
    ) -> dict:
        """Generate OPSUM report"""
        turn = game_state.get("turn", 1)

        # Operations conducted this turn
        operations_conducted = []
        for result in order_results:
            unit_name = result.get("unit_name", "Unknown")
            outcome = result.get("outcome", "unknown")
            operation_name = f"{unit_name}の作戰"

            outcome_text = {
                "success": "任務成功",
                "partial": "部分的成功",
                "failed": "任務失敗",
                "blocked": "阻止された"
            }.get(outcome, "不明")

            operations_conducted.append({
                "operation_name": operation_name,
                "objective": result.get("intent", "任務"),
                "outcome": outcome,
                "units_involved": [unit_name],
                "results": outcome_text
            })

        # Current ongoing operations
        current_operations = []
        for order in current_orders:
            current_operations.append({
                "operation_name": order.get("intent", "作戦中"),
                "status": "ongoing",
                "units_involved": [order.get("unit_name", "不明")]
            })

        # Planned operations
        planned_operations = []
        for order in planned_orders:
            planned_operations.append({
                "operation_name": order.get("intent", "予定作戦"),
                "objective": order.get("objective", "任務"),
                "planned_time": f"Turn {turn + 1}",
                "units_assigned": [order.get("unit_name", "不明")]
            })

        # Commander assessment
        success_count = sum(1 for o in operations_conducted if o["outcome"] == "success")
        total_count = len(operations_conducted)

        if total_count == 0:
            assessment = "現在作戦行動なし"
        elif success_count == total_count:
            assessment = "全作戦成功 - 戦況有利"
        elif success_count > total_count / 2:
            assessment = "概ね作戦成功 - 戦況控制的"
        else:
            assessment = "作戦失敗多数 - 状況嚴峻"

        return {
            "report_id": f"OPSUM-{uuid.uuid4().hex[:8]}",
            "turn": turn,
            "timestamp": datetime.utcnow().isoformat(),
            "period": period or f"Turn {turn}",
            "operations_conducted": operations_conducted,
            "current_operations": current_operations,
            "planned_operations": planned_operations,
            "commander_assessment": assessment
        }


class LOGSITREPGenerator:
    """Generates Logistical Situation Reports"""

    def generate(
        self,
        game_state: dict,
        attrition_data: list[dict] = None,
        resupply_requests: list[dict] = None,
        period: str = ""
    ) -> dict:
        """Generate LOGSITREP report"""
        turn = game_state.get("turn", 1)
        units = game_state.get("units", [])

        # Calculate supply status
        ammo_full = sum(1 for u in units if u.get("ammo") == "full")
        ammo_depleted = sum(1 for u in units if u.get("ammo") == "depleted")
        ammo_exhausted = sum(1 for u in units if u.get("ammo") == "exhausted")

        fuel_full = sum(1 for u in units if u.get("fuel") == "full")
        fuel_depleted = sum(1 for u in units if u.get("fuel") == "depleted")
        fuel_exhausted = sum(1 for u in units if u.get("fuel") == "exhausted")

        readiness_full = sum(1 for u in units if u.get("readiness") == "full")
        readiness_depleted = sum(1 for u in units if u.get("readiness") == "depleted")
        readiness_exhausted = sum(1 for u in units if u.get("readiness") == "exhausted")

        supply_status = {
            "ammo": {
                "full": ammo_full,
                "depleted": ammo_depleted,
                "exhausted": ammo_exhausted
            },
            "fuel": {
                "full": fuel_full,
                "depleted": fuel_depleted,
                "exhausted": fuel_exhausted
            },
            "readiness": {
                "full": readiness_full,
                "depleted": readiness_depleted,
                "exhausted": readiness_exhausted
            }
        }

        # Supply lines (simplified - all open for now)
        supply_lines = [
            {
                "line_id": "main-supply",
                "status": "open",
                "last_verified": game_state.get("time", "00:00")
            }
        ]

        # Calculate attrition
        attrition = []
        if attrition_data:
            for at in attrition_data:
                attrition.append({
                    "unit": at.get("unit_name", "不明"),
                    "ammo_spent": at.get("ammo_spent", 0),
                    "fuel_spent": at.get("fuel_spent", 0),
                    "maintenance_needed": at.get("maintenance_needed", False)
                })

        # Resupply requests
        if resupply_requests is None:
            # Auto-generate from low supply units
            resupply_requests = []
            for unit in units:
                if unit.get("ammo") in ["depleted", "exhausted"]:
                    resupply_requests.append({
                        "unit": unit.get("name", "不明"),
                        "type": "ammo",
                        "priority": "high" if unit.get("ammo") == "exhausted" else "normal",
                        "status": "pending"
                    })
                if unit.get("fuel") in ["depleted", "exhausted"]:
                    resupply_requests.append({
                        "unit": unit.get("name", "不明"),
                        "type": "fuel",
                        "priority": "high" if unit.get("fuel") == "exhausted" else "normal",
                        "status": "pending"
                    })

        return {
            "report_id": f"LOGSITREP-{uuid.uuid4().hex[:8]}",
            "turn": turn,
            "timestamp": datetime.utcnow().isoformat(),
            "period": period or f"Turn {turn}",
            "supply_status": supply_status,
            "supply_lines": supply_lines,
            "attrition": attrition,
            "resupply_requests": resupply_requests
        }


class UnifiedReportGenerator:
    """
    Generates unified reports in standardized military formats
    Supports: SITREP, INTSUM, OPSUM, LOGSITREP, SALUTE
    """

    def __init__(self, sitrep_generator=None):
        self.sitrep_generator = sitrep_generator
        self.salute_generator = SALUTEGenerator()
        self.intsum_generator = INTSUMGenerator()
        self.opsum_generator = OPSUMGenerator()
        self.logsitrep_generator = LOGSITREPGenerator()

    def generate(
        self,
        format_type: str,
        game_state: dict,
        options: dict = None
    ) -> dict:
        """Generate a report in the specified format"""
        options = options or {}

        # Common metadata
        turn = game_state.get("turn", 1)
        timestamp = datetime.utcnow().isoformat()

        if format_type == "sitrep":
            return self._generate_sitrep(game_state, options, timestamp)
        elif format_type == "intsumm":
            return self._generate_intsum(game_state, options, timestamp)
        elif format_type == "opsumm":
            return self._generate_opsumm(game_state, options, timestamp)
        elif format_type == "logsitrep":
            return self._generate_logsitrep(game_state, options, timestamp)
        elif format_type == "salute":
            return self._generate_salute(game_state, options, timestamp)
        else:
            raise ValueError(f"Unknown report format: {format_type}")

    def _generate_sitrep(self, game_state: dict, options: dict, timestamp: str) -> dict:
        """Generate SITREP using existing generator"""
        if self.sitrep_generator:
            order_results = options.get("order_results", [])
            enemy_knowledge = options.get("enemy_knowledge", {})
            commander_order = options.get("commander_order")
            events = options.get("events", [])
            map_renderer = options.get("map_renderer")

            sitrep_data = self.sitrep_generator.generate_sitrep(
                game_state=game_state,
                order_results=order_results,
                map_renderer=map_renderer,
                enemy_knowledge=enemy_knowledge,
                commander_order=commander_order,
                events=events
            )

            return {
                "report_id": f"SITREP-{uuid.uuid4().hex[:8]}",
                "format": "sitrep",
                "turn": game_state.get("turn", 1),
                "timestamp": datetime.utcnow().isoformat(),
                "generated_at": timestamp,
                "content": sitrep_data
            }
        else:
            # Fallback if no sitrep generator
            return {
                "report_id": f"SITREP-{uuid.uuid4().hex[:8]}",
                "format": "sitrep",
                "turn": game_state.get("turn", 1),
                "timestamp": datetime.utcnow().isoformat(),
                "generated_at": timestamp,
                "content": {
                    "turn": game_state.get("turn", 1),
                    "overview": "SITREP generation not available"
                }
            }

    def _generate_intsum(self, game_state: dict, options: dict, timestamp: str) -> dict:
        """Generate INTSUM"""
        enemy_knowledge = options.get("enemy_knowledge", {})
        order_results = options.get("order_results", [])
        period = options.get("period", "")

        content = self.intsum_generator.generate(
            game_state=game_state,
            enemy_knowledge=enemy_knowledge,
            order_results=order_results,
            period=period
        )

        return {
            "report_id": f"INTSUM-{uuid.uuid4().hex[:8]}",
            "format": "intsumm",
            "turn": game_state.get("turn", 1),
            "timestamp": datetime.utcnow().isoformat(),
            "generated_at": timestamp,
            "content": content
        }

    def _generate_opsumm(self, game_state: dict, options: dict, timestamp: str) -> dict:
        """Generate OPSUM"""
        order_results = options.get("order_results", [])
        current_orders = options.get("current_orders", [])
        planned_orders = options.get("planned_orders", [])
        period = options.get("period", "")

        content = self.opsum_generator.generate(
            game_state=game_state,
            order_results=order_results,
            current_orders=current_orders,
            planned_orders=planned_orders,
            period=period
        )

        return {
            "report_id": f"OPSUM-{uuid.uuid4().hex[:8]}",
            "format": "opsumm",
            "turn": game_state.get("turn", 1),
            "timestamp": datetime.utcnow().isoformat(),
            "generated_at": timestamp,
            "content": content
        }

    def _generate_logsitrep(self, game_state: dict, options: dict, timestamp: str) -> dict:
        """Generate LOGSITREP"""
        attrition_data = options.get("attrition_data", [])
        resupply_requests = options.get("resupply_requests")
        period = options.get("period", "")

        content = self.logsitrep_generator.generate(
            game_state=game_state,
            attrition_data=attrition_data,
            resupply_requests=resupply_requests,
            period=period
        )

        return {
            "report_id": f"LOGSITREP-{uuid.uuid4().hex[:8]}",
            "format": "logsitrep",
            "turn": game_state.get("turn", 1),
            "timestamp": datetime.utcnow().isoformat(),
            "generated_at": timestamp,
            "content": content
        }

    def _generate_salute(self, game_state: dict, options: dict, timestamp: str) -> dict:
        """Generate SALUTE for a specific unit"""
        unit_data = options.get("unit_data", {})
        assessment = options.get("assessment", "")

        content = self.salute_generator.generate(
            unit_data=unit_data,
            game_state=game_state,
            assessment=assessment
        )

        return {
            "report_id": f"SALUTE-{uuid.uuid4().hex[:8]}",
            "format": "salute",
            "turn": game_state.get("turn", 1),
            "timestamp": datetime.utcnow().isoformat(),
            "generated_at": timestamp,
            "content": content
        }

    def generate_all(
        self,
        game_state: dict,
        options: dict = None
    ) -> dict:
        """Generate all report formats"""
        options = options or {}
        return {
            "sitrep": self.generate("sitrep", game_state, options),
            "intsumm": self.generate("intsumm", game_state, options),
            "opsumm": self.generate("opsumm", game_state, options),
            "logsitrep": self.generate("logsitrep", game_state, options)
        }


# Global instance
_report_generator = None


def get_report_generator(sitrep_generator=None) -> UnifiedReportGenerator:
    """Get the global report generator"""
    global _report_generator
    if _report_generator is None:
        _report_generator = UnifiedReportGenerator(sitrep_generator)
    return _report_generator
