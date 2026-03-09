# Architecture

## System Overview

Operational CPX is a full-stack web application with a Python backend and Next.js frontend.

```
┌─────────────────────────────────────────────────────────┐
│                     Frontend (Next.js)                   │
│  ┌─────────┐  ┌──────────┐  ┌─────────────────────┐  │
│  │  Game   │  │  Map     │  │   SITREP Display    │  │
│  │  Page   │  │Component │  │                     │  │
│  └────┬────┘  └────┬─────┘  └──────────┬──────────┘  │
│       │            │                    │              │
│       └────────────┼────────────────────┘              │
│                    │                                   │
│              ┌─────▼─────┐                           │
│              │   API      │                           │
│              │   Client   │                           │
│              └─────┬─────┘                           │
└────────────────────┼───────────────────────────────────┘
                     │ HTTP/REST
┌────────────────────┼───────────────────────────────────┐
│                    │       Backend (FastAPI)           │
│              ┌─────▼─────┐                           │
│              │   Routes   │                           │
│              │  /api/*    │                           │
│              └─────┬─────┘                           │
│                    │                                   │
│    ┌───────────────┼───────────────┐                  │
│    │               │               │                  │
│ ┌──▼───┐    ┌─────▼─────┐   ┌─────▼─────┐          │
│ │ Order │    │  Game     │   │   AI      │          │
│ │Parser │    │  State    │   │  Client   │          │
│ └──┬───┘    └─────┬─────┘   └─────┬─────┘          │
│    │              │               │                  │
│    │         ┌────▼────┐         │                  │
│    │         │Rule     │         │                  │
│    │         │Engine   │◄────────┘                  │
│    │         │(Adjudi- │                            │
│    │         │ cation)  │                            │
│    │         └────┬────┘                            │
│    │              │                                  │
│ ┌──▼───┐    ┌────▼────┐   ┌───────┐               │
│ │Terrain│    │Database │   │Services│               │
│ │Effects│    │(SQLite/ │   │(Various│               │
│ └───────┘    │Postgres)│   │Logic) │               │
│              └─────────┘   └───────┘               │
└───────────────────────────────────────────────────────┘
```

## Component Responsibilities

### Frontend

| Component | Responsibility |
|-----------|----------------|
| GamePage | Main game UI container |
| MapComponent | SVG-based map rendering |
| UnitList | Unit sidebar display |
| OrderInput | Command input form |
| SITREPDisplay | Situation report rendering |
| TurnLog | Battle log display |

### Backend Services

| Service | Responsibility |
|---------|----------------|
| `adjudication.py` | Core rule engine - resolves orders |
| `ai_client.py` | MiniMax M2.5 API integration |
| `terrain.py` | Terrain effects calculation |
| `weather_effects.py` | Weather/time modifiers |
| `map_renderer.py` | Text map generation |
| `excon_ai.py` | Enemy AI behavior |
| `sitrep_generator.py` | SITREP text generation |
| `commander_order_service.py` | High-level command management |
| `reporting.py` | Reporting requirement tracking |
| `friction_events.py` | Random event generation |
| `intelligence.py` | Intel accuracy simulation |
| `escalation.py` | Escalation level management |

### API Routes

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/games/` | POST | Create game |
| `/api/games/{game_id}` | GET | Get game by ID |
| `/api/games/{game_id}/units` | GET | Get all units for a game |
| `/api/games/{game_id}/units/` | POST | Create unit for a game |
| `/api/parse-order` | POST | Parse player order (AI) |
| `/api/orders/` | POST | Submit order |
| `/api/advance-turn` | POST | Process turn |
| `/api/games/{game_id}/state` | GET | Get game state (Fog of War applied) |
| `/api/games/{game_id}/sitrep` | GET | Get SITREP |
| `/api/games/{game_id}/debriefing` | GET | Get game debriefing |
| `/api/games/start` | POST | Start new game with scenario |
| `/api/games/{game_id}/end` | POST | End game |
| `/api/units/{unit_id}/move` | POST | Move unit |
| `/api/scenarios` | GET | List scenarios |
| `/api/scenarios/{scenario_id}` | GET | Get scenario details |

## Data Models

### Core Entities

```
Game
├── id: Integer
├── name: String
├── current_turn: Integer
├── current_date: String
├── current_time: String
├── weather: String
├── phase: String
└── is_active: Boolean

