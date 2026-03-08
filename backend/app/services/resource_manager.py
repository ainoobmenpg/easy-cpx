# Resource Management for Operational CPX
# Tracks and manages consumable resources across the game
from enum import Enum
from typing import Optional
from dataclasses import dataclass


class ResourceCategory(Enum):
    """Categories of consumable resources"""
    AMMO = "ammo"
    FUEL = "fuel"
    READINESS = "readiness"
    INTERCEPTOR = "interceptor"
    PRECISION_MUNITIONS = "precision_munitions"
    SUPPLY = "supply"


class ResourceState(Enum):
    """State of a resource (3-stage system from v4.1)"""
    FULL = "full"
    DEPLETED = "depleted"
    EXHAUSTED = "exhausted"


@dataclass
class UnitResources:
    """Resources for a single unit"""
    ammo: ResourceState = ResourceState.FULL
    fuel: ResourceState = ResourceState.FULL
    readiness: ResourceState = ResourceState.FULL
    interceptors: int = 0  # Number of interceptor missiles
    precision_munitions: int = 0  # Number of precision-guided munitions


@dataclass
class GlobalResources:
    """Global pool of resources (for scenarios with shared supply)"""
    total_ammo: int = 1000
    total_fuel: int = 1000
    total_interceptors: int = 50
    total_precision_munitions: int = 30
    supply_points: int = 500


