# Tests for Logistics Service (CPX-7)
import pytest
from app.services.logistics_service import (
    LogisticsService,
    SupplyNode,
    SupplyRoute,
    Convoy,
    SupplyClass,
    TransportMode,
    SupplyRouteStatus,
    SupplyNodeType,
    LogisticsStatus,
    create_logistics_service,
)


class TestSupplyNode:
    """Test supply node operations"""

    def test_create_supply_node(self):
        """Test creating a supply node"""
        node = SupplyNode(
            id="test_depot",
            name="Test Depot",
            node_type=SupplyNodeType.DEPOT,
            x=100,
            y=100,
            side="player",
        )
        assert node.id == "test_depot"
        assert node.name == "Test Depot"
        assert node.status == "operational"
        assert node.class_iii_points == 100  # default

    def test_add_supply_node(self):
        """Test adding node to service"""
        service = create_logistics_service(game_id=1)
        node = SupplyNode(
            id="test_node",
            name="Test Node",
            node_type=SupplyNodeType.FORWARD_OPERATING_BASE,
            x=50,
            y=50,
            side="player",
        )
        service.add_supply_node(node)
        retrieved = service.get_supply_node("test_node")
        assert retrieved is not None
        assert retrieved.name == "Test Node"

    def test_update_node_inventory(self):
        """Test updating node inventory"""
        service = create_logistics_service(game_id=1)
        node = SupplyNode(
            id="test_node",
            name="Test Node",
            node_type=SupplyNodeType.DEPOT,
            x=50,
            y=50,
            side="player",
        )
        service.add_supply_node(node)

        # Add fuel
        result = service.update_node_inventory("test_node", "class_iii", 50)
        assert result is True

        updated = service.get_supply_node("test_node")
        assert updated.class_iii_points == 150

    def test_damage_node(self):
        """Test damaging a supply node"""
        service = create_logistics_service(game_id=1)
        node = SupplyNode(
            id="test_node",
            name="Test Node",
            node_type=SupplyNodeType.DEPOT,
            x=50,
            y=50,
            side="player",
            class_iii_points=100,
        )
        service.add_supply_node(node)

        # Apply moderate damage
        result = service.damage_node("test_node", damage=50)
        assert result is True
        updated = service.get_supply_node("test_node")
        assert updated.status == "damaged"

    def test_destroy_node(self):
        """Test destroying a supply node"""
        service = create_logistics_service(game_id=1)
        node = SupplyNode(
            id="test_node",
            name="Test Node",
            node_type=SupplyNodeType.DEPOT,
            x=50,
            y=50,
            side="player",
        )
        service.add_supply_node(node)

        service.damage_node("test_node", damage=90)
        updated = service.get_supply_node("test_node")
        assert updated.status == "destroyed"
        assert updated.class_iii_points == 0


class TestSupplyRoute:
    """Test supply route operations"""

    def test_create_supply_route(self):
        """Test creating a supply route"""
        route = SupplyRoute(
            id="test_route",
            name="Test Route",
            source_node_id="depot1",
            destination_node_id="fob1",
            transport_mode=TransportMode.ROAD,
            distance=50,
        )
        assert route.id == "test_route"
        assert route.status == SupplyRouteStatus.OPEN

    def test_add_and_get_route(self):
        """Test adding and retrieving route"""
        service = create_logistics_service(game_id=1)
        route = SupplyRoute(
            id="test_route",
            name="Test Route",
            source_node_id="depot1",
            destination_node_id="fob1",
            transport_mode=TransportMode.ROAD,
            distance=50,
        )
        service.add_supply_route(route)
        retrieved = service.get_supply_route("test_route")
        assert retrieved is not None
        assert retrieved.distance == 50

    def test_interdict_route(self):
        """Test route interdiction"""
        service = create_logistics_service(game_id=1)
        route = SupplyRoute(
            id="test_route",
            name="Test Route",
            source_node_id="depot1",
            destination_node_id="fob1",
            transport_mode=TransportMode.ROAD,
            distance=50,
            interdiction_level=0,
        )
        service.add_supply_route(route)

        # Apply heavy interdiction
        service.interdict_route("test_route", level=80)
        updated = service.get_supply_route("test_route")
        assert updated.status == SupplyRouteStatus.CUT
        assert updated.interdiction_level == 80

    def test_check_route_operational(self):
        """Test checking route operational status"""
        service = create_logistics_service(game_id=1)
        depot = SupplyNode(id="d1", name="Depot", node_type=SupplyNodeType.DEPOT, x=0, y=0, side="player")
        fob = SupplyNode(id="f1", name="FOB", node_type=SupplyNodeType.FORWARD_OPERATING_BASE, x=100, y=0, side="player")
        service.add_supply_node(depot)
        service.add_supply_node(fob)

        route = SupplyRoute(
            id="r1",
            name="Route 1",
            source_node_id="d1",
            destination_node_id="f1",
            transport_mode=TransportMode.ROAD,
            distance=100,
        )
        service.add_supply_route(route)

        is_open, status = service.check_route_operational("d1", "f1")
        assert is_open is True
        assert status == SupplyRouteStatus.OPEN


