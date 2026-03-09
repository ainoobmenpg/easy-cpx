# Scenario Manager Service
# Handles scenario loading, validation, and game initialization
import random
from typing import List, Dict, Any, Optional
from app.data.scenarios import load_scenarios, get_scenario as load_scenario_by_id, validate_scenario


class ScenarioManager:
    """Service for managing game scenarios"""

    def __init__(self):
        self._scenarios_cache = None

    def load_scenarios(self) -> List[Dict[str, Any]]:
        """Load all available scenarios"""
        scenarios = load_scenarios()
        # Return without full details for list view
        return [
            {
                "id": s["id"],
                "name": s["name"],
                "description": s["description"],
                "difficulty": s["difficulty"],
                "map_size": s["map_size"]
            }
            for s in scenarios
        ]

    def get_scenario(self, scenario_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed scenario by ID"""
        return load_scenario_by_id(scenario_id)

    def validate_scenario(self, scenario: Dict[str, Any]) -> bool:
        """Validate scenario data structure"""
        return validate_scenario(scenario)

    def create_game_from_scenario(
        self,
        scenario_id: str,
        game_name: str,
        db: Any
    ) -> Dict[str, Any]:
        """Initialize a new game from scenario"""
        scenario = self.get_scenario(scenario_id)
        if not scenario:
            raise ValueError(f"Scenario {scenario_id} not found")

        if not self.validate_scenario(scenario):
            raise ValueError(f"Invalid scenario data")

        # Import here to avoid circular imports
        from app.models import Game, Unit, UnitStatus, SupplyLevel
        from app.services.initial_setup import InitialSetupService
        from app.services.terrain import generate_map_terrain, get_terrain_display_info

        # Get map dimensions from scenario
        map_width = scenario["map_size"]["width"]
        map_height = scenario["map_size"]["height"]

        # Generate terrain with scenario seed (terrain is now deterministic per scenario)
        terrain_seed = scenario.get("terrain_seed", 42)
        terrain_map = generate_map_terrain(map_width, map_height, terrain_seed)
        terrain_info = get_terrain_display_info()

        # Create game with terrain data persisted
        game = Game(
            name=game_name,
            current_turn=1,
            current_date=scenario.get("start_date", "2026-03-06"),
            current_time=scenario.get("start_time", "05:40"),
            weather=scenario.get("initial_weather", "clear"),
            phase="orders",
            is_active=True,
            scenario_id=scenario_id,  # Store scenario ID
            terrain_data={
                "map": terrain_map,
                "info": terrain_info,
                "seed": terrain_seed
            },
            map_width=map_width,
            map_height=map_height
        )
        db.add(game)
        db.commit()
        db.refresh(game)

        # Initialize setup service with terrain seed
        setup = InitialSetupService(random_seed=terrain_seed)

        # Create player units
        player_forces = scenario.get("player_forces", {})
        self._create_units(
            db, game.id, player_forces, "player",
            map_width, map_height, "defensive", setup
        )

        # Create enemy units (hidden initially)
        enemy_forces = scenario.get("enemy_forces", {})
        self._create_units(
            db, game.id, enemy_forces, "enemy",
            map_width, map_height, "offensive", setup
        )

        return {
            "game_id": game.id,
            "scenario_id": scenario_id,
            "turn": game.current_turn,
            "date": game.current_date,
            "time": game.current_time,
            "weather": game.weather,
            "objectives": scenario.get("objectives", [])
        }

    def _create_units(
        self,
        db: Any,
        game_id: int,
        forces: Dict[str, int],
        side: str,
        map_width: int,
        map_height: int,
        deployment_type: str,
        setup: Any
    ):
        """Create units based on force composition"""
        from app.models import Unit, UnitStatus, SupplyLevel

        unit_types = {
            "infantry": "infantry",
            "armor": "armor",
            "artillery": "artillery",
            "reconnaissance": "reconnaissance",
            "air_defense": "air_defense"
        }

        # Generate deployment positions
        positions = self._generate_deployment_positions(
            side, deployment_type, map_width, map_height, forces
        )

        unit_id = 1
        pos_index = 0

        for force_type, count in forces.items():
            unit_type = unit_types.get(force_type, "infantry")
            for i in range(count):
                if pos_index >= len(positions):
                    break

                pos = positions[pos_index]
                pos_index += 1

                unit = Unit(
                    game_id=game_id,
                    name=f"{side.upper()}-{force_type}-{unit_id:02d}",
                    unit_type=unit_type,
                    side=side,
                    x=pos["x"],
                    y=pos["y"],
                    status=UnitStatus.INTACT,
                    ammo=SupplyLevel.FULL,
                    fuel=SupplyLevel.FULL,
                    readiness=SupplyLevel.FULL,
                    strength=100
                )
                db.add(unit)
                unit_id += 1

        db.commit()

    def _generate_deployment_positions(
        self,
        side: str,
        deployment_type: str,
        map_width: int,
        map_height: int,
        forces: Dict[str, int]
    ) -> List[Dict[str, float]]:
        """Generate deployment positions based on side and type"""
        positions = []
        total_units = sum(forces.values())

        if side == "player":
            if deployment_type == "defensive":
                # Defensive: spread along defensive line
                start_y = map_height * 0.7
                end_y = map_height * 0.9
            else:
                # Offensive: forward positions
                start_y = map_height * 0.4
                end_y = map_height * 0.6

            # Player deploys on the left side
            start_x = map_width * 0.1
            end_x = map_width * 0.4
        else:
            # Enemy
            if deployment_type == "offensive":
                # Enemy attacking: forward positions
                start_y = map_height * 0.1
                end_y = map_height * 0.3
            else:
                # Enemy defending
                start_y = map_height * 0.3
                end_y = map_height * 0.5

            start_x = map_width * 0.6
            end_x = map_width * 0.9

        # Handle empty forces
        if total_units == 0:
            return positions

        # Generate positions in a grid pattern
        cols = max(3, int(total_units ** 0.5))
        rows = (total_units + cols - 1) // cols

        cell_width = (end_x - start_x) / cols
        cell_height = (end_y - start_y) / rows

        for i in range(total_units):
            col = i % cols
            row = i // cols

            # Add some randomness within each cell
            jitter_x = random.uniform(0, cell_width * 0.5)
            jitter_y = random.uniform(0, cell_height * 0.5)

            x = start_x + col * cell_width + cell_width / 2 + jitter_x
            y = start_y + row * cell_height + cell_height / 2 + jitter_y

            # Clamp to map bounds
            x = max(1, min(map_width - 1, x))
            y = max(1, min(map_height - 1, y))

            positions.append({"x": round(x, 1), "y": round(y, 1)})

        return positions