Unit
├── id: Integer
├── game_id: ForeignKey
├── name: String
├── unit_type: String
├── side: String (player/enemy)
├── x, y: Float (position)
├── status: Enum (INTACT, DAMAGED, etc.)
├── ammo, fuel, readiness: Enum
├── strength: Integer (0-100)
├── interceptors: Integer
└── precision_munitions: Integer

Order
├── id: Integer
├── game_id: ForeignKey
├── unit_id: ForeignKey
├── order_type: Enum
├── order_level: Enum (TACTICAL/OPERATIONAL/STRATEGIC)
├── intent: Text
├── location_x, location_y: Float
├── parsed_order: JSON
├── result: JSON
└── outcome: String

Turn
├── id: Integer
├── game_id: ForeignKey
├── turn_number: Integer
├── time: String
├── weather: String
├── sitrep: JSON
└── excon_orders: JSON

CommanderOrder
├── id: Integer
├── game_id: ForeignKey
├── intent: Text
├── mission: Text
├── constraints: Text
├── roe: Text
├── priorities: JSON
├── time_limit: String
├── available_forces: JSON
├── reporting_requirements: JSON
└── status: String
```

## AI Integration

### Order Parser

Input: Japanese text (e.g., "前進せよ")
Output: Structured JSON with order type, target, intent

### Referee Writer

Input: Adjudication result JSON
Output: SITREP narrative text

### ExCon Director

Input: Game state summary
Output: Enemy command intent updates

## Fog of War

The system maintains two views of the battlefield:

1. **True State**: Actual unit positions and status
2. **Player View**: What the player has observed

Intelligence is gathered through:
- Direct combat contact
- Reconnaissance units
- Aerial observation
- Signals intelligence

## State Management

### Backend

- RuleEngine manages game state transitions
- Database persistence via SQLAlchemy
- Session-based API requests

### Frontend

- React useState for local state
- Fetch API for backend communication
- Real-time updates on turn advancement

---

## Arcade Mode (Light Design)

### Overview

Arcade Mode is a simplified variant of Operational CPX designed for quick play sessions (15-30 minutes). It uses a fixed 12x8 grid map and simplified 2D6 dice mechanics instead of the full simulation engine.

### Game Mode Flag

The `Game` model includes a `game_mode` field to switch between:

| Mode | Value | Description |
|------|-------|-------------|
| Simulation | `simulation` | Full rule engine with terrain, weather, supply, etc. |
| Arcade | `arcade` | Simplified 2D6 rules with fixed grid |

### Arcade Unit Model

```python
ArcadeUnit
├── id: Integer
├── game_id: ForeignKey
├── name: String
├── unit_type: String  # infantry, armor, artillery, air_defense, recon, support
├── side: String  # player, enemy
├── x: Integer  # Grid position (0-11)
├── y: Integer  # Grid position (0-7)
├── strength: Integer  # 0-10 (simplified from 0-100)
├── can_move: Boolean  # Action available
├── can_attack: Boolean  # Attack available
└── has_supplied: Boolean  # Supply action used this turn
```

### Conversion Utilities

The system provides utilities to convert between Simulation and Arcade models:

- `to_arcade_position(x, y)` - Convert simulation coordinates to 12x8 grid
- `to_simulation_position(arcade_x, arcade_y)` - Convert grid to simulation coordinates
- `arcade_unit_type(unit_type)` - Simplify unit type (infantry/armor/artillery)
- `to_arcade_strength(strength)` - Convert 0-100 to 0-10
- `from_arcade_strength(arcade_strength)` - Convert 0-10 to 0-100
- `is_arcade_game(game_mode)` - Check if game is in arcade mode

### Arcade Map Size

Fixed 12x8 grid (96 cells total):
- Width: 12 cells
- Height: 8 cells
- Used for both display and gameplay

### Key Differences

| Feature | Simulation | Arcade |
|---------|------------|--------|
| Map Size | Variable (50x30 default) | Fixed 12x8 |
| Movement | Terrain-based costs | 1 cell per move |
| Combat | Detailed damage calculation | 2D6 + modifiers |
| Supply | Ammo/Fuel/Readiness tracking | Simplified action economy |
| Units | 10+ unit types | 3 simplified types |
| Turns | Variable phase structure | Simple: orders -> resolve -> report |
| Duration | 30-60 minutes | 15-30 minutes |

> Complete Arcade Mode reference: See [quick-ref.md](./quick-ref.md)
