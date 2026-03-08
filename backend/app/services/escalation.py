# Escalation Service
# Manages escalation levels, international reactions, and approval requirements
from enum import Enum
from typing import Optional
from datetime import datetime


class EscalationLevel(Enum):
    PEACETIME = "peacetime"  # 平時
    CRISIS = "crisis"  # 危機
    CONFLICT = "conflict"  # 紛争
    WAR = "war"  # 戦争
    HOT_WAR = "hot_war"  # 熱戦
    MAXIMUM = "maximum"  # 最大エスカレーション


class ApprovalRequirement(Enum):
    NONE = "none"
    TACTICAL_COMMANDER = "tactical_commander"  # 戦術指揮官
    OPERATIONAL_COMMANDER = "operational_commander"  # 作戦指揮官
    STRATEGIC_COMMANDER = "strategic_commander"  # 戦略指揮官
    NATIONAL_COMMAND = "national_command"  # 国家指揮官
    ALLIED_APPROVAL = "allied_approval"  # 同盟国承認


class ActionType(Enum):
    # Requires no approval
    ROUTINE_PATROL = "routine_patrol"
    LOCAL_RECON = "local_recon"
    DEFENSIVE_POSITION = "defensive_position"

    # Requires tactical commander
    SMALL_RAID = "small_raid"
    ARTILLERY_STRIKE = "artillery_strike"
    LIMITED_AIR_STRIKE = "limited_air_strike"

    # Requires operational commander
    LARGE_OFFENSIVE = "large_offensive"
    MAJOR_AIR_OPERATION = "major_air_operation"
    MISSILE_ATTACK = "missile_attack"

    # Requires strategic/national command
    CITY_ATTACK = "city_attack"
    LARGE_BOMBING = "large_bombing"
    MASS_MISSILE_STRIKE = "mass_missile_strike"

    # Requires allied approval
    USE_CHEMICAL = "use_chemical"
    USE_NUCLEAR = "use_nuclear"
    PREEMPTIVE_STRIKE = "preemptive_strike"


