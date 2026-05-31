"""
Rarity system and gear item creation.
All equipment is represented as a full dict with baked-in stats.
"""
import random
from typing import Dict, Optional

RARITIES: Dict[str, dict] = {
    'common':    {'label': 'Siradan',   'color': (180, 180, 180), 'mult': 1.0},
    'uncommon':  {'label': 'Nadir Disi','color': (80,  220, 80),  'mult': 1.6},
    'rare':      {'label': 'Nadir',     'color': (80,  140, 255), 'mult': 2.4},
    'epic':      {'label': 'Destansi',  'color': (200, 60,  255), 'mult': 3.6},
}
RARITY_ORDER = ['common', 'uncommon', 'rare', 'epic']

ITEM_BASES: Dict[str, dict] = {
    # ── Silahlar ─────────────────────────────────────────────────────
    'wooden_sword':  {'name': 'Ahsap Kilic',  'slot': 'weapon', 'dmg': 8,  'def': 0, 'spd': 0,
                      'blade': (139, 90,  43)},
    'stone_sword':   {'name': 'Tas Kilic',    'slot': 'weapon', 'dmg': 20, 'def': 0, 'spd': 0,
                      'blade': (160, 160, 160)},
    'iron_sword':    {'name': 'Demir Kilic',  'slot': 'weapon', 'dmg': 32, 'def': 0, 'spd': 1,
                      'blade': (180, 140, 110)},
    'gold_sword':    {'name': 'Altin Kilic',  'slot': 'weapon', 'dmg': 45, 'def': 0, 'spd': 0,
                      'blade': (242, 209, 25)},
    'shadow_sword':  {'name': 'Golge Kilic',  'slot': 'weapon', 'dmg': 55, 'def': 0, 'spd': 2,
                      'blade': (100, 0,  200)},
    # ── Zırhlar ──────────────────────────────────────────────────────
    'leather_armor': {'name': 'Deri Zirhi',   'slot': 'armor',  'dmg': 0, 'def': 8,  'spd': 0, 'blade': None},
    'stone_armor':   {'name': 'Tas Zirhi',    'slot': 'armor',  'dmg': 0, 'def': 18, 'spd': 0, 'blade': None},
    'iron_armor':    {'name': 'Demir Zirhi',  'slot': 'armor',  'dmg': 0, 'def': 28, 'spd': 0, 'blade': None},
    'gold_armor':    {'name': 'Altin Zirhi',  'slot': 'armor',  'dmg': 0, 'def': 32, 'spd': 0, 'blade': None},
    'shadow_armor':  {'name': 'Golge Zirhi',  'slot': 'armor',  'dmg': 0, 'def': 52, 'spd': 0, 'blade': None},
    # ── Botlar ───────────────────────────────────────────────────────
    'leather_boots': {'name': 'Deri Bot',     'slot': 'boots',  'dmg': 0, 'def': 3,  'spd': 2, 'blade': None},
    'mud_boots':     {'name': 'Camur Botu',   'slot': 'boots',  'dmg': 0, 'def': 5,  'spd': 3, 'blade': None},
    'swift_boots':   {'name': 'Hizli Bot',    'slot': 'boots',  'dmg': 0, 'def': 10, 'spd': 5, 'blade': None},
    # ── Yüzükler ─────────────────────────────────────────────────────
    'iron_ring':     {'name': 'Demir Yuzuk',  'slot': 'ring',   'dmg': 5,  'def': 3,  'spd': 0, 'blade': None},
    'gold_ring':     {'name': 'Altin Yuzuk',  'slot': 'ring',   'dmg': 10, 'def': 6,  'spd': 1, 'blade': None},
    'shadow_ring':   {'name': 'Golge Yuzugu', 'slot': 'ring',   'dmg': 18, 'def': 10, 'spd': 2, 'blade': None},
}

# Backward compat alias (used by crafting/shop)
EQUIPMENT_ITEMS: Dict[str, dict] = {
    bid: {
        'name':        base['name'],
        'slot':        base['slot'],
        'dmg':         base['dmg'],
        'def':         base['def'],
        'spd':         base['spd'],
        'blade_color': base['blade'],
    }
    for bid, base in ITEM_BASES.items()
}


def make_gear(base_id: str, rarity: str = 'common') -> dict:
    """Create a gear instance with rarity-scaled stats."""
    base = ITEM_BASES[base_id]
    mult = RARITIES[rarity]['mult']
    return {
        'base_id': base_id,
        'rarity':  rarity,
        'name':    f'[{RARITIES[rarity]["label"]}] {base["name"]}',
        'slot':    base['slot'],
        'dmg':     int(base['dmg'] * mult),
        'def':     int(base['def'] * mult),
        'spd':     base['spd'],
        'color':   RARITIES[rarity]['color'],
        'blade':   base.get('blade'),
    }


def roll_rarity(floor: int = 0) -> str:
    """Random rarity weighted by dungeon floor depth."""
    weights = {
        0: [60, 28, 10, 2],
        1: [40, 32, 22, 6],
        2: [20, 30, 32, 18],
    }
    pool = weights.get(floor, weights[0])
    r    = random.randint(1, 100)
    acc  = 0
    for i, w in enumerate(pool):
        acc += w
        if r <= acc:
            return RARITY_ORDER[i]
    return 'common'


def calc_pr(equipped: dict) -> int:
    """Simple power rating: weighted sum of equipped stats."""
    pr = 0
    for item in equipped.values():
        if item:
            pr += item['dmg'] * 2 + item['def'] + item['spd'] * 3
    return pr


# Loot pools per floor (base_id, chance)
FLOOR_GEAR_POOL = {
    0: [('wooden_sword', .35), ('leather_armor', .30), ('leather_boots', .25), ('iron_ring', .20)],
    1: [('stone_sword',  .40), ('stone_armor',  .35), ('mud_boots',     .30), ('iron_ring', .25)],
    2: [('gold_sword',   .45), ('gold_armor',   .40), ('swift_boots',   .35), ('gold_ring', .30),
        ('shadow_sword', .15), ('shadow_armor', .10), ('shadow_ring',   .10)],
}
