# Scenario data loader
import json
import os
from typing import List, Dict, Any, Optional

SCENARIOS_DIR = os.path.dirname(__file__)


def load_scenarios() -> List[Dict[str, Any]]:
    """Load all scenarios from JSON file"""
    with open(os.path.join(SCENARIOS_DIR, 'scenarios.json'), 'r', encoding='utf-8') as f:
        return json.load(f)


def get_scenario(scenario_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific scenario by ID"""
    scenarios = load_scenarios()
    for scenario in scenarios:
        if scenario['id'] == scenario_id:
            return scenario
    return None


def validate_scenario(scenario: Dict[str, Any]) -> bool:
    """Validate scenario structure"""
    required_fields = ['id', 'name', 'description', 'difficulty', 'map_size']
    for field in required_fields:
        if field not in scenario:
            return False

    if scenario['difficulty'] not in ['easy', 'normal', 'hard']:
        return False

    if 'width' not in scenario['map_size'] or 'height' not in scenario['map_size']:
        return False

    return True