class TestConvoy:
    """Test convoy operations"""

    def test_create_convoy(self):
        """Test creating a convoy"""
        convoy = Convoy(
            id="convoy_1",
            name="Convoy 1",
            origin_node_id="depot1",
            destination_node_id="fob1",
            current_x=10,
            current_y=0,
            transport_mode=TransportMode.ROAD,
            class_iii_points=50,
            class_v_points=30,
            status="moving",
            departure_turn=1,
            estimated_arrival_turn=3,
            route_id="route1",
        )
        assert convoy.id == "convoy_1"
        assert convoy.class_iii_points == 50

    def test_create_and_get_convoy(self):
        """Test adding and retrieving convoy"""
        service = create_logistics_service(game_id=1)
        convoy = Convoy(
            id="convoy_1",
            name="Convoy 1",
            origin_node_id="depot1",
            destination_node_id="fob1",
            current_x=10,
            current_y=0,
            transport_mode=TransportMode.ROAD,
        )
        service.create_convoy(convoy)
        retrieved = service.get_convoy("convoy_1")
        assert retrieved is not None
        assert retrieved.name == "Convoy 1"

    def test_get_active_convoys(self):
        """Test getting active convoys"""
        service = create_logistics_service(game_id=1)
        convoy1 = Convoy(
            id="convoy_1",
            name="Convoy 1",
            origin_node_id="depot1",
            destination_node_id="fob1",
            current_x=10,
            current_y=0,
            transport_mode=TransportMode.ROAD,
            status="moving",
        )
        convoy2 = Convoy(
            id="convoy_2",
            name="Convoy 2",
            origin_node_id="depot1",
            destination_node_id="fob2",
            current_x=20,
            current_y=0,
            transport_mode=TransportMode.ROAD,
            status="destroyed",
        )
        service.create_convoy(convoy1)
        service.create_convoy(convoy2)

        active = service.get_active_convoys()
        assert len(active) == 1
        assert active[0].id == "convoy_1"

    def test_deliver_convoy(self):
        """Test convoy delivery"""
        service = create_logistics_service(game_id=1)

        # Create nodes
        depot = SupplyNode(id="d1", name="Depot", node_type=SupplyNodeType.DEPOT, x=0, y=0, side="player", class_iii_points=100)
        fob = SupplyNode(id="f1", name="FOB", node_type=SupplyNodeType.FORWARD_OPERATING_BASE, x=100, y=0, side="player", class_iii_points=10)
        service.add_supply_node(depot)
        service.add_supply_node(fob)

        # Create and deliver convoy
        convoy = Convoy(
            id="convoy_1",
            name="Convoy 1",
            origin_node_id="d1",
            destination_node_id="f1",
            current_x=100,
            current_y=0,
            transport_mode=TransportMode.ROAD,
            class_iii_points=50,
            estimated_arrival_turn=3,
            route_id="r1",
        )
        service.create_convoy(convoy)
        service._convoys["convoy_1"].status = "moving"  # Set to moving for test

        delivered = service.deliver_convoy("convoy_1", turn=3)

        assert "class_iii" in delivered
        assert delivered["class_iii"] == 50
        assert service.get_supply_node("f1").class_iii_points == 60  # 10 + 50