class ResourceManager:
    """
    Manages resource consumption and replenishment across units

    Implements the 3-stage resource system:
    - FULL: Unit has full capability
    - DEPLETED: Unit has reduced capability (50% effectiveness)
    - EXHAUSTED: Unit cannot perform resource-intensive actions
    """

    # Resource consumption rates per action
    CONSUMPTION_RATES = {
        "move": {"fuel": 1, "ammo": 0},
        "attack": {"fuel": 0, "ammo": 2},
        "defend": {"fuel": 0, "ammo": 1},
        "retreat": {"fuel": 2, "ammo": 0},
        "recon": {"fuel": 1, "ammo": 0},
        "special": {"fuel": 1, "ammo": 3},
    }

    # Effectiveness modifiers based on resource state
    EFFECTIVENESS_MODIFIERS = {
        ResourceState.FULL: 1.0,
        ResourceState.DEPLETED: 0.5,
        ResourceState.EXHAUSTED: 0.0,
    }

    def __init__(self):
        self._unit_resources: dict[int, UnitResources] = {}
        self._global_resources = GlobalResources()

    def initialize_unit(self, unit_id: int, unit_type: str = "infantry"):
        """Initialize resources for a new unit based on type"""
        resources = UnitResources()

        # Set initial resources based on unit type
        if "armor" in unit_type.lower():
            resources.fuel = ResourceState.FULL
            resources.ammo = ResourceState.FULL
        elif "artillery" in unit_type.lower():
            resources.ammo = ResourceState.FULL
            resources.fuel = ResourceState.DEPLETED
        elif "air" in unit_type.lower():
            resources.fuel = ResourceState.FULL
            resources.ammo = ResourceState.FULL
            resources.interceptors = 4
        elif "anti_air" in unit_type.lower():
            resources.interceptors = 8
            resources.ammo = ResourceState.FULL

        self._unit_resources[unit_id] = resources

    def get_unit_resources(self, unit_id: int) -> UnitResources:
        """Get resources for a unit"""
        if unit_id not in self._unit_resources:
            self.initialize_unit(unit_id)
        return self._unit_resources[unit_id]

    def can_perform_action(self, unit_id: int, action: str) -> tuple[bool, str]:
        """
        Check if a unit can perform an action based on resources

        Returns:
            (can_perform, reason)
        """
        resources = self.get_unit_resources(unit_id)
        rates = self.CONSUMPTION_RATES.get(action, {})

        # Check ammo
        ammo_needed = rates.get("ammo", 0)
        if ammo_needed > 0:
            if resources.ammo == ResourceState.EXHAUSTED:
                return False, "Ammo exhausted - cannot attack"
            elif resources.ammo == ResourceState.DEPLETED and ammo_needed > 1:
                return False, "Ammo critically low"

        # Check fuel
        fuel_needed = rates.get("fuel", 0)
        if fuel_needed > 0:
            if resources.fuel == ResourceState.EXHAUSTED:
                return False, "Fuel exhausted - cannot move"
            elif resources.fuel == ResourceState.DEPLETED and fuel_needed > 1:
                return False, "Fuel critically low"

        return True, ""

    def consume_resources(self, unit_id: int, action: str):
        """
        Consume resources for a unit action

        Uses the 3-stage system:
        FULL -> DEPLETED -> EXHAUSTED
        """
        resources = self.get_unit_resources(unit_id)
        rates = self.CONSUMPTION_RATES.get(action, {})

        # Consume fuel
        fuel_needed = rates.get("fuel", 0)
        if fuel_needed > 0:
            if resources.fuel == ResourceState.FULL:
                resources.fuel = ResourceState.DEPLETED
            elif resources.fuel == ResourceState.DEPLETED:
                resources.fuel = ResourceState.EXHAUSTED

        # Consume ammo
        ammo_needed = rates.get("ammo", 0)
        if ammo_needed > 0:
            if resources.ammo == ResourceState.FULL:
                resources.ammo = ResourceState.DEPLETED
            elif resources.ammo == ResourceState.DEPLETED:
                resources.ammo = ResourceState.EXHAUSTED

        # Consume readiness
        if resources.readiness == ResourceState.FULL:
            resources.readiness = ResourceState.DEPLETED
        elif resources.readiness == ResourceState.DEPLETED:
            resources.readiness = ResourceState.EXHAUSTED

    def get_effectiveness_modifier(self, unit_id: int) -> float:
        """
        Get the overall effectiveness modifier for a unit based on resources

        Returns:
            Modifier from 0.0 to 1.0
        """
        resources = self.get_unit_resources(unit_id)

        ammo_mod = self.EFFECTIVENESS_MODIFIERS[resources.ammo]
        fuel_mod = self.EFFECTIVENESS_MODIFIERS[resources.fuel]
        readiness_mod = self.EFFECTIVENESS_MODIFIERS[resources.readiness]

        # Use the lowest modifier (bottleneck principle)
        return min(ammo_mod, fuel_mod, readiness_mod)

    def get_resource_summary(self, unit_id: int) -> dict:
        """Get a summary of unit resources for display"""
        resources = self.get_unit_resources(unit_id)
        effectiveness = self.get_effectiveness_modifier(unit_id)

        return {
            "ammo": resources.ammo.value,
            "fuel": resources.fuel.value,
            "readiness": resources.readiness.value,
            "interceptors": resources.interceptors,
            "precision_munitions": resources.precision_munitions,
            "effectiveness": effectiveness,
            "can_attack": resources.ammo != ResourceState.EXHAUSTED,
            "can_move": resources.fuel != ResourceState.EXHAUSTED,
        }

    def use_interceptor(self, unit_id: int) -> bool:
        """Use an interceptor missile"""
        resources = self.get_unit_resources(unit_id)
        if resources.interceptors > 0:
            resources.interceptors -= 1
            return True
        return False

    def use_precision_munition(self, unit_id: int) -> bool:
        """Use a precision-guided munition"""
        resources = self.get_unit_resources(unit_id)
        if resources.precision_munitions > 0:
            resources.precision_munitions -= 1
            return True
        return False

    def replenish_unit(self, unit_id: int, resources_to_add: Optional[dict] = None):
        """
        Replenish unit resources (e.g., from supply unit)

        Args:
            resources_to_add: Dict of resources to add. If None, full replenishment.
        """
        resources = self.get_unit_resources(unit_id)

        if resources_to_add is None:
            # Full replenishment
            resources.ammo = ResourceState.FULL
            resources.fuel = ResourceState.FULL
            resources.readiness = ResourceState.FULL
        else:
            # Partial replenishment
            if "ammo" in resources_to_add:
                if resources.ammo == ResourceState.EXHAUSTED:
                    resources.ammo = ResourceState.DEPLETED
                elif resources.ammo == ResourceState.DEPLETED:
                    resources.ammo = ResourceState.FULL

            if "fuel" in resources_to_add:
                if resources.fuel == ResourceState.EXHAUSTED:
                    resources.fuel = ResourceState.DEPLETED
                elif resources.fuel == ResourceState.DEPLETED:
                    resources.fuel = ResourceState.FULL

            if "readiness" in resources_to_add:
                if resources.readiness == ResourceState.EXHAUSTED:
                    resources.readiness = ResourceState.DEPLETED
                elif resources.readiness == ResourceState.DEPLETED:
                    resources.readiness = ResourceState.FULL

            if "interceptors" in resources_to_add:
                resources.interceptors += resources_to_add["interceptors"]

            if "precision_munitions" in resources_to_add:
                resources.precision_munitions += resources_to_add["precision_munitions"]

    def get_global_resources(self) -> GlobalResources:
        """Get global resource pool"""
        return self._global_resources

    def transfer_to_global(self, resource_type: str, amount: int):
        """Transfer resources to global pool"""
        if resource_type == "ammo":
            self._global_resources.total_ammo += amount
        elif resource_type == "fuel":
            self._global_resources.total_fuel += amount
        elif resource_type == "interceptors":
            self._global_resources.total_interceptors += amount
        elif resource_type == "precision_munitions":
            self._global_resources.total_precision_munitions += amount

    def transfer_from_global(self, unit_id: int, resource_type: str, amount: int) -> bool:
        """Transfer resources from global pool to unit"""
        resources = self.get_unit_resources(unit_id)

        if resource_type == "ammo":
            if self._global_resources.total_ammo >= amount:
                self._global_resources.total_ammo -= amount
                self.replenish_unit(unit_id, {"ammo": True})
                return True
        elif resource_type == "fuel":
            if self._global_resources.total_fuel >= amount:
                self._global_resources.total_fuel -= amount
                self.replenish_unit(unit_id, {"fuel": True})
                return True

        return False


# Global resource manager instance
_resource_manager = ResourceManager()


def get_resource_manager() -> ResourceManager:
    """Get the global resource manager"""
    return _resource_manager