class EscalationService:
    """Service for managing escalation and approval requirements"""

    # Approval requirements for each action
    ACTION_APPROVAL_REQUIREMENTS = {
        # No approval needed
        ActionType.ROUTINE_PATROL: ApprovalRequirement.NONE,
        ActionType.LOCAL_RECON: ApprovalRequirement.NONE,
        ActionType.DEFENSIVE_POSITION: ApprovalRequirement.NONE,

        # Tactical commander
        ActionType.SMALL_RAID: ApprovalRequirement.TACTICAL_COMMANDER,
        ActionType.ARTILLERY_STRIKE: ApprovalRequirement.TACTICAL_COMMANDER,
        ActionType.LIMITED_AIR_STRIKE: ApprovalRequirement.TACTICAL_COMMANDER,

        # Operational commander
        ActionType.LARGE_OFFENSIVE: ApprovalRequirement.OPERATIONAL_COMMANDER,
        ActionType.MAJOR_AIR_OPERATION: ApprovalRequirement.OPERATIONAL_COMMANDER,
        ActionType.MISSILE_ATTACK: ApprovalRequirement.OPERATIONAL_COMMANDER,

        # Strategic/national command
        ActionType.CITY_ATTACK: ApprovalRequirement.STRATEGIC_COMMANDER,
        ActionType.LARGE_BOMBING: ApprovalRequirement.STRATEGIC_COMMANDER,
        ActionType.MASS_MISSILE_STRIKE: ApprovalRequirement.NATIONAL_COMMAND,

        # Allied approval required
        ActionType.USE_CHEMICAL: ApprovalRequirement.ALLIED_APPROVAL,
        ActionType.USE_NUCLEAR: ApprovalRequirement.ALLIED_APPROVAL,
        ActionType.PREEMPTIVE_STRIKE: ApprovalRequirement.ALLIED_APPROVAL,
    }

    # Escalation thresholds
    ESCALATION_THRESHOLDS = {
        EscalationLevel.PEACETIME: 0,
        EscalationLevel.CRISIS: 20,
        EscalationLevel.CONFLICT: 40,
        EscalationLevel.WAR: 60,
        EscalationLevel.HOT_WAR: 80,
        EscalationLevel.MAXIMUM: 95,
    }

    def __init__(self, random_seed: Optional[int] = None):
        self.current_level = EscalationLevel.PEACETIME
        self.escalation_points = 0
        self.pending_approvals = []
        self.international_reactions = []

    def get_approval_requirement(self, action: str) -> tuple[ApprovalRequirement, bool]:
        """Get approval requirement for an action (action, approval_required)"""
        try:
            action_type = ActionType(action)
            required = self.ACTION_APPROVAL_REQUIREMENTS.get(
                action_type,
                ApprovalRequirement.TACTICAL_COMMANDER
            )
            return required, required != ApprovalRequirement.NONE
        except ValueError:
            return ApprovalRequirement.TACTICAL_COMMANDER, True

    def request_approval(
        self,
        action: str,
        requester_level: str,
        justification: str = ""
    ) -> dict:
        """Request approval for an action"""
        required, needs_approval = self.get_approval_requirement(action)

        if not needs_approval:
            return {
                "approved": True,
                "action": action,
                "reason": "No approval required",
            }

        # Check if requester has authority
        authority_levels = {
            ApprovalRequirement.NONE: "none",
            ApprovalRequirement.TACTICAL_COMMANDER: "tactical",
            ApprovalRequirement.OPERATIONAL_COMMANDER: "operational",
            ApprovalRequirement.STRATEGIC_COMMANDER: "strategic",
            ApprovalRequirement.NATIONAL_COMMAND: "national",
            ApprovalRequirement.ALLIED_APPROVAL: "allied",
        }

        request = {
            "id": len(self.pending_approvals) + 1,
            "action": action,
            "requester": requester_level,
            "required_level": required.value,
            "justification": justification,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "pending",
        }

        self.pending_approvals.append(request)
        return {
            "approved": False,
            "action": action,
            "reason": f"Requires {required.value} approval",
            "request_id": request["id"],
        }

    def approve_action(self, request_id: int, approver: str) -> dict:
        """Approve a pending action request"""
        for request in self.pending_approvals:
            if request["id"] == request_id:
                request["status"] = "approved"
                request["approver"] = approver
                request["approved_at"] = datetime.utcnow().isoformat()
                return {
                    "approved": True,
                    "request": request,
                }

        return {"approved": False, "reason": "Request not found"}

    def reject_action(self, request_id: int, reason: str) -> dict:
        """Reject an action request"""
        for request in self.pending_approvals:
            if request["id"] == request_id:
                request["status"] = "rejected"
                request["rejection_reason"] = reason
                request["rejected_at"] = datetime.utcnow().isoformat()
                return {
                    "rejected": True,
                    "request": request,
                }

        return {"rejected": False, "reason": "Request not found"}

    def add_escalation_points(self, points: int, reason: str = "") -> EscalationLevel:
        """Add escalation points and return new level"""
        self.escalation_points = min(100, self.escalation_points + points)

        # Determine new level
        old_level = self.current_level
        for level, threshold in sorted(
            self.ESCALATION_THRESHOLDS.items(),
            key=lambda x: x[1],
            reverse=True
        ):
            if self.escalation_points >= threshold:
                self.current_level = level
                break

        # Trigger international reaction on level change
        if old_level != self.current_level:
            self._trigger_international_reaction(old_level, self.current_level)

        return self.current_level

    def _trigger_international_reaction(
        self,
        old_level: EscalationLevel,
        new_level: EscalationLevel
    ):
        """Trigger international reaction to escalation"""
        reaction_templates = {
            (EscalationLevel.CRISIS, EscalationLevel.CONFLICT): [
                "国際社会が懸念を表明",
                "外交努力が加速",
                "各国が退避を開始",
            ],
            (EscalationLevel.CONFLICT, EscalationLevel.WAR): [
                "同盟国が出兵を検討",
                "経済制裁が発動",
                "国際平和維持軍が待機",
            ],
            (EscalationLevel.WAR, EscalationLevel.HOT_WAR): [
                "全面戦争への警戒が高まった",
                "核抑止態勢が強化",
                "一般市民の被害が拡大",
            ],
            (EscalationLevel.HOT_WAR, EscalationLevel.MAXIMUM): [
                "全面的な軍事的対立に発展",
                "国際秩序が崩壊危機",
            ],
        }

        key = (old_level, new_level)
        if key in reaction_templates:
            import random
            reaction = {
                "from_level": old_level.value,
                "to_level": new_level.value,
                "message": random.choice(reaction_templates[key]),
                "timestamp": datetime.utcnow().isoformat(),
            }
            self.international_reactions.append(reaction)

    def get_current_escalation(self) -> dict:
        """Get current escalation status"""
        return {
            "level": self.current_level.value,
            "points": self.escalation_points,
            "pending_approvals": self.pending_approvals,
            "international_reactions": self.international_reactions[-5:],  # Last 5
        }

    def calculate_action_escalation_impact(self, action: str) -> int:
        """Calculate escalation point impact of an action"""
        impact_map = {
            ActionType.ROUTINE_PATROL: 0,
            ActionType.LOCAL_RECON: 1,
            ActionType.DEFENSIVE_POSITION: 0,
            ActionType.SMALL_RAID: 3,
            ActionType.ARTILLERY_STRIKE: 5,
            ActionType.LIMITED_AIR_STRIKE: 5,
            ActionType.LARGE_OFFENSIVE: 10,
            ActionType.MAJOR_AIR_OPERATION: 12,
            ActionType.MISSILE_ATTACK: 15,
            ActionType.CITY_ATTACK: 25,
            ActionType.LARGE_BOMBING: 30,
            ActionType.MASS_MISSILE_STRIKE: 40,
            ActionType.USE_CHEMICAL: 50,
            ActionType.USE_NUCLEAR: 100,
            ActionType.PREEMPTIVE_STRIKE: 35,
        }

        try:
            action_type = ActionType(action)
            return impact_map.get(action_type, 5)
        except ValueError:
            return 5


# Service instance factory
def create_escalation_service(seed: Optional[int] = None) -> EscalationService:
    return EscalationService(random_seed=seed)
