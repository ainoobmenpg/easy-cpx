# Baltic Scenario

## Overview
Baltic Sea coast operations - NATO forces must secure a coastal corridor while enemy forces attempt to cut off the land bridge to Kaliningrad.

## Scenario Details
- **ID**: baltic
- **Name**: バルト海岸
- **Difficulty**: hard
- **Duration**: 5-7 turns (decision by turn 7)
- **First Contact**: Turn 2

## Map Configuration
- **Size**: 60x50 grid
- **Terrain**: Coastal plains, marshland, urban area (coastal town)
- **Weather**: Overcast (spring)
- **Grid Reference**: MGRS 34T (Baltic Coast)

## ORBAT (Order of Battle)

### Player Forces (NATO)
| Type | Count | Starting Position |
|------|-------|-------------------|
| Armor | 2 | x:8-14, y:20-30 |
| Infantry | 5 | x:5-18, y:15-35 |
| Artillery | 2 | x:6-10, y:22-28 |
| Recon | 3 | x:12-20, y:18-32 |
| Air Defense | 2 | x:8, y:25 |

### Enemy Forces (Opposing)
| Type | Count | Starting Position |
|------|-------|-------------------|
| Armor | 3 | x:42-50, y:20-30 |
| Infantry | 4 | x:38-48, y:15-35 |
| Artillery | 3 | x:45-52, y:22-28 |
| Recon | 2 | x:35-42, y:18-32 |

## Initial Setup
- **Turn 1**: Player forces consolidate in coastal town
- **Turn 2**: First contact - recon patrols engage
- **Turns 3-5**: Heavy fighting for town control
- **Turns 6-7**: Encirclement attempt or breakout

## Objectives

### Primary Objectives (Must Complete)
- [ ] **obj_baltic_main_1**: Secure the coastal town (x:15-25, y:20-30) for 4 turns
- [ ] **obj_baltic_main_2**: Prevent enemy encirclement - keep supply route open

### Secondary Objectives (Bonus)
- [ ] **obj_baltic_sub_1**: Destroy enemy artillery positions
- [ ] **obj_baltic_sub_2**: Capture enemy recon unit

## Victory Conditions
- **Major Victory**: Hold town + keep supply route + destroy 3+ enemy units
- **Minor Victory**: Hold town + keep supply route
- **Draw**: Hold town until turn 7
- **Defeat**: Town lost before turn 5 or supply route cut

## Notes
- Marshland at y:35-40 limits maneuverability
- Urban terrain provides defense bonus (+1 to defense)
- Coastal road (y:25) is key supply route
- Enemy has numerical advantage but player has better defensive positions

---

## Arcade Configuration (12x8)

### Map Configuration
- **Size**: 12x8 grid (condensed from 60x50)
- **Arcade Grid Reference**: Simplified MGRS (local grid)
- **Terrain**: Coastal plains, marshland, urban area (coastal town)
- **Weather**: Overcast (spring)

### Force Configuration

#### Player Forces (NATO)
| Type | Count | Starting Position |
|------|-------|-------------------|
| Armor | 1 | x:2-3, y:4-5 |
| Infantry | 2 | x:1-3, y:3-6 |
| Artillery | 1 | x:1, y:4-5 |
| Recon | 1 | x:3, y:3-5 |
| Air Defense | 1 | x:2, y:5 |

#### Enemy Forces (Opposing)
| Type | Count | Starting Position |
|------|-------|-------------------|
| Armor | 2 | x:9-10, y:4-5 |
| Infantry | 2 | x:8-10, y:3-6 |
| Artillery | 1 | x:10, y:4-5 |
| Recon | 1 | x:8, y:3-5 |

### Initial Setup
- **Turn 1**: Player forces consolidate in coastal town
- **Turn 2**: First contact - recon patrols engage
- **Turns 3-5**: Heavy fighting for town control
- **Turns 6-7**: Encirclement attempt or breakout

### Objectives

#### Primary Objectives
- [ ] **obj_baltic_arcade_1**: Secure the coastal town (x:3-5, y:3-5) for 3 turns
- [ ] **obj_baltic_arcade_2**: Prevent enemy encirclement - keep supply route open

#### Secondary Objectives (Bonus)
- [ ] **obj_baltic_arcade_sub_1**: Destroy enemy artillery positions
- [ ] **obj_baltic_arcade_sub_2**: Capture enemy recon unit

### Victory Conditions (VP)
- **Major Victory (VP 3)**: Hold town + keep supply route + destroy 2+ enemy units
- **Minor Victory (VP 2)**: Hold town + keep supply route
- **Draw (VP 1)**: Hold town until turn 7
- **Defeat (VP 0)**: Town lost before turn 5 or supply route cut

### STRIKE Resources
- **Initial STRIKE**: 3
- **STRIKE per Kill**: +1 (enemy armor), +0.5 (enemy infantry/artillery)

### Notes
- Arcade mode: condensed 12x8 grid
- Urban terrain at center provides defense bonus
- Coastal road is key supply route
- Faster resolution: 6-8 turns
