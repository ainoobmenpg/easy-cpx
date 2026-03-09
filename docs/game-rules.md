# Game Rules

> Quick Reference: See [quick-ref.md](./quick-ref.md) for arcade mode summary

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

---

## Arcade Mode

Arcade mode provides a simplified, faster-paced experience using 2D6 dice rolls and a streamlined command set.

### Game Mode Selection

| Mode | Description |
|------|-------------|
| SIMULATION | Full rule engine with complex factors |
| ARCADE | Simplified 2D6 system for quick battles |

### 2D6 Judgment System

Combat and actions are resolved using 2 six-sided dice (2D6).

#### Base Roll Table

| Roll | Result | Description |
|------|--------|-------------|
| 2 | CRITICAL_FAIL | Complete failure, potential unit damage |
| 3-4 | FAIL | Action failed |
| 5-6 | PARTIAL | Mixed results |
| 7-8 | SUCCESS | Action succeeded |
| 9-10 | GREAT | Strong success |
| 11-12 | CRITICAL | Exceptional result |

#### Modifiers

| Factor | Modifier |
|--------|----------|
| Terrain Advantage (Defense) | +1 |
| Strength 80+ | +1 |
| Strength 50-79 | 0 |
| Strength below 50 | -1 |
| Weather: Rain/Storm | -1 |
| Night Combat | -1 |
| Initiative (Attack First) | +1 |
| Superior Numbers (2:1) | +1 |
| Supply Depleted | -1 |
| Supply Exhausted | -2 |

#### Modified Roll Table

| Modified Roll | Result |
|---------------|--------|
| 2-3 | CRITICAL_FAIL |
| 4-5 | FAIL |
| 6-7 | PARTIAL |
| 8-9 | SUCCESS |
| 10-11 | GREAT |
| 12+ | CRITICAL |

### Arcade Commands (6 Commands)

| Command | Description | Dice Roll |
|---------|-------------|-----------|
| ATTACK | Offensive action | Attack vs Defense |
| MOVE | Relocate unit | Movement check |
| DEFEND | Hold position | Defense bonus |
| RECON | Gather intelligence | Recon roll |
| SUPPLY | Request logistics | Supply check |
| WAIT | Hold action | No roll |

### Combat Resolution

1. Attacker declares target
2. Calculate attacker's attack rating (base + modifiers)
3. Calculate defender's defense rating (base + modifiers)
4. Roll 2D6 + attacker's attack rating
5. Compare to 2D6 + defender's defense rating
6. Higher total wins

#### Damage Table

| Result | Damage to Defender |
|--------|-------------------|
| CRITICAL_FAIL | Attacker takes 1 damage |
| FAIL | No damage |
| PARTIAL | Defender: 1 damage |
| SUCCESS | Defender: 2 damage |
| GREAT | Defender: 3 damage |
| CRITICAL | Defender: 4 damage |

### Movement

| Terrain | Cells per Turn |
|---------|----------------|
| Plain | 4 |
| Forest | 2 |
| Urban | 2 |
| Mountain | 1 |
| Water | 0 (impassable) |

### Unit Stats (Arcade)

| Type | Attack | Defense | Move | HP |
|------|--------|---------|------|-----|
| INFANTRY | 3 | 3 | 2 | 3 |
| ARMOR | 4 | 4 | 3 | 4 |
| ARTILLERY | 5 | 2 | 2 | 2 |
| AIR_DEFENSE | 2 | 4 | 2 | 3 |
| RECON | 2 | 2 | 4 | 2 |
| SUPPORT | 1 | 3 | 3 | 4 |

### Quick Turn Flow

1. Issue commands to units (6 commands)
2. Resolve all MOVE orders
3. Resolve all ATTACK orders
4. Apply damage and remove destroyed units
5. Generate brief SITREP
6. Advance to next turn

### Fog of War (Arcade)

Arcade mode uses simplified fog of war:

- **Visible**: Adjacent cells (1 cell radius)
- **Known**: Previously observed locations
- **Unknown**: All other areas

### Victory Conditions (Arcade)

| Condition | Description |
|-----------|-------------|
| Elimination | Destroy all enemy units |
| Breakthrough | Reach opposite edge of map |
| Points | 10 points per unit destroyed |

---

## Command Reference

### Simulation Mode Commands

- MOVE, ATTACK, DEFEND, SUPPORT, RETREAT, RECON, SUPPLY, SPECIAL
- Three levels: TACTICAL, OPERATIONAL, STRATEGIC

### Arcade Mode Commands

- ATTACK, MOVE, DEFEND, RECON, SUPPLY, WAIT
- No levels, simple execution
