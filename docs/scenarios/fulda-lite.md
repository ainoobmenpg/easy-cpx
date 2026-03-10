# Fulda-lite Scenario

## Overview
Cold War scenario based on the Fulda Gap - a potential Soviet invasion route through Germany. Players defend the gap against Warsaw Pact forces.

## Scenario Details
- **ID**: fulda-lite
- **Name**: フルダ・ギャップ
- **Difficulty**: normal
- **Duration**: 5-7 turns (decision by turn 7)
- **First Contact**: Turn 2

## Map Configuration
- **Size**: 50x40 grid
- **Terrain**: Central European highlands, forest, river crossing
- **Weather**: Clear (spring)
- **Grid Reference**: MGRS 34T (Central Europe)

## ORBAT (Order of Battle)

### Player Forces (NATO)
| Type | Count | Starting Position |
|------|-------|-------------------|
| Armor | 3 | x:10-15, y:15-25 |
| Infantry | 4 | x:8-20, y:10-30 |
| Artillery | 2 | x:5-12, y:20-25 |
| Recon | 2 | x:12-18, y:12-18 |
| Air Defense | 1 | x:8, y:22 |

### Enemy Forces (Warsaw Pact)
| Type | Count | Starting Position |
|------|-------|-------------------|
| Armor | 4 | x:35-42, y:15-25 |
| Infantry | 3 | x:32-40, y:12-28 |
| Artillery | 2 | x:38-45, y:18-22 |
| Recon | 2 | x:28-35, y:15-25 |

## Initial Setup
- **Turn 1**: Deployment phase, forces move to forward positions
- **Turn 2**: First contact expected - recon units engage
- **Turns 3-5**: Main battle phase
- **Turns 6-7**: Decision phase - breakthrough or stalemate

## Objectives

### Primary Objectives (Must Complete)
- [ ] **obj_fulda_main_1**: Hold the river crossing at x:20-25 for 4 turns
- [ ] **obj_fulda_main_2**: Destroy enemy armor force (3+ units)

### Secondary Objectives (Bonus)
- [ ] **obj_fulda_sub_1**: Capture enemy artillery battery
- [ ] **obj_fulda_sub_2**: Maintain supply line to forward position

## Victory Conditions
- **Major Victory**: Hold crossing + destroy 4+ enemy armor
- **Minor Victory**: Hold crossing + destroy 2+ enemy armor
- **Draw**: Hold crossing until turn 7
- **Defeat**: Crossing lost before turn 5

## Notes
- River at x:20 provides natural defense
- Forest zones at y:10-15 and y:28-32 provide concealment
- Player has air superiority advantage until turn 5

---

## Arcade Configuration (12x8)

### Map Configuration
- **Size**: 12x8 grid (condensed from 50x40)
- **Arcade Grid Reference**: Simplified MGRS (local grid)
- **Terrain**: Central European highlands, forest, river crossing
- **Weather**: Clear (spring)

### Force Configuration

#### Player Forces (NATO)
| Type | Count | Starting Position |
|------|-------|-------------------|
| Armor | 2 | x:2-3, y:3-5 |
| Infantry | 2 | x:1-3, y:2-6 |
| Artillery | 1 | x:1, y:4 |
| Recon | 1 | x:3, y:3-4 |

#### Enemy Forces (Warsaw Pact)
| Type | Count | Starting Position |
|------|-------|-------------------|
| Armor | 2 | x:9-10, y:3-5 |
| Infantry | 2 | x:8-10, y:2-6 |
| Artillery | 1 | x:10, y:4 |
| Recon | 1 | x:7-8, y:3-4 |

### Initial Setup
- **Turn 1**: Deployment phase, forces move to forward positions
- **Turn 2**: First contact - recon units engage
- **Turns 3-5**: Main battle phase
- **Turns 6-7**: Decision phase - breakthrough or stalemate

### Objectives

#### Primary Objectives
- [ ] **obj_fulda_arcade_1**: Hold the river crossing at x:5-6 for 3 turns
- [ ] **obj_fulda_arcade_2**: Destroy enemy armor force (2+ units)

#### Secondary Objectives (Bonus)
- [ ] **obj_fulda_arcade_sub_1**: Capture enemy artillery battery

### Victory Conditions (VP)
- **Major Victory (VP 3)**: Hold crossing + destroy 2+ enemy armor
- **Minor Victory (VP 2)**: Hold crossing + destroy 1+ enemy armor
- **Draw (VP 1)**: Hold crossing until turn 7
- **Defeat (VP 0)**: Crossing lost before turn 5

### STRIKE Resources
- **Initial STRIKE**: 3
- **STRIKE per Kill**: +1 (enemy armor), +0.5 (enemy infantry)

### Notes
- Arcade mode: condensed 12x8 grid
- River at x:5 provides natural defense
- Forest zones at y:1-2 and y:6-7 provide concealment
- Faster resolution: 6-8 turns
