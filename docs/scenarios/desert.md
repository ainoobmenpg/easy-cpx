# Desert Scenario

## Overview
Desert warfare scenario - Rapid maneuver battle in open terrain. Player forces must advance and seize key objectives before enemy reinforcements arrive.

## Scenario Details
- **ID**: desert
- **Name**: 砂漠の嵐
- **Difficulty**: easy
- **Duration**: 5-7 turns (decision by turn 6)
- **First Contact**: Turn 2

## Map Configuration
- **Size**: 70x50 grid
- **Terrain**: Open desert, wadi (dry riverbed), small oasis
- **Weather**: Hot, clear

## Force Configuration

### Player Forces (Coalition)
| Type | Count | Starting Position |
|------|-------|-------------------|
| Armor | 4 | x:5-12, y:20-30 |
| Infantry | 2 | x:8-15, y:22-28 |
| Artillery | 2 | x:6-10, y:24-26 |
| Recon | 3 | x:15-22, y:18-32 |
| Air Defense | 1 | x:8, y:25 |

### Enemy Forces (Opposing)
| Type | Count | Starting Position |
|------|-------|-------------------|
| Armor | 3 | x:50-58, y:20-30 |
| Infantry | 3 | x:48-55, y:18-32 |
| Artillery | 2 | x:52-58, y:22-28 |
| Recon | 2 | x:42-50, y:20-30 |

## Initial Setup
- **Turn 1**: Player advances rapidly across open desert
- **Turn 2**: First contact at wadi crossing (x:30)
- **Turns 3-4**: Main engagement at oasis
- **Turns 5-6**: Decision - capture objective or repel counterattack

## Objectives

### Primary Objectives (Must Complete)
- [ ] **obj_desert_main_1**: Capture the oasis (x:40-45, y:22-28) by turn 5
- [ ] **obj_desert_main_2**: Destroy enemy armor reserve (2+ units)

### Secondary Objectives (Bonus)
- [ ] **obj_desert_sub_1**: Secure wadi crossing point
- [ ] **obj_desert_sub_2**: Maintain 70%+ unit strength

## Victory Conditions
- **Major Victory**: Capture oasis + destroy 3+ enemy armor
- **Minor Victory**: Capture oasis + destroy 1+ enemy armor
- **Draw**: Control oasis at turn 6
- **Defeat**: Oasis not captured by turn 6 or 50%+ units lost

## Notes
- Open terrain favors armor mobility
- Wadi at x:25-30 provides temporary cover
- Oasis is key terrain - controls water supply
- Player has air support advantage
- Enemy has higher initial strength but player advances faster

---

## Arcade Configuration

### Map Configuration
- **Size**: 12x8 grid
- **Terrain**: Open desert, wadi (dry riverbed), small oasis
- **Weather**: Hot, clear

### Force Configuration

#### Player Forces (Coalition)
| Type | Count | Starting Position |
|------|-------|-------------------|
| Armor | 2 | x:1-2, y:3-5 |
| Infantry | 1 | x:1-2, y:4-5 |
| Artillery | 1 | x:1, y:4 |
| Recon | 2 | x:2-3, y:3-5 |
| Air Defense | 1 | x:1, y:4 |

#### Enemy Forces (Opposing)
| Type | Count | Starting Position |
|------|-------|-------------------|
| Armor | 2 | x:9-10, y:3-5 |
| Infantry | 2 | x:8-10, y:3-5 |
| Artillery | 1 | x:10, y:4 |
| Recon | 1 | x:8, y:3-5 |

### Initial Setup
- **Turn 1**: Player advances rapidly across open desert
- **Turn 2**: First contact at wadi crossing (x:5)
- **Turns 3-4**: Main engagement at oasis
- **Turns 5-6**: Decision - capture objective or repel counterattack

### Objectives

#### Primary Objectives
- [ ] **obj_desert_arcade_1**: Capture the oasis (x:7-8, y:3-5) by turn 5
- [ ] **obj_desert_arcade_2**: Destroy enemy armor reserve (1+ units)

#### Secondary Objectives (Bonus)
- [ ] **obj_desert_arcade_sub_1**: Secure wadi crossing point
- [ ] **obj_desert_arcade_sub_2**: Maintain 70%+ unit strength

### Victory Conditions (VP)
- **Major Victory (VP 3)**: Capture oasis + destroy 2+ enemy armor
- **Minor Victory (VP 2)**: Capture oasis + destroy 1+ enemy armor
- **Draw (VP 1)**: Control oasis at turn 6
- **Defeat (VP 0)**: Oasis not captured by turn 6 or 50%+ units lost

### STRIKE Resources
- **Initial STRIKE**: 3
- **STRIKE per Kill**: +1 (enemy armor), +0.5 (enemy infantry)

### Notes
- Arcade mode: condensed 12x8 grid
- Open terrain favors armor mobility
- Wadi at x:4-5 provides temporary cover
- Oasis is key terrain - controls water supply
- Faster resolution: 6-8 turns
