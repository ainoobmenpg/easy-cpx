# Tests for RNG Service and Structured Logging
import pytest
import json
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from app.services.rng_service import RNGService, get_rng, SeedSource
from app.services.structured_logging import StructuredLogger, get_structured_logger


class TestRNGService:
    """Tests for RNG Service"""

    def test_initialization_with_seed(self):
        """Test RNG initialization with explicit seed"""
        rng = RNGService(game_id=123, initial_seed=42)
        assert rng.current_seed == 42
        assert rng.current_turn_seed is None

    def test_initialization_with_game_id(self):
        """Test RNG initialization with game_id generates deterministic seed"""
        rng1 = RNGService(game_id=100)
        rng2 = RNGService(game_id=100)
        # Same game_id should produce same seed
        assert rng1.current_seed == rng2.current_seed

    def test_different_game_ids_produce_different_seeds(self):
        """Test different game_ids produce different seeds"""
        rng1 = RNGService(game_id=100)
        rng2 = RNGService(game_id=200)
        assert rng1.current_seed != rng2.current_seed

    def test_roll_2d6_returns_valid_range(self):
        """Test 2D6 roll returns value between 2-12"""
        rng = RNGService(initial_seed=42)
        for _ in range(100):
            die1, die2, total = rng.roll_2d6()
            assert 2 <= total <= 12
            assert 1 <= die1 <= 6
            assert 1 <= die2 <= 6

    def test_reproducibility_with_same_seed(self):
        """Test same seed produces same sequence"""
        rng1 = RNGService(initial_seed=12345)
        rng2 = RNGService(initial_seed=12345)

        results1 = [rng1.roll_2d6() for _ in range(10)]
        results2 = [rng2.roll_2d6() for _ in range(10)]

        assert results1 == results2

    def test_turn_seed_is_deterministic(self):
        """Test turn seed is deterministic based on base seed and turn"""
        rng = RNGService(initial_seed=100)
        seed1 = rng.set_turn_seed(turn_number=1)
        seed2 = rng.set_turn_seed(turn_number=1)

        # Same turn should give same seed
        assert seed1 == seed2

    def test_different_turns_have_different_seeds(self):
        """Test different turns have different seeds"""
        rng = RNGService(initial_seed=100)
        seed1 = rng.set_turn_seed(turn_number=1)
        seed2 = rng.set_turn_seed(turn_number=2)

        assert seed1 != seed2

    def test_roll_1d6_returns_valid_range(self):
        """Test 1D6 roll returns value between 1-6"""
        rng = RNGService(initial_seed=42)
        for _ in range(100):
            result = rng.roll_1d6()
            assert 1 <= result <= 6

    def test_roll_dx_with_sides(self):
        """Test roll_dx with custom sides"""
        rng = RNGService(initial_seed=42)
        for _ in range(100):
            result = rng.roll_dx(10)  # 1D10
            assert 1 <= result <= 10

    def test_weighted_choice(self):
        """Test weighted random choice"""
        rng = RNGService(initial_seed=42)
        choices = ["A", "B", "C"]
        weights = [0.5, 0.3, 0.2]

        # Run many times and check distribution
        results = [rng.weighted_choice(choices, weights) for _ in range(1000)]
        count_a = results.count("A")
        count_b = results.count("B")
        count_c = results.count("C")

        # Should be roughly proportional (allow some variance)
        assert count_a > count_b > count_c

    def test_random_float_in_range(self):
        """Test random float is in specified range"""
        rng = RNGService(initial_seed=42)
        for _ in range(100):
            result = rng.random_float(5.0, 10.0)
            assert 5.0 <= result < 10.0

    def test_random_bool_probability(self):
        """Test random bool respects probability"""
        rng = RNGService(initial_seed=42)

        # 100% should always be True
        rng2 = RNGService(initial_seed=1)
        results = [rng2.random_bool(1.0) for _ in range(100)]
        assert all(results)

        # 0% should always be False
        rng3 = RNGService(initial_seed=1)
        results = [rng3.random_bool(0.0) for _ in range(100)]
        assert not any(results)

    def test_get_seed_info(self):
        """Test seed info retrieval"""
        rng = RNGService(initial_seed=100)
        rng.set_turn_seed(turn_number=1)

        info = rng.get_seed_info()

        assert "base_seed" in info
        assert "turn_seed" in info
        assert "determination_counter" in info
        assert "seed_history" in info
        assert info["base_seed"] == 100


class TestStructuredLogger:
    """Tests for Structured Logging"""

    def test_logger_initialization(self):
        """Test structured logger can be initialized"""
        logger = StructuredLogger("test")
        assert logger is not None

    def test_context_setting(self):
        """Test context can be set and retrieved"""
        logger = StructuredLogger("test")
        logger.set_context(game_id=123, turn=5)

        entry = logger._build_log_entry("test", "test_event")
        assert entry["context"]["game_id"] == 123
        assert entry["context"]["turn"] == 5

    def test_context_clearing(self):
        """Test context can be cleared"""
        logger = StructuredLogger("test")
        logger.set_context(game_id=123)
        logger.clear_context()

        entry = logger._build_log_entry("test", "test_event")
        assert entry["context"] == {}

    def test_log_entry_structure(self):
        """Test log entry has required fields"""
        logger = StructuredLogger("test")
        logger.set_context(game_id=1)

        entry = logger._build_log_entry(
            category="combat",
            event="attack",
            data={"attacker": "unit1", "defender": "unit2"}
        )

        assert "timestamp" in entry
        assert "category" in entry
        assert "event" in entry
        assert "context" in entry
        assert entry["category"] == "combat"
        assert entry["data"]["attacker"] == "unit1"

    def test_get_structured_logger_singleton(self):
        """Test get_structured_logger returns singleton"""
        logger1 = get_structured_logger()
        logger2 = get_structured_logger()
        assert logger1 is logger2


class TestReproducibility:
    """Integration tests for reproducibility"""

    def test_full_combat_sequence_reproducibility(self):
        """Test full combat sequence can be reproduced with same seed"""
        # First run
        rng1 = RNGService(initial_seed=99999)
        rng1.set_turn_seed(turn_number=1)
        results1 = [rng1.roll_2d6() for _ in range(5)]

        # Second run with same seed
        rng2 = RNGService(initial_seed=99999)
        rng2.set_turn_seed(turn_number=1)
        results2 = [rng2.roll_2d6() for _ in range(5)]

        assert results1 == results2

    def test_different_turns_produce_different_results(self):
        """Test different turns produce different results"""
        rng = RNGService(initial_seed=99999)

        rng.set_turn_seed(turn_number=1)
        results_turn1 = [rng.roll_2d6() for _ in range(5)]

        rng.set_turn_seed(turn_number=2)
        results_turn2 = [rng.roll_2d6() for _ in range(5)]

        assert results_turn1 != results_turn2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
