# Arcade CPX Quick Reference

## 2D6 Judgment Table (Diff System)

Roll 2D6 for attacker and defender, then calculate the difference.

**Diff = (Attacker 2D6) - (Defender 2D6)**

| Diff | Result | Abbr | Description |
|------|--------|------|-------------|
| 0-1 | DRAW | D | No decisive outcome |
| 2-3 | ADVANTAGE | A | Minor advantage |
| 4-5 | VICTORY | V | Decisive win |
| 6+ | COMPLETE_VICTORY | CV | Full effect |
| -1 to -3 | DEFENDER_ADV | DA | Defender advantage |
| -6 or less | DEFENDER_VICTORY | DV | Defender repels |

Same table applies to both sides (whoever has positive diff uses it).

## 6 Commands

| Command | Icon | Description |
|---------|------|-------------|
| MOVE | > | Relocate unit |
| ATTACK | X | Offensive action |
| DEFEND | O | Hold position (+2 DEF) |
| RECON | ? | Gather intel |
| SUPPLY | + | Request logistics |
| STRIKE | * | Heavy attack |

## Unit Stats (6 Types)

| Type | ATK | DEF | MOVE | HP |
|------|-----|-----|------|-----|
| INFANTRY | 3 | 3 | 2 | 3 |
| ARMOR | 4 | 4 | 3 | 4 |
| ARTILLERY | 5 | 2 | 2 | 2 |
| AIR_DEFENSE | 2 | 4 | 2 | 3 |
| RECON | 2 | 2 | 4 | 2 |
| SUPPORT | 1 | 3 | 3 | 4 |

## Terrain Movement

| Terrain | Cells/Turn |
|---------|------------|
| Plain | 4 |
| Forest | 2 |
| Urban | 2 |
| Mountain | 1 |
| Water | 0 (impassable) |

## Turn Flow

1. Issue commands to units
2. Resolve MOVE orders
3. Resolve ATTACK orders
4. Apply damage
5. Generate SITREP
6. Next turn

## Victory Conditions

- **Elimination**: Destroy all enemy units
- **Breakthrough**: Reach opposite edge
- **Points**: 10 pts/unit destroyed
