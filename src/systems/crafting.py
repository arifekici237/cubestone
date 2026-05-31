from typing import List, Dict, Any

BLOCK_NAMES = {
    1: 'Grass', 2: 'Dirt', 3: 'Stone', 4: 'Wood',
    5: 'Smooth Stone', 6: 'Planks', 7: 'Mud Block', 8: 'Gold Block',
    13: 'Iron Ore', 14: 'Coal', 17: 'Mesale',
}
ITEM_NAMES = {
    'coin':      'Coin',
    'slime_gel': 'Slime Gel',
}

RECIPES: List[Dict[str, Any]] = [
    # ── Bloklar ───────────────────────────────────────────────────────
    {
        'name':         'Mesale',
        'result_type':  'block',
        'result_id':    17,
        'result_count': 4,
        'ingredients':  {'block_14': 1, 'block_4': 1},   # 1 Coal + 1 Wood → 4 Torches
    },
    {
        'name':         'Smooth Stone',
        'result_type':  'block',
        'result_id':    5,
        'result_count': 2,
        'ingredients':  {'block_3': 4},
    },
    {
        'name':         'Planks',
        'result_type':  'block',
        'result_id':    6,
        'result_count': 3,
        'ingredients':  {'block_4': 2},
    },
    {
        'name':         'Mud Block',
        'result_type':  'block',
        'result_id':    7,
        'result_count': 2,
        'ingredients':  {'block_2': 3, 'item_slime_gel': 1},
    },
    {
        'name':         'Gold Block',
        'result_type':  'block',
        'result_id':    8,
        'result_count': 1,
        'ingredients':  {'item_coin': 5},
    },
    # ── Silahlar ─────────────────────────────────────────────────────
    {
        'name':         'Demir Kilic',
        'result_type':  'equipment',
        'result_id':    'iron_sword',
        'result_count': 1,
        'ingredients':  {'block_13': 4, 'block_4': 2},
    },
    {
        'name':         'Demir Zirh',
        'result_type':  'equipment',
        'result_id':    'iron_armor',
        'result_count': 1,
        'ingredients':  {'block_13': 6, 'block_3': 4},
    },
    {
        'name':         'Ahsap Kilic',
        'result_type':  'equipment',
        'result_id':    'wooden_sword',
        'result_count': 1,
        'ingredients':  {'block_4': 3, 'block_6': 2},
    },
    {
        'name':         'Tas Kilic',
        'result_type':  'equipment',
        'result_id':    'stone_sword',
        'result_count': 1,
        'ingredients':  {'block_3': 6, 'block_4': 2},
    },
    {
        'name':         'Altin Kilic',
        'result_type':  'equipment',
        'result_id':    'gold_sword',
        'result_count': 1,
        'ingredients':  {'block_8': 3, 'item_coin': 3},
    },
    # ── Zırh + Bot ───────────────────────────────────────────────────
    {
        'name':         'Tas Zirh',
        'result_type':  'equipment',
        'result_id':    'stone_armor',
        'result_count': 1,
        'ingredients':  {'block_3': 8, 'block_5': 2},
    },
    {
        'name':         'Altin Zirh',
        'result_type':  'equipment',
        'result_id':    'gold_armor',
        'result_count': 1,
        'ingredients':  {'block_8': 5, 'block_5': 4},
    },
    {
        'name':         'Camur Botu',
        'result_type':  'equipment',
        'result_id':    'mud_boots',
        'result_count': 1,
        'ingredients':  {'block_7': 4, 'item_slime_gel': 2},
    },
]


def _get(ing_key: str, bc: dict, ic: dict) -> int:
    if ing_key.startswith('block_'):
        return bc.get(int(ing_key[6:]), 0)
    if ing_key.startswith('item_'):
        return ic.get(ing_key[5:], 0)
    return 0


def _consume(ing_key: str, amount: int, bc: dict, ic: dict):
    if ing_key.startswith('block_'):
        bid = int(ing_key[6:])
        bc[bid] = max(0, bc.get(bid, 0) - amount)
    elif ing_key.startswith('item_'):
        iid = ing_key[5:]
        ic[iid] = max(0, ic.get(iid, 0) - amount)


class CraftingSystem:
    def __init__(self, block_counts: dict, item_counts: dict, equipment=None):
        self.block_counts = block_counts
        self.item_counts  = item_counts
        self.equipment    = equipment

    def can_craft(self, recipe: dict) -> bool:
        for k, n in recipe['ingredients'].items():
            if _get(k, self.block_counts, self.item_counts) < n:
                return False
        return True

    def craft(self, recipe: dict) -> bool:
        if not self.can_craft(recipe):
            return False
        for k, n in recipe['ingredients'].items():
            _consume(k, n, self.block_counts, self.item_counts)
        if recipe['result_type'] == 'block':
            bid = recipe['result_id']
            self.block_counts[bid] = self.block_counts.get(bid, 0) + recipe['result_count']
        elif recipe['result_type'] == 'equipment' and self.equipment:
            self.equipment.add_gear(recipe['result_id'], 'common')
        return True

    @staticmethod
    def format_ingredients(recipe: dict) -> str:
        parts = []
        for ing_key, count in recipe['ingredients'].items():
            if ing_key.startswith('block_'):
                name = BLOCK_NAMES.get(int(ing_key[6:]), ing_key)
            else:
                name = ITEM_NAMES.get(ing_key[5:], ing_key[5:].replace('_', ' ').title())
            parts.append(f'{count}x {name}')
        return ' + '.join(parts)
