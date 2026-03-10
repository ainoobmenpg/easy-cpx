# Fire Support & Airspace Constraints Service
# Evaluates FSCL, No-Fire, ROZ, and other airspace restrictions in adjudication
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.models import ControlMeasure, ArcadeUnit, Game


class FiresConstraintService:
    """Service for evaluating fire support and airspace constraints"""

    def __init__(self, db: Session):
        self.db = db

    def get_control_measures(self, game_id: int) -> Dict[str, List[Dict]]:
        """Get all control measures for a game, grouped by type"""
        measures = self.db.query(ControlMeasure).filter(
            ControlMeasure.game_id == game_id
        ).all()

        result = {
            "phase_lines": [],
            "boundaries": [],
            "airspaces": []
        }

        for m in measures:
            data = {
                "id": m.id,
                "name": m.name,
                "points": m.points,
                "color": m.color,
                "line_style": m.line_style,
                "status": getattr(m, 'status', 'active')
            }

            if m.measure_type == "phase_line":
                data["status"] = m.status
                result["phase_lines"].append(data)
            elif m.measure_type == "boundary":
                data["owning_side"] = m.owning_side
                result["boundaries"].append(data)
            elif m.measure_type == "airspace":
                data["airspace_type"] = m.airspace_type
                data["altitude_low"] = m.altitude_low
                data["altitude_high"] = m.altitude_high
                result["airspaces"].append(data)

        return result

    def is_point_in_boundary(self, x: float, y: float, boundary: Dict) -> bool:
        """Check if a point is within a boundary (simple point-in-polygon)"""
        points = boundary.get("points", [])
        if len(points) < 3:
            return False

        # Simple ray casting algorithm
        n = len(points)
        inside = False
        j = n - 1

        for i in range(n):
            xi, yi = points[i]
            xj, yj = points[j]

            if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
                inside = not inside
            j = i

        return inside

    def check_fscl_violation(
        self,
        shooter_x: float,
        shooter_y: float,
        target_x: float,
        target_y: float,
        game_id: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if firing crosses a Fire Support Coordination Line (FSCL).
        Returns (is_violation, reason)
        """
        # Get boundaries
        boundaries = self.db.query(ControlMeasure).filter(
            ControlMeasure.game_id == game_id,
            ControlMeasure.measure_type == "boundary",
            ControlMeasure.name.ilike("%FSCL%")
        ).all()

        if not boundaries:
            return False, None

        for boundary in boundaries:
            # Check if shooter and target are on different sides
            shooter_in = self.is_point_in_boundary(shooter_x, shooter_y, {
                "points": boundary.points
            })
            target_in = self.is_point_in_boundary(target_x, target_y, {
                "points": boundary.points
            })

            if shooter_in != target_in:
                return True, f"Fires cross FSCL '{boundary.name}'"

        return False, None

    def check_no_fire_zone(
        self,
        target_x: float,
        target_y: float,
        game_id: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if target is in a No-Fire Zone (NFZ).
        Returns (is_blocked, reason)
        """
        airspaces = self.db.query(ControlMeasure).filter(
            ControlMeasure.game_id == game_id,
            ControlMeasure.measure_type == "airspace",
            ControlMeasure.airspace_type.in_(["no_fire", "restricted"])
        ).all()

        for airspace in airspaces:
            if self.is_point_in_boundary(target_x, target_y, {
                "points": airspace.points
            }):
                return True, f"Target in {airspace.airspace_type} zone '{airspace.name}'"

        return False, None

    def check_roz_violation(
        self,
        unit_x: float,
        unit_y: float,
        unit_type: str,
        game_id: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if unit is in a Restricted Operations Zone (ROZ).
        Only applies to certain unit types.
        """
        # ROZ mainly affects aircraft and helicopters
        restricted_types = ["aircraft", "attack_helo", "transport_helo", "uav"]

        if unit_type not in restricted_types:
            return False, None

        airspaces = self.db.query(ControlMeasure).filter(
            ControlMeasure.game_id == game_id,
            ControlMeasure.measure_type == "airspace",
            ControlMeasure.airspace_type.in_(["roz", "no_fly"])
        ).all()

        for airspace in airspaces:
            if self.is_point_in_boundary(unit_x, unit_y, {
                "points": airspace.points
            }):
                return True, f"{unit_type} in ROZ '{airspace.name}'"

        return False, None

    def apply_fires_constraints(
        self,
        shooter: ArcadeUnit,
        target_x: float,
        target_y: float,
        game_id: int,
        has_coordination: bool = False
    ) -> Dict[str, Any]:
        """
        Apply all fire support constraints.

        Returns:
            Dict with:
                - allowed: bool
                - modifier: int (penalty applied)
                - reason: str (if not allowed or penalized)
                - outcome: str (success/partial/failed/blocked)
        """
        result = {
            "allowed": True,
            "modifier": 0,
            "reason": None,
            "outcome": "success"
        }

        # Check FSCL crossing
        fscl_violation, fscl_reason = self.check_fscl_violation(
            shooter.x, shooter.y, target_x, target_y, game_id
        )

        if fscl_violation:
            if not has_coordination:
                # Without prior coordination, apply penalty
                result["modifier"] -= 2
                result["reason"] = fscl_reason
                result["outcome"] = "partial"
            else:
                # With coordination, minor penalty
                result["modifier"] -= 1
                result["reason"] = fscl_reason

        # Check No-Fire Zone
        nfz_blocked, nfz_reason = self.check_no_fire_zone(target_x, target_y, game_id)

        if nfz_blocked:
            result["allowed"] = False
            result["reason"] = nfz_reason
            result["outcome"] = "blocked"

        # Check ROZ for aircraft
        roz_violation, roz_reason = self.check_roz_violation(
            target_x, target_y, shooter.unit_type, game_id
        )

        if roz_violation:
            result["allowed"] = False
            result["reason"] = (result["reason"] + "; " + roz_reason) if result["reason"] else roz_reason
            result["outcome"] = "blocked"

        return result


def get_fires_constraint_service(db: Session) -> FiresConstraintService:
    """Factory function to get fires constraint service"""
    return FiresConstraintService(db)
