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
| `/api/game/{game_id}/state` | GET | Get game state (Fog of War applied) |
| `/api/game/{game_id}/sitrep` | GET | Get SITREP |
| `/api/game/{game_id}/debriefing` | Get game debriefing |
| `/api/game/start` | POST | Start new game with scenario |
| `/api/game/end` | POST | End game |
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
