# Game Rules

## Turn System

The game operates on a turn-based system where each turn represents approximately 15 minutes of game time.

### Turn Phases

1. **Orders Phase**: Player issues commands to units
2. **Adjudication Phase**: AI interprets orders and rule engine resolves actions
3. **SITREP Phase**: AI generates situation report

## Order Types

| Order | Description |
|-------|-------------|
| MOVE | Move unit to specified location |
| ATTACK | Attack enemy unit |
| DEFEND | Hold defensive position |
| SUPPORT | Provide support to nearby units |
| RETREAT | Withdraw from current position |
| RECON | Conduct reconnaissance |
| SUPPLY | Request supply convoy |
| SPECIAL | Special operation |

## Order Levels

| Level | Description |
|-------|-------------|
| TACTICAL | Individual unit actions (recon, defensive positions) |
| OPERATIONAL | Formation-level actions (division movement, air ops) |
| STRATEGIC | Strategic decisions (mobilization, war initiation) |

## Judgment Criteria

Combat outcomes are determined by multiple factors:

### Primary Factors

1. **Terrain Advantage**: Defenders in urban/mountain/forest get bonus
2. **Unit Strength**: Higher strength = better combat performance
3. **Supply Status**: Full supply = normal, depleted = penalty, exhausted = failed
4. **Weather Effects**: Bad weather reduces effectiveness
5. **Night Penalties**: Night combat without NOD devices is penalized
6. **Firepower Ratio**: Numerical superiority matters
7. **Initiative**: Who attacks first

### Success Levels

- **SUCCESS**: All major factors favor attacker
- **PARTIAL**: Some factors mixed
- **FAILED**: Defender has advantage or attacker exhausted

## Resource Management

### Supply Levels

| Level | Status | Combat Effect |
|-------|--------|---------------|
| FULL | 充足 | Normal effectiveness |
| DEPLETED | 低下 | -30% combat effectiveness |
| EXHAUSTED | 枯渇 | Cannot attack, limited movement |

### Extended Resources

- **Interceptors**: Air defense missiles
- **Precision Munitions**: Guided weapons

## Terrain Effects

| Terrain | Defense Bonus | Movement Cost | Concealment |
|---------|---------------|---------------|--------------|
| Plain | 1.0x | 1.0x | 10% |
| Urban | 1.5x | 1.5x | 40% |
| Forest | 1.2x | 1.3x | 50% |
| Mountain | 1.8x | 2.0x | 30% |
| High Ground | 1.3x | 1.2x | 20% |
| Water | - | Impassable | 0% |
| Swamp | 1.1x | 2.0x | 40% |

## Weather Effects

| Weather | Recon | Air Ops | Artillery | Movement |
|---------|-------|---------|-----------|----------|
| Clear | 100% | 100% | 100% | 100% |
| Cloudy | 90% | 95% | 90% | 100% |
| Rain | 60% | 70% | 50% | 80% |
| Storm | 30% | 40% | 30% | 50% |
| Fog | 40% | 50% | 40% | 90% |
| Snow | 50% | 60% | 50% | 70% |

## Time of Day

| Period | Hours | Visibility | Combat | Notes |
|--------|-------|------------|--------|-------|
| DAY | 07:00-17:00 | 100% | 100% | Normal operations |
| DAWN | 05:00-07:00 | 80% | 90% | Slightly reduced |
| DUSK | 17:00-19:00 | 70% | 85% | Caution advised |
| NIGHT | 19:00-05:00 | 30% | 60% | NOD required |

## Intelligence System

### Confidence Levels

- **CONFIRMED**: Direct contact, high certainty
- **ESTIMATED**: Indirect information, moderate certainty
- **UNKNOWN**: No information available

### Intelligence Sources

1. **Direct Contact**: 85% accuracy, immediate
2. **Recon Report**: 60% accuracy, 1 turn delay
3. **Aerial Recon**: 70% accuracy, freshness varies
4. **Signals Intel**: 40% accuracy, 2 turn delay
5. **Command Intel**: 30% accuracy, 3 turn delay

## Friction Events

Random events that affect operations:

- **Misfire**: Friendly fire incident
- **Communication Failure**: Command disruption
- **Maintenance Issue**: Equipment problems
- **Weather Deterioration**: Sudden weather change
- **Unit Error**: Positioning mistake
- **Supply Delay**: Logistics problems
- **Unexpected Contact**: Unplanned enemy engagement

## Escalation Levels

| Level | Points | Description |
|-------|--------|-------------|
| PEACETIME | 0-19 | Normal state |
| CRISIS | 20-39 | Increased tension |
| CONFLICT | 40-59 | Active fighting |
| WAR | 60-79 | Full-scale war |
| HOT_WAR | 80-94 | Intense combat |
| MAXIMUM | 95-100 | Maximum escalation |

## Victory Conditions

The game continues until one side achieves:
- Elimination of all enemy units
- Occupation of key objectives
- Mutual exhaustion (stalemate)
