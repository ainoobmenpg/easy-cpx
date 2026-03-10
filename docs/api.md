# API Reference

> This document covers the Operational CPX API endpoints. For authentication and RBAC details, see [architecture.md](./architecture.md).

## Base URL

```
Production: https://your-domain.com/api
Development: http://localhost:8000/api
```

## Authentication

Currently, the API does not require authentication. For future implementation, see [CPX-AUTH](./issues/cpx-auth-jwt.md).

## Common Headers

| Header | Value | Required |
|--------|-------|----------|
| Content-Type | application/json | Yes |
| Authorization | Bearer {token} | Future |

## Response Format

All responses follow this structure:

```json
{
  "data": { ... },
  "error": null
}
```

Error responses:

```json
{
  "data": null,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message"
  }
}
```

## HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 422 | Validation Error |
| 500 | Internal Server Error |

---

## Games

### Create Game

**POST** `/games/`

```json
{
  "name": "Operation Desert Storm"
}
```

Response (200):
```json
{
  "id": 1,
  "name": "Operation Desert Storm",
  "current_turn": 0,
  "status": "pending",
  "game_mode": "simulation"
}
```

### List Games

**GET** `/games/`

Response (200):
```json
[
  {
    "id": 1,
    "name": "Operation Desert Storm",
    "current_turn": 5,
    "status": "active"
  }
]
```

### Get Game

**GET** `/games/{game_id}`

Response (200):
```json
{
  "id": 1,
  "name": "Operation Desert Storm",
  "current_turn": 5,
  "current_date": "2026-03-10",
  "current_time": "12:00",
  "weather": "clear",
  "phase": "execution",
  "status": "active",
  "game_mode": "simulation"
}
```

### Start Game

**POST** `/games/start`

```json
{
  "scenario_id": "fulda-lite",
  "name": "My Game"
}
```

Response (200):
```json
{
  "game_id": 1,
  "status": "started"
}
```

### End Game

**POST** `/games/{game_id}/end`

Response (200):
```json
{
  "game_id": 1,
  "status": "ended"
}
```

---

## Units

### Get Units

**GET** `/games/{game_id}/units`

Response (200):
```json
[
  {
    "id": 1,
    "name": "Alpha Company",
    "unit_type": "infantry",
    "side": "player",
    "x": 10.5,
    "y": 20.3,
    "status": "intact",
    "strength": 80
  }
]
```

### Create Unit

**POST** `/games/{game_id}/units/`

```json
{
  "name": "Bravo Company",
  "unit_type": "armor",
  "side": "player",
  "x": 15.0,
  "y": 25.0
}
```

### Move Unit

**POST** `/units/{unit_id}/move`

```json
{
  "target_x": 20,
  "target_y": 25
}
```

Response (200):
```json
{
  "unit_id": 1,
  "from_x": 15,
  "from_y": 25,
  "to_x": 20,
  "to_y": 25,
  "distance": 5,
  "cost": 5,
  "result": "success"
}
```

### Get Reachable Cells

**GET** `/units/{unit_id}/reachable?game_id={game_id}`

Response (200):
```json
{
  "unit_id": 1,
  "reachable": [
    {"x": 16, "y": 25},
    {"x": 17, "y": 25},
    {"x": 15, "y": 26}
  ]
}
```

---

## Orders

### Parse Order (AI)

**POST** `/parse-order`

```json
{
  "order_text": "前線に進出せよ",
  "game_id": 1,
  "unit_id": 1
}
```

Response (200):
```json
{
  "order_type": "MOVE",
  "intent": "前線に進出",
  "target_location": {"x": 30, "y": 15},
  "confidence": 0.85
}
```

### Submit Order

**POST** `/orders/`

```json
{
  "game_id": 1,
  "unit_id": 1,
  "order_type": "MOVE",
  "order_level": "TACTICAL",
  "intent": "前線に進出",
  "location_x": 30,
  "location_y": 15
}
```

Response (200):
```json
{
  "id": 1,
  "game_id": 1,
  "unit_id": 1,
  "order_type": "MOVE",
  "status": "pending"
}
```

### Commit Turn

**POST** `/turn/commit`

```json
{
  "game_id": 1
}
```

Response (200):
```json
{
  "game_id": 1,
  "turn": 6,
  "orders_resolved": 5,
  "events_drawn": 1
}
```

### Advance Turn

**POST** `/advance-turn`

```json
{
  "game_id": 1
}
```

Response (200):
```json
{
  "game_id": 1,
  "turn": 6,
  "date": "2026-03-10",
  "time": "12:00"
}
```

---

## Game State

### Get Game State (Fog of War)

**GET** `/games/{game_id}/state`

Response (200):
```json
{
  "game_id": 1,
  "turn": 5,
  "units": [...],
  "visible_cells": [...],
  "known_cells": [...]
}
```

