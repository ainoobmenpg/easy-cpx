# Arcade CPX Quick Reference

> Complete reference for Arcade Mode gameplay. For detailed rules, see [game-rules.md](./game-rules.md).

## Map

- **Size**: 12 x 8 grid (96 cells total)
- **Origin**: Player starts at left side (x: 0-2), Enemy at right side (x: 9-11)

## Unit Types and Stats

| Type | ATK | DEF | MOVE | HP | Special |
|------|-----|-----|------|-----|---------|
| INFANTRY | 3 | 3 | 2 | 3 | Balanced |
| ARMOR | 4 | 4 | 3 | 4 | High mobility |
| ARTILLERY | 5 | 2 | 2 | 2 | High attack, fragile |
| AIR_DEFENSE | 2 | 4 | 2 | 3 | Anti-air |
| RECON | 2 | 2 | 4 | 2 | Fast movement |
| SUPPORT | 1 | 3 | 3 | 4 | Durable |

## 2D6 Judgment Table (Diff System)

Roll 2D6 for both sides, then calculate the difference.

**Diff = (Attacker Roll) - (Defender Roll)**

| Diff | Result | Abbr | Damage |
|------|--------|------|--------|
| ≤-3 | CRITICAL_FAIL | CF | Attacker takes 1 damage |
| -2 | FAIL | F | No damage |
| -1, 0 | PARTIAL | P | Defender: 1 damage |
| +1 | SUCCESS | S | Defender: 2 damage |
| +2 | GREAT | G | Defender: 3 damage |
| ≥+3 | CRITICAL | C | Defender: 4 damage |

### Modifiers

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

## 6 Commands

| Command | Icon | Description | Effect |
|---------|------|-------------|--------|
| MOVE | `>` | Relocate unit | Move to adjacent cell |
| ATTACK | `X` | Offensive action | Combat vs enemy in range |
| DEFEND | `O` | Hold position | +2 DEF until next turn |
| RECON | `?` | Gather intel | Reveal adjacent cells |
| SUPPLY | `+` | Request logistics | Restore supply status |
| STRIKE | `*` | Heavy attack | +2 ATK, -1 DEF (this turn), requires adjacent enemy, 3 uses per game, cannot attack next turn |

## Terrain Movement

Movement is calculated as: `Unit MOVE stat / Terrain Cost (Manhattan distance)`

| Terrain | Cost | INF (MOVE=2) | ARM (MOVE=3) | ART (MOVE=2) |
|---------|------|--------------|--------------|--------------|
| Plain | 1 | 2 cells | 3 cells | 2 cells |
| Forest | 2 | 1 cell | 1 cell | 1 cell |
| Urban | 2 | 1 cell | 1 cell | 1 cell |
| Mountain | 4 | 0 cells | 0 cells | 0 cells |
| Water | 999 | impassable | impassable | impassable |

## Turn Flow

1. Issue commands to units
2. Resolve MOVE orders
3. Resolve ATTACK/STRIKE orders
4. Apply damage (remove destroyed units)
5. Event deck draw (20% chance)
6. Generate SITREP
7. Next turn

## Victory Conditions

| Condition | Description |
|-----------|-------------|
| Elimination | Destroy all enemy units |
| Breakthrough | Reach opposite edge of map |
| Points | 10 points per enemy unit destroyed |

## Event Deck (10 Cards)

Drawn with 20% chance per turn (after turn 2).

| Event | Effect | Rarity |
|-------|--------|--------|
| 増援部隊到着 | +2 combat, 1 turn | Common |
| 敵増援確認 | -1 defense, 1 turn | Common |
| 弾薬消費率高騰 | Artillery limited | Uncommon |
| 天候急変 | -1 movement, 1 turn | Common |
| 情報漏洩の可能性 | Defensive posture | Rare |
| 補給線途絶 | Supply priority, 2 turns | Uncommon |
| 士気高揚 | +1 combat, 1 turn | Uncommon |
| 敵部隊動揺 | +2 attack, 1 turn | Rare |
| 砲兵火力遮断解除 | +1 artillery, 1 turn | Common |
| 航空火力使用可能 | +2 air strike, 1 turn | Rare |

## Fog of War

- **Visible**: Adjacent cells (1 cell radius)
- **Known**: Previously observed locations
- **Unknown**: All other areas