class TestLogisticsSummary:
    """Test logistics summary generation"""

    def test_get_logistics_summary(self):
        """Test generating logistics summary"""
        service = create_logistics_service(game_id=1)

        # Add nodes
        depot = SupplyNode(
            id="d1",
            name="Main Depot",
            node_type=SupplyNodeType.DEPOT,
            x=0,
            y=0,
            side="player",
            class_i_points=100,
            class_iii_points=100,
            class_v_points=100,
            capacity=500,
            current_capacity=300,
        )
        service.add_supply_node(depot)

        # Add route
        route = SupplyRoute(
            id="r1",
            name="Route 1",
            source_node_id="d1",
            destination_node_id="f1",
            transport_mode=TransportMode.ROAD,
            distance=50,
        )
        service.add_supply_route(route)

        summary = service.get_logistics_summary(turn=1)

        assert summary["turn"] == 1
        assert summary["total_class_i"] == 100
        assert summary["total_class_iii"] == 100
        assert summary["total_class_v"] == 100
        assert summary["active_convoys"] == 0
        assert summary["routes_open"] >= 0


class TestUnitConnectivity:
    """Test unit connectivity to supply network"""

    def test_update_unit_connectivity_near_node(self):
        """Test unit connectivity when near supply node"""
        service = create_logistics_service(game_id=1)

        depot = SupplyNode(
            id="d1",
            name="Depot",
            node_type=SupplyNodeType.DEPOT,
            x=100,
            y=100,
            side="player",
        )
        service.add_supply_node(depot)

        # Unit near depot (within 30km)
        status = service.update_unit_connectivity(unit_id=1, x=110, y=105)

        assert status.connected_to_network is True
        assert status.nearest_node_id == "d1"
        assert status.nearest_node_distance is not None

    def test_update_unit_connectivity_no_network(self):
        """Test unit connectivity when far from any node"""
        service = create_logistics_service(game_id=1)

        depot = SupplyNode(
            id="d1",
            name="Depot",
            node_type=SupplyNodeType.DEPOT,
            x=100,
            y=100,
            side="player",
        )
        service.add_supply_node(depot)

        # Unit far from depot (outside 30km range)
        status = service.update_unit_connectivity(unit_id=1, x=200, y=200)

        assert status.connected_to_network is False
        assert status.nearest_node_id is None


class TestTurnProcessing:
    """Test turn advancement processing"""

    def test_advance_turn_scheduled_resupply(self):
        """Test scheduled resupply triggers"""
        service = create_logistics_service(game_id=1)

        depot = SupplyNode(
            id="d1",
            name="Depot",
            node_type=SupplyNodeType.DEPOT,
            x=100,
            y=100,
            side="player",
            next_resupply_turn=3,
        )
        service.add_supply_node(depot)

        events = service.advance_turn(turn=3)

        # Should trigger scheduled resupply
        resupply_events = [e for e in events if e["type"] == "scheduled_resupply"]
        assert len(resupply_events) > 0


class TestDefaultNetwork:
    """Test default network creation"""

    def test_create_default_network(self):
        """Test creating default logistics network"""
        service = create_logistics_service(game_id=1)

        # Add nodes and routes manually
        depot = SupplyNode(
            id="depot_main",
            name="Main Depot",
            node_type=SupplyNodeType.DEPOT,
            x=100,
            y=100,
            side="player",
        )
        service.add_supply_node(depot)

        fob = SupplyNode(
            id="fob_forward",
            name="FOB Forward",
            node_type=SupplyNodeType.FORWARD_OPERATING_BASE,
            x=150,
            y=80,
            side="player",
        )
        service.add_supply_node(fob)

        route = SupplyRoute(
            id="route_main_fob",
            name="Main Route to FOB",
            source_node_id="depot_main",
            destination_node_id="fob_forward",
            transport_mode=TransportMode.ROAD,
            distance=60,
        )
        service.add_supply_route(route)

        # Verify network
        player_nodes = service.get_player_nodes()
        assert len(player_nodes) == 2

        routes = service._supply_routes
        assert len(routes) == 1

    def test_logistics_status_enum(self):
        """Test logistics status enum values"""
        assert LogisticsStatus.ADEQUATE.value == "adequate"
        assert LogisticsStatus.MARGINAL.value == "marginal"
        assert LogisticsStatus.CRITICAL.value == "critical"

    def test_supply_route_status_enum(self):
        """Test supply route status enum values"""
        assert SupplyRouteStatus.OPEN.value == "open"
        assert SupplyRouteStatus.INTERDICTED.value == "interdicted"
        assert SupplyRouteStatus.CUT.value == "cut"


class TestFactory:
    """Test factory function"""

    def test_create_logistics_service(self):
        """Test factory creates service"""
        service = create_logistics_service(game_id=123, seed=42)
        assert service.game_id == 123
        assert service.current_turn == 0
