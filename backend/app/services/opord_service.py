# OPORD Service - Manages OPORD/FRAGO data in SMESC format
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass
class OpordSituationData:
    """Situation section of OPORD"""
    enemy_situation: str = ""
    friendly_situation: str = ""
    terrain_impact: str = ""
    weather_impact: str = ""
    attachments: list[str] = field(default_factory=list)
    detachments: list[str] = field(default_factory=list)


@dataclass
class OpordMissionData:
    """Mission section of OPORD"""
    task: str = ""
    purpose: str = ""
    end_state: str = ""
    success_criteria: list[str] = field(default_factory=list)


@dataclass
class OpordExecutionUnitTask:
    """Task assigned to a specific unit"""
    unit: str
    task: str
    timing: Optional[str] = None


@dataclass
class OpordExecutionContingency:
    """Contingency plan"""
    condition: str
    action: str


@dataclass
class OpordExecutionData:
    """Execution section of OPORD"""
    concept_of_operations: str = ""
    phase_timeline: list[str] = field(default_factory=list)
    tasks_by_unit: list[OpordExecutionUnitTask] = field(default_factory=list)
    coordination: str = ""
    contingencies: list[OpordExecutionContingency] = field(default_factory=list)
    command_signal: str = ""


@dataclass
class OpordBoundary:
    """Boundary definition"""
    name: str
    line: str
    control: str


@dataclass
class OpordPhaseLine:
    """Phase line definition"""
    name: str
    location: str
    criteria: str


@dataclass
class OpordCoordinationData:
    """Coordination section of OPORD"""
    boundaries: list[OpordBoundary] = field(default_factory=list)
    phase_lines: list[OpordPhaseLine] = field(default_factory=list)
    fire_support: str = ""
    air_support: str = ""
    engineer_support: str = ""
    c2_relationships: str = ""


@dataclass
class OpordSupplyData:
    """Supply information"""
    ammo: str = ""
    fuel: str = ""
    other: str = ""


@dataclass
class OpordServiceSupportData:
    """Service Support section of OPORD"""
    supply: OpordSupplyData = field(default_factory=OpordSupplyData)
    maintenance: str = ""
    medical: str = ""
    transportation: str = ""
    evacuation: str = ""
    field_services: str = ""
    general_supply: str = ""


@dataclass
class OPORDData:
    """Complete OPORD data structure in SMESC format"""
    opord_id: str
    game_id: int
    title: str
    classification: str = "unclassified"
    effective_date: str = ""
    situation: OpordSituationData = field(default_factory=OpordSituationData)
    mission: OpordMissionData = field(default_factory=OpordMissionData)
    execution: OpordExecutionData = field(default_factory=OpordExecutionData)
    coordination: OpordCoordinationData = field(default_factory=OpordCoordinationData)
    service_support: OpordServiceSupportData = field(default_factory=OpordServiceSupportData)
    created_at: str = ""
    updated_at: str = ""
    created_by: Optional[str] = None


