from typing import List, Dict, Any

# ── Satın alınabilecekler (coin harcar, blok/eşya kazanır) ────────────
BUY_ITEMS: List[Dict[str, Any]] = [
    {'name': 'Grass x5',     'type': 'block',     'id': 1,                 'count': 5, 'price': 2},
    {'name': 'Stone x5',     'type': 'block',     'id': 3,                 'count': 5, 'price': 3},
    {'name': 'Wood x3',      'type': 'block',     'id': 4,                 'count': 3, 'price': 2},
    {'name': 'Dirt x5',      'type': 'block',     'id': 2,                 'count': 5, 'price': 1},
    {'name': 'Iyilestirme',  'type': 'item',      'id': 'health_potion',   'count': 1, 'price': 5},
    {'name': 'Slime Gel x2', 'type': 'item',      'id': 'slime_gel',       'count': 2, 'price': 4},
    {'name': 'Ahsap Kilic',  'type': 'equipment', 'id': 'wooden_sword',    'count': 1, 'price': 8},
    {'name': 'Tas Kilic',    'type': 'equipment', 'id': 'stone_sword',     'count': 1, 'price': 20},
    {'name': 'Tas Zirh',     'type': 'equipment', 'id': 'stone_armor',     'count': 1, 'price': 15},
]

# ── Satılabilecekler (blok verir, coin alır) ──────────────────────────
SELL_ITEMS: List[Dict[str, Any]] = [
    {'name': 'Grass',        'type': 'block', 'id': 1, 'count': 1, 'reward': 1},
    {'name': 'Dirt',         'type': 'block', 'id': 2, 'count': 1, 'reward': 1},
    {'name': 'Stone',        'type': 'block', 'id': 3, 'count': 1, 'reward': 2},
    {'name': 'Wood',         'type': 'block', 'id': 4, 'count': 1, 'reward': 2},
    {'name': 'Smooth Stone', 'type': 'block', 'id': 5, 'count': 1, 'reward': 3},
]


class ShopSystem:
    def __init__(self, block_counts: dict, item_counts: dict, equipment=None):
        self.block_counts = block_counts
        self.item_counts  = item_counts
        self.equipment    = equipment

    def coins(self) -> int:
        return self.item_counts.get('coin', 0)

    def _add_coins(self, n: int):
        self.item_counts['coin'] = self.item_counts.get('coin', 0) + n

    def can_buy(self, item: dict) -> bool:
        return self.coins() >= item['price']

    def buy(self, item: dict) -> bool:
        if not self.can_buy(item):
            return False
        self.item_counts['coin'] -= item['price']
        if item['type'] == 'block':
            bid = item['id']
            self.block_counts[bid] = self.block_counts.get(bid, 0) + item['count']
        elif item['type'] == 'item':
            key = item['id']
            self.item_counts[key] = self.item_counts.get(key, 0) + item['count']
        elif item['type'] == 'equipment' and self.equipment:
            self.equipment.add_gear(item['id'], 'common')
        return True

    def can_sell(self, item: dict) -> bool:
        if item['type'] == 'block':
            return self.block_counts.get(item['id'], 0) >= item['count']
        return self.item_counts.get(item['id'], 0) >= item['count']

    def sell(self, item: dict) -> bool:
        if not self.can_sell(item):
            return False
        if item['type'] == 'block':
            self.block_counts[item['id']] -= item['count']
        else:
            self.item_counts[item['id']] -= item['count']
        self._add_coins(item['reward'])
        return True
