# Logistics Service (CPX-7)
# Handles supply nodes, routes, convoys, and resupply cycles

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import math


class SupplyClass(str, Enum):
    """NATO supply class types"""
    CLASS_I = "class_i"  # Rations
    CLASS_III = "class_iii"  # Fuel
    CLASS_V = "class_v"  # Ammo
    CLASS_VI = "class_vi"  # Personal items
    CLASS_VII = "class_vii"  # Major end items
    CLASS_IX = "class_ix"  # Repair parts


class TransportMode(str, Enum):
    """Mode of transport for supply routes"""
    ROAD = "road"
    RAIL = "rail"
    AIR = "air"
    SEA = "sea"
    PIPELINE = "pipeline"


class SupplyRouteStatus(str, Enum):
    """Supply route status"""
    OPEN = "open"
    INTERDICTED = "interdicted"
    CUT = "cut"
    UNKNOWN = "unknown"


class SupplyNodeType(str, Enum):
    """Type of supply node"""
    DEPOT = "depot"
    FORWARD_OPERATING_BASE = "forward_operating_base"
    RAILHEAD = "railhead"
    SEAPORT = "seaport"
    AIRFIELD = "airfield"


class LogisticsStatus(str, Enum):
    """Logistics status for reporting"""
    ADEQUATE = "adequate"
    MARGINAL = "marginal"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class SupplyNode:
    """Fixed supply location"""
    id: str
    name: str
    node_type: SupplyNodeType
    x: int
    y: int
    side: str  # 'player' or 'enemy'
    # Inventory (supply points)
    class_i_points: int = 100
    class_iii_points: int = 100
    class_v_points: int = 100
    class_vi_points: int = 50
    class_vii_points: int = 20
    class_ix_points: int = 50
    capacity: int = 500
    current_capacity: int = 500
    # Status
    status: str = "operational"  # operational, damaged, destroyed
    last_resupply_turn: int = 0
    next_resupply_turn: int = 5


@dataclass
class SupplyRoute:
    """Supply route between nodes"""
    id: str
    name: str
    source_node_id: str
    destination_node_id: str
    transport_mode: TransportMode
    distance: float  # km
    status: SupplyRouteStatus = SupplyRouteStatus.OPEN
    interdiction_level: int = 0  # 0-100
    travel_time_hours: float = 24.0
    last_verified_turn: int = 0


@dataclass
class Convoy:
    """Transport unit carrying supplies"""
    id: str
    name: str
    origin_node_id: str
    destination_node_id: str
    current_x: int
    current_y: int
    transport_mode: TransportMode
    # Cargo
    class_i_points: int = 0
    class_iii_points: int = 0
    class_v_points: int = 0
    class_vi_points: int = 0
    class_ix_points: int = 0
    # Status
    status: str = "waiting"  # moving, loading, unloading, waiting, destroyed
    departure_turn: int = 0
    estimated_arrival_turn: int = 0
    actual_arrival_turn: Optional[int] = None
    route_id: str = ""


@dataclass
class UnitLogisticsStatus:
    """Logistics status for a military unit"""
    unit_id: int
    supply_level: LogisticsStatus = LogisticsStatus.ADEQUATE
    last_resupply_turn: int = 0
    next_scheduled_resupply: int = 0
    nearest_node_id: Optional[str] = None
    nearest_node_distance: Optional[float] = None
    is_on_supply_route: bool = False
    connected_to_network: bool = True


