# Operational CPX

A web-based military command post exercise (CPX) simulation game featuring AI-powered adjudication and turn-based tactical combat.

## Overview

Operational CPX is a strategic-level military simulation where players act as commanders issuing orders to their units. The AI (MiniMax M2.5) interprets player commands and the rule engine adjudicates outcomes based on terrain, weather, supply, and other factors.

## Features

- **Turn-Based Combat**: Strategic command with phase-based turn system
- **AI-Adjudicated Orders**: Natural language order parsing with AI interpretation
- **Fog of War**: Limited information visibility based on reconnaissance
- **Terrain Effects**: Combat modifiers based on terrain (urban, forest, mountain, etc.)
- **Weather System**: Weather affects reconnaissance, movement, and combat
- **Day/Night Cycle**: Time affects visibility and combat effectiveness
- **Resource Management**: Ammo, fuel, and readiness tracking
- **Detailed SITREPs**: AI-generated situation reports with confidence levels

## Tech Stack

- **Frontend**: Next.js 16, React, TypeScript, Tailwind CSS
- **Backend**: Python FastAPI, SQLAlchemy
- **Database**: SQLite (development), PostgreSQL (production)
- **AI**: MiniMax M2.5 for order parsing and SITREP generation

## Project Structure

```
easy-cpx/
├── frontend/                 # Next.js frontend
│   ├── app/
│   │   └── game/           # Game UI components
│   ├── public/
│   └── package.json
├── backend/                  # Python FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── models/         # Database models
│   │   ├── services/       # Business logic
│   │   │   ├── adjudication.py   # Rule engine
│   │   │   ├── ai_client.py      # AI integration
│   │   │   ├── terrain.py        # Terrain effects
│   │   │   ├── weather_effects.py
│   │   │   ├── map_renderer.py
│   │   │   ├── excon_ai.py
│   │   │   └── sitrep_generator.py
│   │   └── data/           # Equipment database
│   ├── tests/              # Test suite
│   └── main.py
├── shared/                   # Shared schemas and types
├── docs/                    # Documentation
└── Plans.md                # Implementation plan
```

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.10+
- pip/venv

### Setup

1. **Clone the repository**

2. **Setup Frontend**
   ```bash
   cd frontend
   npm install
   ```

3. **Setup Backend**
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install fastapi uvicorn sqlalchemy pydantic httpx
   ```
   Note: App uses SQLite by default (set DATABASE_URL for PostgreSQL)

### Running the Application

1. **Start Backend**
   ```bash
   cd backend
   source .venv/bin/activate
   uvicorn main:app --reload
   ```
   Backend runs on http://localhost:8000

2. **Start Frontend**
   ```bash
   cd frontend
   npm run dev
   ```
   Frontend runs on http://localhost:3000

3. **Open Browser**
   Navigate to http://localhost:3000/game

## Game Commands

Players issue orders in natural Japanese:

- `前進せよ` - Move forward
- `敵を攻撃せよ` - Attack enemy
- `防衛せよ` - Defend position
- `撤退せよ` - Retreat
- `偵察せよ` - Reconnaissance
- `補給せよ` - Supply

## Development

### Running Tests

```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend lint
cd frontend
npm run lint
```

### API Endpoints

- `GET /api/games` - List games
- `GET /api/game/{id}/state` - Get game state
- `POST /api/parse-order` - Parse player order
- `POST /api/orders/` - Submit order
- `POST /api/advance-turn` - Advance turn

## License

MIT

## Authors

- Easy-CPX Development Team
