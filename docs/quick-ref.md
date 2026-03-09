# Arcade CPX Quick Reference

## 2D6 Judgment Table

| Roll+Mod | Result | Effect |
|----------|--------|--------|
| 2-3 | CRITICAL FAIL | Attacker takes 1 damage |
| 4-5 | FAIL | No damage |
| 6-7 | PARTIAL | Defender: 1 damage |
| 8-9 | SUCCESS | Defender: 2 damage |
| 10-11 | GREAT | Defender: 3 damage |
| 12+ | CRITICAL | Defender: 4 damage |

## 6 Commands

| Command | Icon | Description |
|---------|------|-------------|
| MOVE | > | Relocate unit |
| ATTACK | X | Offensive action |
| DEFEND | O | Hold position (+2 DEF) |
| RECON | ? | Gather intel |
| SUPPLY | + | Request logistics |
| STRIKE | * | Heavy attack |

## Unit Stats

| Type | ATK | DEF | MOVE | HP |
|------|-----|-----|------|-----|
| INFANTRY | 3 | 3 | 2 | 3 |
| ARMOR | 4 | 4 | 3 | 4 |
| ARTILLERY | 5 | 2 | 2 | 2 |
| AIR_DEFENSE | 2 | 4 | 2 | 3 |
| RECON | 2 | 2 | 4 | 2 |

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