### Get SITREP

**GET** `/games/{game_id}/sitrep`

Response (200):
```json
{
  "game_id": 1,
  "turn": 5,
  "sitrep": "敵主力部隊が北方国境沿いに集結中...",
  "timestamp": "2026-03-10T12:00:00Z"
}
```

### Get Debriefing

**GET** `/games/{game_id}/debriefing`

Response (200):
```json
{
  "game_id": 1,
  "turn": 10,
  "summary": "作戦は概ね成功...",
  "losses": {"player": 15, "enemy": 45},
  "victory_points": 120
}
```

---

## OPORD

### Get OPORD

**GET** `/games/{game_id}/opord`

Response (200):
```json
{
  "opord_id": "uuid",
  "game_id": 1,
  "title": "作戦計画",
  "situation": {
    "enemy_situation": "敵主力部隊が...",
    "friendly_situation": "自軍主力は...",
    ...
  },
  "mission": {...},
  "execution": {...},
  "service_support": {...}
}
```

### Create OPORD

**POST** `/games/{game_id}/opord`

```json
{
  "title": "新作戦計画",
  "situation": {...},
  "mission": {...}
}
```

### Update OPORD

**PUT** `/games/{game_id}/opord`

```json
{
  "mission": {
    "task": "敵を撃破",
    "purpose": "安全を確保"
  }
}
```

### Get OPORD Display

**GET** `/games/{game_id}/opord/display`

Response (200): Formatted OPORD text for UI display

---

## Injects (MEL/MIL)

### Get Active Injects

**GET** `/injects/{game_id}`

Response (200):
```json
{
  "game_id": 1,
  "injects": [
    {
      "id": "inject-1",
      "type": "MIL",
      "title": "敵増援出現",
      "description": "敵増援部隊が北方から接近中",
      "trigger_turn": 3,
      "effects": {...}
    }
  ]
}
```

### Trigger Inject

**POST** `/injects/{game_id}/trigger`

```json
{
  "inject_id": "inject-1"
}
```

Response (200):
```json
{
  "inject_id": "inject-1",
  "status": "triggered",
  "effects": {...}
}
```

### Cancel Inject

**POST** `/injects/{game_id}/cancel`

```json
{
  "inject_id": "inject-1"
}
```

### Reset Injects

**POST** `/injects/{game_id}/reset`

Response (200):
```json
{
  "game_id": 1,
  "status": "reset"
}
```

### Get Inject Effects

**GET** `/injects/{game_id}/effects`

Response (200):
```json
{
  "game_id": 1,
  "effects": [
    {"type": "unit_add", "side": "enemy", "count": 3}
  ]
}
```

### Decrement Inject Turn

**POST** `/injects/{game_id}/decrement-turn`

```json
{
  "inject_id": "inject-1"
}
```

---

## Events

### Draw Random Event

**POST** `/event/draw`

```json
{
  "game_id": 1
}
```

Response (200):
```json
{
  "event": "天候急変",
  "effect": "-1 movement, 1 turn",
  "severity": "common"
}
```

---

## Scenarios

### List Scenarios

**GET** `/scenarios`

Response (200):
```json
[
  {
    "id": "fulda-lite",
    "name": "Fulda Lite",
    "description": "Cold War scenario",
    "duration": "30-60 min"
  }
]
```

### Get Scenario

**GET** `/scenarios/{scenario_id}`

Response (200):
```json
{
  "id": "fulda-lite",
  "name": "Fulda Lite",
  "description": "Cold War scenario",
  "initial_state": {...},
  "objectives": [...]
}
```

---

## Reports

### Generate Report

**POST** `/reports/generate`

```json
{
  "game_id": 1,
  "report_type": "SITREP"
}
```

### Get Report

**GET** `/reports/{game_id}`

Response (200):
```json
{
  "game_id": 1,
  "reports": [...]
}
```

---

## Internal Endpoints

> **Warning**: These endpoints expose sensitive data without Fog of War. They require `ENABLE_INTERNAL_ENDPOINTS=true` and should never be exposed to public clients.

### Get True State

**GET** `/internal/games/{game_id}/true-state`

Response (200): Complete game state without Fog of War

### Get All Units

**GET** `/internal/games/{game_id}/units`

Response (200): All units including hidden enemy positions

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:3000` |
| `DATABASE_URL` | PostgreSQL connection | `sqlite:///./cpx.db` |
| `MINIMAX_API_KEY` | AI API key | - |
| `MINIMAX_BASE_URL` | AI API endpoint | `https://api.minimax.chat/v1` |
| `ENABLE_INTERNAL_ENDPOINTS` | Enable internal APIs | `false` |
| `CPX_RNG_SEED` | Fixed RNG seed | - |
| `CPX_SEED_SALT` | RNG salt | `default` |
