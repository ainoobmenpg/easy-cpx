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

## Force Configuration

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