class OpordService:
    """
    Service for managing OPORD/FRAGO in SMESC format.

    SMESC Format:
    - Situation: 状況（敵、味方、地形、天候）
    - Mission: 任務
    - Execution: 実行（任務達成のための具体的な指示）
    - Coordination: 調整（他部隊との調整事項）
    - Service Support: 後方支援（補給、整備、衛生等）
    """

    def __init__(self):
        self._current_opord: Optional[OPORDData] = None

    def create_default_opord(self, game_id: int, title: str = "作戦計画") -> OPORDData:
        """Create a default OPORD with SMESC structure"""
        now = datetime.now().isoformat()

        self._current_opord = OPORDData(
            opord_id=str(uuid.uuid4()),
            game_id=game_id,
            title=title,
            classification="unclassified",
            effective_date=now[:10],
            situation=OpordSituationData(
                enemy_situation="敵主力部隊が北方国境沿いに集結中。敵航空兵力による脅威あり。",
                friendly_situation="自軍主力は南部地域に展開中。増援部隊が参入予定。",
                terrain_impact="山林地帯が視界を制限し、機甲部隊の機動を制約。",
                weather_impact="視界不良による偵察効率低下懸念。降水により機動路が制限される可能性。",
                attachments=["第3機甲旅団", "直射火力中队"],
                detachments=[]
            ),
            mission=OpordMissionData(
                task="敵渗透部隊を撃破し、国境地域の安全を確立する",
                purpose="北部国境の主導権を回復し、後方の安全を確保する",
                end_state="敵主力部隊が撃破され、国境線が確保される",
                success_criteria=[
                    "敵戦力の50%以上撃破",
                    "味方損耗30%以下",
                    "目標地点の確保完了"
                ]
            ),
            execution=OpordExecutionData(
                concept_of_operations="北部方面から敵主力に圧力をかけつつ、側面を機動部隊で奇襲する",
                phase_timeline=[
                    "Phase 1: 偵察・監視態勢確立",
                    "Phase 2: 主力部隊前進",
                    "Phase 3: 敵主力攻撃",
                    "Phase 4: 確保・防勢転換"
                ],
                tasks_by_unit=[
                    OpordExecutionUnitTask(unit="第1大隊", task="敵主力に対し正面から攻撃", timing="0800"),
                    OpordExecutionUnitTask(unit="第2大隊", task="右側面から機動し敵退路を遮断", timing="0900"),
                    OpordExecutionUnitTask(unit="直射火力", task="敵防御拠点への火力支援", timing="随伴")
                ],
                coordination="第2大隊とは0800に火力協調線を設定",
                contingencies=[
                    OpordExecutionContingency(condition="敵航空脅威出現", action="対空火器を展開し防空態勢"),
                    OpordExecutionContingency(condition="敵増援出現", action="予備隊を投入し対応")
                ],
                command_signal="VHF周波数 45.25 MHz"
            ),
            coordination=OpordCoordinationData(
                boundaries=[
                    OpordBoundary(name="ELM", line="A-B", control="当軍")
                ],
                phase_lines=[
                    OpordPhaseLine(name="PHASE LINE RED", location="川線", criteria="全隊到達")
                ],
                fire_support="直射火力150榴弾優先配分",
                air_support="戦闘ヘリ2機随伴",
                engineer_support="渡河施設2箇所設置予定",
                c2_relationships="当隊→旅団→師団"
            ),
            service_support=OpordServiceSupportData(
                supply=OpordSupplyData(
                    ammo="前方弾薬集積所（FAP）に3日分保有",
                    fuel="現地調達可能、予備燃料16000ℓ",
                    other="的一般補給は後方より"
                ),
                maintenance="前方整備班（1個小隊）随伴",
                medical="衛生班（1個分身）随伴、後送は戦場病院へ",
                transportation="輸送中队（10トン車5両）随伴",
                evacuation="負傷者は後方医院へ空送",
                field_services="糧秣は1日分携行",
                general_supply="後方支援大队より補給受領"
            ),
            created_at=now,
            updated_at=now
        )

        return self._current_opord

    def get_current_opord(self) -> Optional[OPORDData]:
        """Get the current OPORD"""
        return self._current_opord

    def set_opord(self, opord: OPORDData) -> None:
        """Set the current OPORD"""
        self._current_opord = opord

    def update_situation(
        self,
        enemy_situation: Optional[str] = None,
        friendly_situation: Optional[str] = None,
        terrain_impact: Optional[str] = None,
        weather_impact: Optional[str] = None,
        attachments: Optional[list[str]] = None,
        detachments: Optional[list[str]] = None
    ) -> OpordSituationData:
        """Update situation section"""
        if self._current_opord is None:
            raise ValueError("No current OPORD exists. Call create_default_opord first.")

        if enemy_situation is not None:
            self._current_opord.situation.enemy_situation = enemy_situation
        if friendly_situation is not None:
            self._current_opord.situation.friendly_situation = friendly_situation
        if terrain_impact is not None:
            self._current_opord.situation.terrain_impact = terrain_impact
        if weather_impact is not None:
            self._current_opord.situation.weather_impact = weather_impact
        if attachments is not None:
            self._current_opord.situation.attachments = attachments
        if detachments is not None:
            self._current_opord.situation.detachments = detachments

        self._current_opord.updated_at = datetime.now().isoformat()
        return self._current_opord.situation

    def update_mission(
        self,
        task: Optional[str] = None,
        purpose: Optional[str] = None,
        end_state: Optional[str] = None,
        success_criteria: Optional[list[str]] = None
    ) -> OpordMissionData:
        """Update mission section"""
        if self._current_opord is None:
            raise ValueError("No current OPORD exists. Call create_default_opord first.")

        if task is not None:
            self._current_opord.mission.task = task
        if purpose is not None:
            self._current_opord.mission.purpose = purpose
        if end_state is not None:
            self._current_opord.mission.end_state = end_state
        if success_criteria is not None:
            self._current_opord.mission.success_criteria = success_criteria

        self._current_opord.updated_at = datetime.now().isoformat()
        return self._current_opord.mission

    def update_execution(
        self,
        concept_of_operations: Optional[str] = None,
        phase_timeline: Optional[list[str]] = None,
        tasks_by_unit: Optional[list[Dict[str, Any]]] = None,
        coordination: Optional[str] = None,
        contingencies: Optional[list[Dict[str, Any]]] = None,
        command_signal: Optional[str] = None
    ) -> OpordExecutionData:
        """Update execution section"""
        if self._current_opord is None:
            raise ValueError("No current OPORD exists. Call create_default_opord first.")

        if concept_of_operations is not None:
            self._current_opord.execution.concept_of_operations = concept_of_operations
        if phase_timeline is not None:
            self._current_opord.execution.phase_timeline = phase_timeline
        if tasks_by_unit is not None:
            self._current_opord.execution.tasks_by_unit = [
                OpordExecutionUnitTask(**task) for task in tasks_by_unit
            ]
        if coordination is not None:
            self._current_opord.execution.coordination = coordination
        if contingencies is not None:
            self._current_opord.execution.contingencies = [
                OpordExecutionContingency(**c) for c in contingencies
            ]
        if command_signal is not None:
            self._current_opord.execution.command_signal = command_signal

        self._current_opord.updated_at = datetime.now().isoformat()
        return self._current_opord.execution

    def update_coordination(
        self,
        boundaries: Optional[list[Dict[str, Any]]] = None,
        phase_lines: Optional[list[Dict[str, Any]]] = None,
        fire_support: Optional[str] = None,
        air_support: Optional[str] = None,
        engineer_support: Optional[str] = None,
        c2_relationships: Optional[str] = None
    ) -> OpordCoordinationData:
        """Update coordination section"""
        if self._current_opord is None:
            raise ValueError("No current OPORD exists. Call create_default_opord first.")

        if boundaries is not None:
            self._current_opord.coordination.boundaries = [
                OpordBoundary(**b) for b in boundaries
            ]
        if phase_lines is not None:
            self._current_opord.coordination.phase_lines = [
                OpordPhaseLine(**p) for p in phase_lines
            ]
        if fire_support is not None:
            self._current_opord.coordination.fire_support = fire_support
        if air_support is not None:
            self._current_opord.coordination.air_support = air_support
        if engineer_support is not None:
            self._current_opord.coordination.engineer_support = engineer_support
        if c2_relationships is not None:
            self._current_opord.coordination.c2_relationships = c2_relationships

        self._current_opord.updated_at = datetime.now().isoformat()
        return self._current_opord.coordination

    def update_service_support(
        self,
        supply: Optional[Dict[str, str]] = None,
        maintenance: Optional[str] = None,
        medical: Optional[str] = None,
        transportation: Optional[str] = None,
        evacuation: Optional[str] = None,
        field_services: Optional[str] = None,
        general_supply: Optional[str] = None
    ) -> OpordServiceSupportData:
        """Update service support section"""
        if self._current_opord is None:
            raise ValueError("No current OPORD exists. Call create_default_opord first.")

        if supply is not None:
            self._current_opord.service_support.supply = OpordSupplyData(**supply)
        if maintenance is not None:
            self._current_opord.service_support.maintenance = maintenance
        if medical is not None:
            self._current_opord.service_support.medical = medical
        if transportation is not None:
            self._current_opord.service_support.transportation = transportation
        if evacuation is not None:
            self._current_opord.service_support.evacuation = evacuation
        if field_services is not None:
            self._current_opord.service_support.field_services = field_services
        if general_supply is not None:
            self._current_opord.service_support.general_supply = general_supply

        self._current_opord.updated_at = datetime.now().isoformat()
        return self._current_opord.service_support

    def format_for_display(self) -> str:
        """Format OPORD for display in UI"""
        if self._current_opord is None:
            return "No active OPORD"

        opord = self._current_opord
        lines = [
            f"【OPORD: {opord.title}】",
            f"区分: {opord.classification} | 発効日: {opord.effective_date}",
            "",
            "=== SITUATION（状況） ===",
            f"敵状況: {opord.situation.enemy_situation}",
            f"味方状況: {opord.situation.friendly_situation}",
            f"地形影響: {opord.situation.terrain_impact}",
            f"天候影響: {opord.situation.weather_impact}",
            "",
            "=== MISSION（任務） ===",
            f"任務: {opord.mission.task}",
            f"目的: {opord.mission.purpose}",
            f"終結状態: {opord.mission.end_state}",
            f"成功基準: {', '.join(opord.mission.success_criteria)}",
            "",
            "=== EXECUTION（実行） ===",
            f"作戦構想: {opord.execution.concept_of_operations}",
            f"調整: {opord.execution.coordination}",
            f"指揮通信: {opord.execution.command_signal}",
            "",
            "=== COORDINATION（調整） ===",
            f"火力支援: {opord.coordination.fire_support}",
            f"航空支援: {opord.coordination.air_support}",
            f"指揮系統: {opord.coordination.c2_relationships}",
            "",
            "=== SERVICE SUPPORT（後方支援） ===",
            f"弾薬: {opord.service_support.supply.ammo}",
            f"燃料: {opord.service_support.supply.fuel}",
            f"整備: {opord.service_support.maintenance}",
            f"衛生: {opord.service_support.medical}",
        ]

        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Convert OPORD to dictionary for API response"""
        if self._current_opord is None:
            return {}

        opord = self._current_opord
        return {
            "opord_id": opord.opord_id,
            "game_id": opord.game_id,
            "title": opord.title,
            "classification": opord.classification,
            "effective_date": opord.effective_date,
            "situation": {
                "enemy_situation": opord.situation.enemy_situation,
                "friendly_situation": opord.situation.friendly_situation,
                "terrain_impact": opord.situation.terrain_impact,
                "weather_impact": opord.situation.weather_impact,
                "attachments": opord.situation.attachments,
                "detachments": opord.situation.detachments
            },
            "mission": {
                "task": opord.mission.task,
                "purpose": opord.mission.purpose,
                "end_state": opord.mission.end_state,
                "success_criteria": opord.mission.success_criteria
            },
            "execution": {
                "concept_of_operations": opord.execution.concept_of_operations,
                "phase_timeline": opord.execution.phase_timeline,
                "tasks_by_unit": [
                    {"unit": t.unit, "task": t.task, "timing": t.timing}
                    for t in opord.execution.tasks_by_unit
                ],
                "coordination": opord.execution.coordination,
                "contingencies": [
                    {"condition": c.condition, "action": c.action}
                    for c in opord.execution.contingencies
                ],
                "command_signal": opord.execution.command_signal
            },
            "coordination": {
                "boundaries": [
                    {"name": b.name, "line": b.line, "control": b.control}
                    for b in opord.coordination.boundaries
                ],
                "phase_lines": [
                    {"name": p.name, "location": p.location, "criteria": p.criteria}
                    for p in opord.coordination.phase_lines
                ],
                "fire_support": opord.coordination.fire_support,
                "air_support": opord.coordination.air_support,
                "engineer_support": opord.coordination.engineer_support,
                "c2_relationships": opord.coordination.c2_relationships
            },
            "service_support": {
                "supply": {
                    "ammo": opord.service_support.supply.ammo,
                    "fuel": opord.service_support.supply.fuel,
                    "other": opord.service_support.supply.other
                },
                "maintenance": opord.service_support.maintenance,
                "medical": opord.service_support.medical,
                "transportation": opord.service_support.transportation,
                "evacuation": opord.service_support.evacuation,
                "field_services": opord.service_support.field_services,
                "general_supply": opord.service_support.general_supply
            },
            "created_at": opord.created_at,
            "updated_at": opord.updated_at,
            "created_by": opord.created_by
        }


# Global instance
_opord_service = OpordService()


def get_opord_service() -> OpordService:
    """Get the global OPORD service"""
    return _opord_service