class LogisticsService:
    """
    Manages logistics network: supply nodes, routes, convoys, and resupply.

    Key functions:
    - Track supply nodes and their inventory
    - Manage supply routes and their status
    - Process convoys and deliveries
    - Calculate unit connectivity to supply network
    - Generate logistics summaries for LOGSITREP
    """

    # Default resupply cycle in turns
    DEFAULT_RESUPPLY_CYCLE = 5

    # Supply thresholds for status calculation
    STATUS_THRESHOLDS = {
        "adequate": 0.5,  # 50%+ inventory
        "marginal": 0.2,  # 20-50% inventory
        "critical": 0.0,  # <20% inventory
    }

    def __init__(self, game_id: int = 0, random_seed: Optional[int] = None):
        self.game_id = game_id
        self._supply_nodes: Dict[str, SupplyNode] = {}
        self._supply_routes: Dict[str, SupplyRoute] = {}
        self._convoys: Dict[str, Convoy] = {}
        self._unit_status: Dict[int, UnitLogisticsStatus] = {}
        self.current_turn = 0
        self._random_seed = random_seed

    # ==================== Supply Nodes ====================

    def add_supply_node(self, node: SupplyNode) -> None:
        """Add a supply node to the network"""
        self._supply_nodes[node.id] = node

    def get_supply_node(self, node_id: str) -> Optional[SupplyNode]:
        """Get a supply node by ID"""
        return self._supply_nodes.get(node_id)

    def get_player_nodes(self) -> List[SupplyNode]:
        """Get all player-owned supply nodes"""
        return [n for n in self._supply_nodes.values() if n.side == "player"]

    def get_enemy_nodes(self) -> List[SupplyNode]:
        """Get all enemy supply nodes"""
        return [n for n in self._supply_nodes.values() if n.side == "enemy"]

    def update_node_inventory(self, node_id: str, supply_class: str, amount: int) -> bool:
        """Update inventory at a supply node"""
        node = self._supply_nodes.get(node_id)
        if not node or node.status == "destroyed":
            return False

        # Update the specified supply class
        if supply_class == "class_i":
            node.class_i_points = max(0, node.class_i_points + amount)
        elif supply_class == "class_iii":
            node.class_iii_points = max(0, node.class_iii_points + amount)
        elif supply_class == "class_v":
            node.class_v_points = max(0, node.class_v_points + amount)
        elif supply_class == "class_vi":
            node.class_vi_points = max(0, node.class_vi_points + amount)
        elif supply_class == "class_ix":
            node.class_ix_points = max(0, node.class_ix_points + amount)

        # Update current capacity
        node.current_capacity = (
            node.class_i_points + node.class_iii_points + node.class_v_points +
            node.class_vi_points + node.class_vii_points + node.class_ix_points
        )
        return True

    def damage_node(self, node_id: str, damage: int = 50) -> bool:
        """Apply damage to a supply node"""
        node = self._supply_nodes.get(node_id)
        if not node:
            return False

        if node.status == "destroyed":
            return False

        # Apply damage - reduce inventory and possibly change status
        reduction = int(damage * 0.5)
        node.class_i_points = max(0, node.class_i_points - reduction)
        node.class_iii_points = max(0, node.class_iii_points - reduction)
        node.class_v_points = max(0, node.class_v_points - reduction)

        # Update status based on damage
        if damage >= 75:
            node.status = "destroyed"
            node.class_i_points = 0
            node.class_iii_points = 0
            node.class_v_points = 0
        elif damage >= 40:
            node.status = "damaged"

        node.current_capacity = (
            node.class_i_points + node.class_iii_points + node.class_v_points +
            node.class_vi_points + node.class_vii_points + node.class_ix_points
        )
        return True

    # ==================== Supply Routes ====================

    def add_supply_route(self, route: SupplyRoute) -> None:
        """Add a supply route to the network"""
        self._supply_routes[route.id] = route

    def get_supply_route(self, route_id: str) -> Optional[SupplyRoute]:
        """Get a supply route by ID"""
        return self._supply_routes.get(route_id)

    def get_routes_for_node(self, node_id: str) -> List[SupplyRoute]:
        """Get all routes connected to a node"""
        return [
            r for r in self._supply_routes.values()
            if r.source_node_id == node_id or r.destination_node_id == node_id
        ]

    def update_route_status(self, route_id: str, status: SupplyRouteStatus) -> bool:
        """Update the status of a supply route"""
        route = self._supply_routes.get(route_id)
        if not route:
            return False
        route.status = status
        return True

    def interdict_route(self, route_id: str, level: int) -> bool:
        """Apply interdiction to a route (0-100)"""
        route = self._supply_routes.get(route_id)
        if not route:
            return False
        route.interdiction_level = min(100, max(0, level))

        # Update status based on interdiction level
        if level >= 75:
            route.status = SupplyRouteStatus.CUT
        elif level >= 40:
            route.status = SupplyRouteStatus.INTERDICTED
        else:
            route.status = SupplyRouteStatus.OPEN

        return True

    def check_route_operational(self, source_id: str, dest_id: str) -> tuple[bool, SupplyRouteStatus]:
        """
        Check if there's an operational route between two nodes.
        Returns (is_operational, status)
        """
        for route in self._supply_routes.values():
            if (route.source_node_id == source_id and route.destination_node_id == dest_id) or \
               (route.source_node_id == dest_id and route.destination_node_id == source_id):
                if route.status == SupplyRouteStatus.OPEN:
                    return True, SupplyRouteStatus.OPEN
                elif route.status == SupplyRouteStatus.INTERDICTED:
                    return False, SupplyRouteStatus.INTERDICTED
                elif route.status == SupplyRouteStatus.CUT:
                    return False, SupplyRouteStatus.CUT
        return False, SupplyRouteStatus.UNKNOWN

    # ==================== Convoys ====================

    def create_convoy(self, convoy: Convoy) -> str:
        """Create a new convoy and return its ID"""
        self._convoys[convoy.id] = convoy
        return convoy.id

    def get_convoy(self, convoy_id: str) -> Optional[Convoy]:
        """Get a convoy by ID"""
        return self._convoys.get(convoy_id)

    def get_active_convoys(self) -> List[Convoy]:
        """Get all active convoys (moving or waiting)"""
        return [
            c for c in self._convoys.values()
            if c.status in ["moving", "waiting", "loading", "unloading"]
        ]

    def update_convoy_position(self, convoy_id: str, x: int, y: int) -> bool:
        """Update convoy position"""
        convoy = self._convoys.get(convoy_id)
        if not convoy or convoy.status == "destroyed":
            return False
        convoy.current_x = x
        convoy.current_y = y
        return True

    def deliver_convoy(self, convoy_id: str, turn: int) -> Dict[str, int]:
        """
        Deliver convoy cargo to destination node.
        Returns dict of delivered amounts by supply class.
        """
        convoy = self._convoys.get(convoy_id)
        if not convoy:
            return {}

        # Get destination node
        dest_node = self._supply_nodes.get(convoy.destination_node_id)
        if not dest_node or dest_node.status == "destroyed":
            return {}

        # Deliver cargo
        delivered = {
            "class_i": convoy.class_i_points,
            "class_iii": convoy.class_iii_points,
            "class_v": convoy.class_v_points,
            "class_vi": convoy.class_vi_points,
            "class_ix": convoy.class_ix_points,
        }

        # Add to destination inventory
        dest_node.class_i_points = min(dest_node.capacity, dest_node.class_i_points + convoy.class_i_points)
        dest_node.class_iii_points = min(dest_node.capacity, dest_node.class_iii_points + convoy.class_iii_points)
        dest_node.class_v_points = min(dest_node.capacity, dest_node.class_v_points + convoy.class_v_points)
        dest_node.class_vi_points = min(dest_node.capacity, dest_node.class_vi_points + convoy.class_vi_points)
        dest_node.class_ix_points = min(dest_node.capacity, dest_node.class_ix_points + convoy.class_ix_points)

        # Update node capacity
        dest_node.current_capacity = (
            dest_node.class_i_points + dest_node.class_iii_points + dest_node.class_v_points +
            dest_node.class_vi_points + dest_node.class_vii_points + dest_node.class_ix_points
        )

        # Clear convoy cargo and mark delivered
        convoy.class_i_points = 0
        convoy.class_iii_points = 0
        convoy.class_v_points = 0
        convoy.class_vi_points = 0
        convoy.class_ix_points = 0
        convoy.actual_arrival_turn = turn

        return delivered

    def destroy_convoy(self, convoy_id: str) -> bool:
        """Destroy a convoy"""
        convoy = self._convoys.get(convoy_id)
        if not convoy:
            return False
        convoy.status = "destroyed"
        return True

    # ==================== Unit Logistics Status ====================

    def get_unit_logistics_status(self, unit_id: int) -> UnitLogisticsStatus:
        """Get logistics status for a unit"""
        if unit_id not in self._unit_status:
            self._unit_status[unit_id] = UnitLogisticsStatus(
                unit_id=unit_id,
                supply_level=LogisticsStatus.ADEQUATE,
                last_resupply_turn=self.current_turn,
                next_scheduled_resupply=self.current_turn + self.DEFAULT_RESUPPLY_CYCLE,
                connected_to_network=True
            )
        return self._unit_status[unit_id]

    def update_unit_connectivity(self, unit_id: int, x: int, y: int) -> UnitLogisticsStatus:
        """Update unit's connectivity to supply network"""
        status = self.get_unit_logistics_status(unit_id)

        # Find nearest supply node
        nearest_node = None
        nearest_distance = float('inf')

        for node in self.get_player_nodes():
            if node.status == "destroyed":
                continue

            # Calculate distance
            distance = math.sqrt((node.x - x) ** 2 + (node.y - y) ** 2)

            # Check route connectivity
            is_connected = False
            for route in self.get_routes_for_node(node.id):
                if route.status == SupplyRouteStatus.OPEN:
                    is_connected = True
                    break

            # For units, also consider direct distance to node (30km range)
            if distance <= 30:
                is_connected = True

            if is_connected and distance < nearest_distance:
                nearest_node = node
                nearest_distance = distance

        if nearest_node:
            status.nearest_node_id = nearest_node.id
            status.nearest_node_distance = nearest_distance
            status.connected_to_network = True

            # Check if on a supply route (within 10km of a route)
            status.is_on_supply_route = self._is_on_supply_route(x, y)
        else:
            status.connected_to_network = False
            status.nearest_node_id = None
            status.nearest_node_distance = None

        return status

    def _is_on_supply_route(self, x: int, y: int, threshold: float = 10.0) -> bool:
        """Check if position is near a supply route"""
        for route in self._supply_routes.values():
            if route.status == SupplyRouteStatus.CUT:
                continue

            source = self.get_supply_route(route.id)
            if not source:
                continue

            source_node = self._supply_nodes.get(route.source_node_id)
            dest_node = self._supply_nodes.get(route.destination_node_id)

            if not source_node or not dest_node:
                continue

            # Calculate distance from point to line segment
            distance = self._point_to_line_distance(
                x, y,
                source_node.x, source_node.y,
                dest_node.x, dest_node.y
            )

            if distance <= threshold:
                return True

        return False

    def _point_to_line_distance(self, px: float, py: float,
                                 x1: float, y1: float,
                                 x2: float, y2: float) -> float:
        """Calculate distance from point to line segment"""
        dx = x2 - x1
        dy = y2 - y1

        if dx == 0 and dy == 0:
            return math.sqrt((px - x1) ** 2 + (py - y1) ** 2)

        t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))

        near_x = x1 + t * dx
        near_y = y1 + t * dy

        return math.sqrt((px - near_x) ** 2 + (py - near_y) ** 2)

    # ==================== Logistics Summary ====================

    def get_logistics_summary(self, turn: int) -> Dict[str, Any]:
        """Generate logistics summary for LOGSITREP"""
        player_nodes = self.get_player_nodes()

        # Calculate total inventory
        total_class_i = sum(n.class_i_points for n in player_nodes)
        total_class_iii = sum(n.class_iii_points for n in player_nodes)
        total_class_v = sum(n.class_v_points for n in player_nodes)

        # Calculate status
        max_capacity = sum(n.capacity for n in player_nodes) if player_nodes else 1

        class_iii_ratio = total_class_iii / (max_capacity * 0.3) if max_capacity > 0 else 0
        class_v_ratio = total_class_v / (max_capacity * 0.3) if max_capacity > 0 else 0

        if class_iii_ratio >= 0.5:
            class_iii_status = LogisticsStatus.ADEQUATE
        elif class_iii_ratio >= 0.2:
            class_iii_status = LogisticsStatus.MARGINAL
        else:
            class_iii_status = LogisticsStatus.CRITICAL

        if class_v_ratio >= 0.5:
            class_v_status = LogisticsStatus.ADEQUATE
        elif class_v_ratio >= 0.2:
            class_v_status = LogisticsStatus.MARGINAL
        else:
            class_v_status = LogisticsStatus.CRITICAL

        # Count routes
        routes_open = sum(1 for r in self._supply_routes.values()
                         if r.status == SupplyRouteStatus.OPEN and r.source_node_id in [n.id for n in player_nodes])
        routes_interdicted = sum(1 for r in self._supply_routes.values()
                                if r.status == SupplyRouteStatus.INTERDICTED and r.source_node_id in [n.id for n in player_nodes])
        routes_cut = sum(1 for r in self._supply_routes.values()
                        if r.status == SupplyRouteStatus.CUT and r.source_node_id in [n.id for n in player_nodes])

        # Count nodes
        nodes_operational = sum(1 for n in player_nodes if n.status == "operational")
        nodes_damaged = sum(1 for n in player_nodes if n.status == "damaged")
        nodes_destroyed = sum(1 for n in player_nodes if n.status == "destroyed")

        # Critical shortages
        critical_shortages = []
        if class_iii_status == LogisticsStatus.CRITICAL:
            critical_shortages.append("Class III (Fuel) critically low")
        if class_v_status == LogisticsStatus.CRITICAL:
            critical_shortages.append("Class V (Ammo) critically low")
        if nodes_destroyed > 0:
            critical_shortages.append(f"{nodes_destroyed} supply node(s) destroyed")

        return {
            "turn": turn,
            "total_class_i": total_class_i,
            "total_class_iii": total_class_iii,
            "total_class_v": total_class_v,
            "class_iii_status": class_iii_status.value,
            "class_v_status": class_v_status.value,
            "active_convoys": len(self.get_active_convoys()),
            "routes_open": routes_open,
            "routes_interdicted": routes_interdicted,
            "routes_cut": routes_cut,
            "nodes_operational": nodes_operational,
            "nodes_damaged": nodes_damaged,
            "nodes_destroyed": nodes_destroyed,
            "critical_shortages": critical_shortages,
        }

    # ==================== Turn Processing ====================

    def advance_turn(self, turn: int) -> List[Dict[str, Any]]:
        """Process logistics for new turn"""
        self.current_turn = turn
        events = []

        # Process convoys
        for convoy in self.get_active_convoys():
            if convoy.status == "moving":
                # Check if convoy has arrived
                if turn >= convoy.estimated_arrival_turn:
                    # Check route status - may be delayed or destroyed
                    route = self.get_supply_route(convoy.route_id)
                    if route:
                        if route.status == SupplyRouteStatus.CUT:
                            # Convoy is stranded
                            events.append({
                                "type": "supply_convoy_stranded",
                                "convoy_id": convoy.id,
                                "route_id": convoy.route_id,
                                "description": f"Convoy {convoy.name} stranded - route cut"
                            })
                            convoy.status = "waiting"
                        elif route.status == SupplyRouteStatus.INTERDICTED:
                            # Delayed
                            delay = int(route.interdiction_level / 20)
                            convoy.estimated_arrival_turn += delay
                            events.append({
                                "type": "supply_convoy_delayed",
                                "convoy_id": convoy.id,
                                "delay": delay,
                                "description": f"Convoy {convoy.name} delayed by interdiction"
                            })
                        else:
                            # Arrived
                            delivered = self.deliver_convoy(convoy.id, turn)
                            if delivered:
                                events.append({
                                    "type": "supply_delivered",
                                    "convoy_id": convoy.id,
                                    "delivered": delivered,
                                    "description": f"Convoy {convoy.name} delivered supplies"
                                })
                    else:
                        # No route - just deliver
                        delivered = self.deliver_convoy(convoy.id, turn)
                        if delivered:
                            events.append({
                                "type": "supply_delivered",
                                "convoy_id": convoy.id,
                                "delivered": delivered,
                                "description": f"Convoy {convoy.name} delivered supplies"
                            })

        # Process scheduled resupply at nodes
        for node in self.get_player_nodes():
            if turn >= node.next_resupply_turn and node.status == "operational":
                # Auto-resupply (simplified - in full game this would pull from higher echelon)
                events.append({
                    "type": "scheduled_resupply",
                    "node_id": node.id,
                    "description": f"Scheduled resupply at {node.name}"
                })
                node.next_resupply_turn = turn + self.DEFAULT_RESUPPLY_CYCLE

        return events

    # ==================== Initialization Helpers ====================

    @classmethod
    def create_default_network(cls, game_id: int = 0) -> "LogisticsService":
        """Create a default logistics network for testing"""
        service = cls(game_id=game_id, random_seed=42)

        # Create supply nodes
        depot = SupplyNode(
            id="depot_main",
            name="Main Depot",
            node_type=SupplyNodeType.DEPOT,
            x=100,
            y=100,
            side="player",
            class_i_points=200,
            class_iii_points=200,
            class_v_points=200,
            capacity=500,
            current_capacity=500,
            status="operational",
            next_resupply_turn=10
        )
        service.add_supply_node(depot)

        fob = SupplyNode(
            id="fob_forward",
            name="FOB Forward",
            node_type=SupplyNodeType.FORWARD_OPERATING_BASE,
            x=150,
            y=80,
            side="player",
            class_i_points=50,
            class_iii_points=50,
            class_v_points=50,
            capacity=200,
            current_capacity=150,
            status="operational",
            next_resupply_turn=5
        )
        service.add_supply_node(fob)

        # Create supply route
        route = SupplyRoute(
            id="route_main_fob",
            name="Main Route to FOB",
            source_node_id="depot_main",
            destination_node_id="fob_forward",
            transport_mode=TransportMode.ROAD,
            distance=60,
            status=SupplyRouteStatus.OPEN,
            interdiction_level=10,
            travel_time_hours=12,
            last_verified_turn=0
        )
        service.add_supply_route(route)

        return service


# Factory function
def create_logistics_service(game_id: int = 0, seed: Optional[int] = None) -> LogisticsService:
    """Create a new logistics service instance"""
    return LogisticsService(game_id=game_id, random_seed=seed)
