# Sync Matrix Service Tests - CPX-SYNC
import pytest
from app.services.sync_matrix_service import (
    SyncMatrixService,
    SyncMatrixData,
    SyncMatrixEntryData,
    get_sync_matrix_service,
)


class TestSyncMatrixService:
    """Tests for Sync Matrix Service (CPX-SYNC)"""

    def setup_method(self):
        """Create a fresh service instance for each test"""
        self.service = SyncMatrixService()

    def test_create_default_matrix(self):
        """Test creating a default sync matrix"""
        matrix = self.service.create_default_matrix(game_id=1, name="Test Matrix")

        assert matrix is not None
        assert matrix.game_id == 1
        assert matrix.name == "Test Matrix"
        assert len(matrix.phases) == 4
        assert len(matrix.effects) == 4
        assert "Recon" in matrix.effects
        assert "Fires" in matrix.effects
        assert "Maneuver" in matrix.effects
        assert "Logistics" in matrix.effects

    def test_get_current_matrix(self):
        """Test getting current matrix"""
        self.service.create_default_matrix(game_id=1)

        current = self.service.get_current_matrix()
        assert current is not None
        assert current.game_id == 1

    def test_update_entry(self):
        """Test updating a matrix entry"""
        self.service.create_default_matrix(game_id=1)

        matrix = self.service.update_entry(
            phase="Phase 1",
            effect="Recon",
            value="High",
            notes="Initial reconnaissance",
            start_time="0800",
            end_time="1000"
        )

        assert matrix is not None
        entry = matrix.matrix_data["Phase 1"]["Recon"]
        assert entry["value"] == "High"
        assert entry["notes"] == "Initial reconnaissance"
        assert entry["start_time"] == "0800"
        assert entry["end_time"] == "1000"

    def test_get_entry(self):
        """Test getting a specific entry"""
        self.service.create_default_matrix(game_id=1)

        self.service.update_entry(
            phase="Phase 2",
            effect="Fires",
            value="Medium",
            notes="Artillery support"
        )

        entry = self.service.get_entry("Phase 2", "Fires")
        assert entry is not None
        assert entry["value"] == "Medium"
        assert entry["notes"] == "Artillery support"

    def test_update_entry_with_links(self):
        """Test updating entry with links to OPORD/ATO/Inject"""
        self.service.create_default_matrix(game_id=1)

        matrix = self.service.update_entry(
            phase="Phase 3",
            effect="Maneuver",
            value="Critical",
            linked_opord_id=1,
            linked_ato_mission_id=5,
            linked_inject_id="inj_001"
        )

        assert matrix is not None
        entry = matrix.matrix_data["Phase 3"]["Maneuver"]
        assert entry["linked_opord_id"] == 1
        assert entry["linked_ato_mission_id"] == 5
        assert entry["linked_inject_id"] == "inj_001"

    def test_add_phase(self):
        """Test adding a new phase"""
        self.service.create_default_matrix(game_id=1)

        matrix = self.service.add_phase("Phase 5")

        assert len(matrix.phases) == 5
        assert "Phase 5" in matrix.phases
        assert "Phase 5" in matrix.matrix_data

    def test_add_effect(self):
        """Test adding a new effect"""
        self.service.create_default_matrix(game_id=1)

        matrix = self.service.add_effect("Cyber")

        assert len(matrix.effects) == 5
        assert "Cyber" in matrix.effects
        # Check that new effect is added to all phases
        for phase in matrix.phases:
            assert "Cyber" in matrix.matrix_data[phase]

    def test_remove_phase(self):
        """Test removing a phase"""
        self.service.create_default_matrix(game_id=1)

        matrix = self.service.remove_phase("Phase 1")

        assert len(matrix.phases) == 3
        assert "Phase 1" not in matrix.phases
        assert "Phase 1" not in matrix.matrix_data

    def test_remove_effect(self):
        """Test removing an effect"""
        self.service.create_default_matrix(game_id=1)

        matrix = self.service.remove_effect("Logistics")

        assert len(matrix.effects) == 3
        assert "Logistics" not in matrix.effects
        # Check that effect is removed from all phases
        for phase in matrix.phases:
            assert "Logistics" not in matrix.matrix_data[phase]

    def test_to_dict(self):
        """Test converting matrix to dictionary"""
        self.service.create_default_matrix(game_id=1)

        self.service.update_entry(
            phase="Phase 1",
            effect="Recon",
            value="High"
        )

        matrix_dict = self.service.to_dict()

        assert matrix_dict["game_id"] == 1
        assert matrix_dict["name"] == "Default Sync Matrix"
        assert "effect_colors" in matrix_dict
        assert matrix_dict["effect_colors"]["Recon"] == "#22c55e"
        assert matrix_dict["effect_colors"]["Fires"] == "#ef4444"

    def test_export_to_csv(self):
        """Test exporting matrix to CSV"""
        self.service.create_default_matrix(game_id=1)

        self.service.update_entry(
            phase="Phase 1",
            effect="Recon",
            value="High",
            notes="Initial recon"
        )

        csv_output = self.service.export_to_csv()

        assert "Phase" in csv_output
        assert "Effect" in csv_output
        assert "Phase 1" in csv_output
        assert "Recon" in csv_output
        assert "High" in csv_output
        assert "Initial recon" in csv_output

    def test_export_to_json(self):
        """Test exporting matrix to JSON"""
        self.service.create_default_matrix(game_id=1)

        json_output = self.service.export_to_json()

        assert json_output["game_id"] == 1
        assert "phases" in json_output
        assert "effects" in json_output
        assert "matrix_data" in json_output

    def test_invalid_phase_raises_error(self):
        """Test that invalid phase raises error"""
        self.service.create_default_matrix(game_id=1)

        with pytest.raises(ValueError, match="Unknown phase"):
            self.service.update_entry(
                phase="Invalid Phase",
                effect="Recon",
                value="High"
            )

    def test_invalid_effect_raises_error(self):
        """Test that invalid effect raises error"""
        self.service.create_default_matrix(game_id=1)

        with pytest.raises(ValueError, match="Unknown effect"):
            self.service.update_entry(
                phase="Phase 1",
                effect="Invalid Effect",
                value="High"
            )

    def test_duplicate_phase_raises_error(self):
        """Test that adding duplicate phase raises error"""
        self.service.create_default_matrix(game_id=1)

        with pytest.raises(ValueError, match="Phase already exists"):
            self.service.add_phase("Phase 1")

    def test_duplicate_effect_raises_error(self):
        """Test that adding duplicate effect raises error"""
        self.service.create_default_matrix(game_id=1)

        with pytest.raises(ValueError, match="Effect already exists"):
            self.service.add_effect("Recon")

    def test_default_phases_and_effects(self):
        """Test default phases and effects constants"""
        assert len(SyncMatrixService.DEFAULT_PHASES) == 4
        assert len(SyncMatrixService.DEFAULT_EFFECTS) == 4
        assert SyncMatrixService.EFFECT_COLORS["Recon"] == "#22c55e"
        assert SyncMatrixService.EFFECT_COLORS["Fires"] == "#ef4444"
        assert SyncMatrixService.EFFECT_COLORS["Maneuver"] == "#3b82f6"
        assert SyncMatrixService.EFFECT_COLORS["Logistics"] == "#f59e0b"

    def test_format_for_display(self):
        """Test formatting matrix for display"""
        self.service.create_default_matrix(game_id=1)

        self.service.update_entry(
            phase="Phase 1",
            effect="Recon",
            value="High"
        )

        display = self.service.format_for_display()

        assert "Sync Matrix" in display
        assert "Phase 1" in display
        assert "Recon" in display
        assert "Fires" in display

    def test_set_matrix(self):
        """Test setting a matrix directly"""
        new_matrix = SyncMatrixData(
            game_id=2,
            name="Custom Matrix",
            phases=["Phase A", "Phase B"],
            effects=["Alpha", "Beta"]
        )

        self.service.set_matrix(new_matrix)
        current = self.service.get_current_matrix()

        assert current is not None
        assert current.game_id == 2
        assert current.name == "Custom Matrix"

    def test_empty_matrix_raises_error_on_update(self):
        """Test that updating without matrix raises error"""
        with pytest.raises(ValueError, match="No current matrix exists"):
            self.service.update_entry(
                phase="Phase 1",
                effect="Recon",
                value="High"
            )

    def test_empty_matrix_raises_error_on_add_phase(self):
        """Test that adding phase without matrix raises error"""
        with pytest.raises(ValueError, match="No current matrix exists"):
            self.service.add_phase("New Phase")

    def test_empty_matrix_raises_error_on_get_entry(self):
        """Test that getting entry without matrix returns None"""
        entry = self.service.get_entry("Phase 1", "Recon")
        assert entry is None


class TestSyncMatrixData:
    """Tests for SyncMatrixData dataclass"""

    def test_default_values(self):
        """Test default values"""
        matrix = SyncMatrixData(game_id=1)

        assert matrix.matrix_id is None
        assert matrix.game_id == 1
        assert matrix.name == "Default Sync Matrix"
        assert matrix.phases is not None
        assert matrix.effects is not None
        assert matrix.resolution == "turn"
        assert matrix.status == "draft"

    def test_custom_values(self):
        """Test custom values"""
        matrix = SyncMatrixData(
            game_id=1,
            name="Custom",
            phases=["P1", "P2"],
            effects=["E1"],
            resolution="hour",
            status="active"
        )

        assert matrix.name == "Custom"
        assert matrix.phases == ["P1", "P2"]
        assert matrix.effects == ["E1"]
        assert matrix.resolution == "hour"
        assert matrix.status == "active"
