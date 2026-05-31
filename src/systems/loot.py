import random
from typing import List, Tuple

from systems.gear import FLOOR_GEAR_POOL, make_gear, roll_rarity

LOOT_TABLES = {
    'slime': [
        ('coin',      1.00, (1, 3)),
        ('slime_gel', 0.75, (1, 2)),
    ],
    'goblin': [
        ('coin',      1.00, (2, 4)),
        ('slime_gel', 0.25, (1, 1)),
    ],
    'troll': [
        ('coin',      1.00, (3, 6)),
        ('slime_gel', 0.50, (1, 2)),
    ],
    'skeleton': [
        ('coin',      1.00, (4, 8)),
        ('slime_gel', 0.30, (1, 2)),
    ],
}

# Surface/overworld enemies drop floor-0 gear; underground floor-1/2
_ENEMY_FLOOR = {'slime': 0, 'goblin': 0, 'troll': 1, 'skeleton': 2}


def roll_loot(enemy_type: str) -> List[Tuple[str, int]]:
    results = []
    for item_id, chance, (lo, hi) in LOOT_TABLES.get(enemy_type, []):
        if random.random() <= chance:
            results.append((item_id, random.randint(lo, hi)))
    return results


def roll_gear_drop(enemy_type: str):
    """Return a gear dict or None. 15% chance for slime, 25% goblin, 35% troll."""
    GEAR_CHANCE = {'slime': 0.15, 'goblin': 0.25, 'troll': 0.35, 'skeleton': 0.40}
    if random.random() > GEAR_CHANCE.get(enemy_type, 0.10):
        return None
    floor = _ENEMY_FLOOR.get(enemy_type, 0)
    pool  = FLOOR_GEAR_POOL.get(floor, [])
    if not pool:
        return None
    # Weighted sample: sum all chances then pick
    total  = sum(c for _, c in pool)
    r      = random.uniform(0, total)
    acc    = 0.0
    chosen = pool[0][0]
    for base_id, chance in pool:
        acc += chance
        if r <= acc:
            chosen = base_id
            break
    return make_gear(chosen, roll_rarity(floor))
