# RNG Service for Operational CPX
# Provides deterministic random number generation with seed management
import random
import hashlib
from typing import Optional, Tuple, List, Any
from datetime import datetime
import os
import logging

logger = logging.getLogger("cpx")


class _RNG:
    """Thread-local random instance wrapper for isolation"""

    def __init__(self, seed: Optional[int] = None):
        self._random = random.Random(seed)

    def seed(self, seed: Optional[int]) -> None:
        """Set the seed"""
        self._random.seed(seed)

    def randint(self, a: int, b: int) -> int:
        """Generate random integer in range [a, b]"""
        return self._random.randint(a, b)

    def uniform(self, a: float, b: float) -> float:
        """Generate random float in range [a, b)"""
        return self._random.uniform(a, b)

    def random(self) -> float:
        """Generate random float in range [0, 1)"""
        return self._random.random()

    def choices(self, population: List[Any], weights: Optional[List[float]] = None, k: int = 1) -> List[Any]:
        """Randomly select from population with weights"""
        return self._random.choices(population, weights=weights, k=k)

# RNG seed sources
class SeedSource:
    """Sources for RNG seed generation"""
    GAME_ID = "game_id"
    TURN = "turn"
    MANUAL = "manual"
    ENV = "env"
    TIME = "time"


class RNGService:
    """
    Centralized RNG service for reproducible game adjudication.

    Features:
    - Seed management per game/turn/determination
    - Persistence of seeds for replay
    - CLI/env variable support for reproducibility
    """

    def __init__(self, game_id: Optional[int] = None, initial_seed: Optional[int] = None):
        self.game_id = game_id
        self._seed: Optional[int] = None
        self._turn_seed: Optional[int] = None
        self._determination_counter: int = 0
        self._seed_history: List[Tuple[int, str, int]] = []  # (turn, source, seed)

        # Initialize seed
        if initial_seed is not None:
            self._seed = initial_seed
        elif game_id is not None:
            # Generate deterministic seed from game_id
            self._seed = self._generate_seed_from_game_id(game_id)
        else:
            # Fall back to environment or random
            env_seed = os.environ.get("CPX_RNG_SEED")
            if env_seed:
                self._seed = int(env_seed)
            else:
                self._seed = int(datetime.now().timestamp()) % (10**9)

        # Create isolated RNG instance
        self._rng = _RNG(self._seed)
        logger.info(f"RNGService initialized: game_id={game_id}, seed={self._seed}")

    def _generate_seed_from_game_id(self, game_id: int) -> int:
        """Generate deterministic seed from game_id"""
        hash_input = f"cpx_game_{game_id}_{os.environ.get('CPX_SEED_SALT', 'default')}"
        return int(hashlib.md5(hash_input.encode()).hexdigest()[:8], 16)

    @property
    def current_seed(self) -> int:
        """Get current base seed"""
        return self._seed

    @property
    def current_turn_seed(self) -> Optional[int]:
        """Get current turn seed"""
        return self._turn_seed

    def set_turn_seed(self, turn_number: int, seed: Optional[int] = None) -> int:
        """
        Set seed for a specific turn.
        Returns the seed used.
        """
        if seed is not None:
            self._turn_seed = seed
        else:
            # Generate deterministic turn seed from base seed and turn number
            self._turn_seed = (self._seed * 1000 + turn_number) % (10**9)

        self._rng.seed(self._turn_seed)
        self._determination_counter = 0
        self._seed_history.append((turn_number, SeedSource.TURN, self._turn_seed))
        logger.debug(f"Turn seed set: turn={turn_number}, seed={self._turn_seed}")
        return self._turn_seed

    def reset_determination_counter(self) -> None:
        """Reset the determination counter for a new turn"""
        self._determination_counter = 0

    def roll_2d6(self, context: Optional[str] = None) -> Tuple[int, int, int]:
        """
        Roll 2D6 (two six-sided dice).

        Returns:
            Tuple of (die1, die2, total)
        """
        die1 = self._rng.randint(1, 6)
        die2 = self._rng.randint(1, 6)
        total = die1 + die2
        self._determination_counter += 1

        if context:
            logger.debug(f"2D6 roll [{context}]: {die1}+{die2}={total}")

        return (die1, die2, total)

    def roll_1d6(self, context: Optional[str] = None) -> int:
        """Roll 1D6 (one six-sided die)"""
        result = self._rng.randint(1, 6)
        self._determination_counter += 1

        if context:
            logger.debug(f"1D6 roll [{context}]: {result}")

        return result

    def roll_dx(self, sides: int, context: Optional[str] = None) -> int:
        """Roll XdY (sides-sided die)"""
        result = self._rng.randint(1, sides)
        self._determination_counter += 1

        if context:
            logger.debug(f"1D{sides} roll [{context}]: {result}")

        return result

    def weighted_choice(
        self,
        choices: List[Any],
        weights: List[float],
        context: Optional[str] = None
    ) -> Any:
        """Make a weighted random choice"""
        result = self._rng.choices(choices, weights=weights, k=1)[0]
        self._determination_counter += 1

        if context:
            logger.debug(f"Weighted choice [{context}]: {result}")

        return result

    def random_float(self, min_val: float = 0.0, max_val: float = 1.0) -> float:
        """Get random float in range [min_val, max_val)"""
        return self._rng.uniform(min_val, max_val)

    def random_bool(self, probability: float = 0.5) -> bool:
        """Get random boolean with given probability"""
        return self._rng.random() < probability

    def get_seed_info(self) -> dict:
        """Get current seed information"""
        return {
            "base_seed": self._seed,
            "turn_seed": self._turn_seed,
            "determination_counter": self._determination_counter,
            "seed_history": self._seed_history
        }

    @classmethod
    def create_from_env(cls) -> "RNGService":
        """Create RNGService from environment variables"""
        seed = os.environ.get("CPX_RNG_SEED")
        game_id = os.environ.get("CPX_GAME_ID")

        kwargs = {}
        if seed:
            kwargs["initial_seed"] = int(seed)
        if game_id:
            kwargs["game_id"] = int(game_id)

        return cls(**kwargs)


# Global RNG instance (for backward compatibility)
_global_rng: Optional[RNGService] = None


def get_rng(game_id: Optional[int] = None, seed: Optional[int] = None) -> RNGService:
    """Get or create global RNG service"""
    global _global_rng
    if _global_rng is None:
        _global_rng = RNGService(game_id=game_id, initial_seed=seed)
    return _global_rng


def reset_rng() -> None:
    """Reset global RNG"""
    global _global_rng
    _global_rng = None
