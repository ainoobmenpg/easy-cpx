# OPORD Service Tests - SMESC Format
import pytest
from app.services.opord_service import (
    OpordService,
    OpordSituationData,
    OpordMissionData,
    OpordExecutionData,
    OpordCoordinationData,
    OpordServiceSupportData,
    OPORDData,
)


class TestOpordService:
    """Tests for OPORD service in SMESC format"""

    def test_create_default_opord(self):
        """Test creating a default OPORD"""
        service = OpordService()
        opord = service.create_default_opord(game_id=1, title="Test Operation")

        assert opord is not None
        assert opord.game_id == 1
        assert opord.title == "Test Operation"
        assert opord.classification == "unclassified"
        assert opord.situation is not None
        assert opord.mission is not None
        assert opord.execution is not None
        assert opord.coordination is not None
        assert opord.service_support is not None

    def test_get_current_opord(self):
        """Test getting current OPORD"""
        service = OpordService()
        service.create_default_opord(game_id=1)

        current = service.get_current_opord()
        assert current is not None
        assert current.game_id == 1

    def test_update_situation(self):
        """Test updating situation section"""
        service = OpordService()
        service.create_default_opord(game_id=1)

        new_enemy = "Updated enemy situation"
        service.update_situation(enemy_situation=new_enemy)

        current = service.get_current_opord()
        assert current.situation.enemy_situation == new_enemy

    def test_update_mission(self):
        """Test updating mission section"""
        service = OpordService()
        service.create_default_opord(game_id=1)

        new_task = "Updated mission task"
        service.update_mission(task=new_task)

        current = service.get_current_opord()
        assert current.mission.task == new_task

    def test_update_execution(self):
        """Test updating execution section"""
        service = OpordService()
        service.create_default_opord(game_id=1)

        new_concept = "Updated concept of operations"
        service.update_execution(concept_of_operations=new_concept)

        current = service.get_current_opord()
        assert current.execution.concept_of_operations == new_concept

    def test_update_coordination(self):
        """Test updating coordination section"""
        service = OpordService()
        service.create_default_opord(game_id=1)

        new_fire = "Updated fire support"
        service.update_coordination(fire_support=new_fire)

        current = service.get_current_opord()
        assert current.coordination.fire_support == new_fire

    def test_update_service_support(self):
        """Test updating service support section"""
        service = OpordService()
        service.create_default_opord(game_id=1)

        new_ammo = "Updated ammo supply"
        service.update_service_support(supply={"ammo": new_ammo, "fuel": "", "other": ""})

        current = service.get_current_opord()
        assert current.service_support.supply.ammo == new_ammo

    def test_format_for_display(self):
        """Test formatting OPORD for display"""
        service = OpordService()
        service.create_default_opord(game_id=1, title="Display Test")

        formatted = service.format_for_display()
        assert "OPORD: Display Test" in formatted
        assert "SITUATION" in formatted
        assert "MISSION" in formatted
        assert "EXECUTION" in formatted
        assert "COORDINATION" in formatted
        assert "SERVICE SUPPORT" in formatted

    def test_to_dict(self):
        """Test converting OPORD to dictionary"""
        service = OpordService()
        service.create_default_opord(game_id=1)

        opord_dict = service.to_dict()

        assert opord_dict["game_id"] == 1
        assert "situation" in opord_dict
        assert "mission" in opord_dict
        assert "execution" in opord_dict
        assert "coordination" in opord_dict
        assert "service_support" in opord_dict
        assert "enemy_situation" in opord_dict["situation"]
        assert "task" in opord_dict["mission"]

    def test_smesc_structure(self):
        """Test SMESC structure completeness"""
        service = OpordService()
        opord = service.create_default_opord(game_id=1)

        # Situation
        assert hasattr(opord.situation, 'enemy_situation')
        assert hasattr(opord.situation, 'friendly_situation')
        assert hasattr(opord.situation, 'terrain_impact')
        assert hasattr(opord.situation, 'weather_impact')

        # Mission
        assert hasattr(opord.mission, 'task')
        assert hasattr(opord.mission, 'purpose')
        assert hasattr(opord.mission, 'end_state')
        assert hasattr(opord.mission, 'success_criteria')

        # Execution
        assert hasattr(opord.execution, 'concept_of_operations')
        assert hasattr(opord.execution, 'phase_timeline')
        assert hasattr(opord.execution, 'tasks_by_unit')
        assert hasattr(opord.execution, 'coordination')
        assert hasattr(opord.execution, 'contingencies')
        assert hasattr(opord.execution, 'command_signal')

        # Coordination
        assert hasattr(opord.coordination, 'boundaries')
        assert hasattr(opord.coordination, 'phase_lines')
        assert hasattr(opord.coordination, 'fire_support')
        assert hasattr(opord.coordination, 'air_support')
        assert hasattr(opord.coordination, 'engineer_support')
        assert hasattr(opord.coordination, 'c2_relationships')

        # Service Support
        assert hasattr(opord.service_support, 'supply')
        assert hasattr(opord.service_support, 'maintenance')
        assert hasattr(opord.service_support, 'medical')
        assert hasattr(opord.service_support, 'transportation')
        assert hasattr(opord.service_support, 'evacuation')
        assert hasattr(opord.service_support, 'field_services')
        assert hasattr(opord.service_support, 'general_supply')

    def test_set_opord(self):
        """Test setting OPORD directly"""
        service = OpordService()

        custom_opord = OPORDData(
            opord_id="test-123",
            game_id=99,
            title="Custom OPORD",
            situation=OpordSituationData(enemy_situation="Custom enemy"),
            mission=OpordMissionData(task="Custom task"),
            execution=OpordExecutionData(concept_of_operations="Custom concept"),
            coordination=OpordCoordinationData(fire_support="Custom fire"),
            service_support=OpordServiceSupportData(maintenance="Custom maintenance")
        )

        service.set_opord(custom_opord)
        current = service.get_current_opord()

        assert current is not None
        assert current.opord_id == "test-123"
        assert current.game_id == 99
        assert current.title == "Custom OPORD"
        assert current.situation.enemy_situation == "Custom enemy"
        assert current.mission.task == "Custom task"
