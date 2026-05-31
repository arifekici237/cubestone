import builtins
import random
from ursina import Entity, Text, color, camera, destroy, invoke

from systems.gear import FLOOR_GEAR_POOL, make_gear, roll_rarity

_LOOT = {
    0: {'coin': (6,  15), 'slime_gel': (1, 3), 'health_potion': (0, 1)},
    1: {'coin': (15, 30), 'slime_gel': (2, 4), 'health_potion': (1, 2)},
    2: {'coin': (25, 50), 'slime_gel': (3, 6), 'health_potion': (2, 3)},
}

INTERACT_DIST = 3.0


class DungeonChest(Entity):
    def __init__(self, position, player, item_counts, equipment,
                 floor: int = 0, on_collect=None):
        super().__init__(position=position)
        self.player      = player
        self.item_counts = item_counts
        self.equipment   = equipment
        self.floor       = min(max(floor, 0), 2)
        self.on_collect  = on_collect
        self._collected  = False
        self._hint       = None
        self._near_prev  = False
        self._base       = builtins.__dict__.get('base')

        self._body = Entity(parent=self, model='cube',
                            color=color.rgb(139, 90, 43),
                            scale=(0.80, 0.55, 0.55))
        Entity(parent=self._body, model='cube',
               color=color.rgb(165, 115, 55),
               scale=(1.0, 0.35, 1.0), position=(0, 0.68, 0))
        Entity(parent=self._body, model='cube',
               color=color.rgb(242, 209, 25),
               scale=(0.22, 0.22, 0.14), position=(0, 0.18, -0.52))

    # ------------------------------------------------------------------
    def _dist2(self) -> float:
        dx = self.player.x - self.x
        dy = self.player.y - self.y
        dz = self.player.z - self.z
        return dx * dx + dy * dy + dz * dz

    def update(self):
        if self._collected:
            return
        near = self._dist2() < INTERACT_DIST ** 2
        if near and not self._near_prev:
            self._hint = Text(
                parent=camera.ui, text='[G] Sandigi ac',
                origin=(0, 0), position=(0, -0.28),
                scale=1.1, color=color.yellow,
            )
        elif not near and self._near_prev:
            if self._hint:
                destroy(self._hint)
                self._hint = None
        self._near_prev = near

    def input(self, key):
        if self._collected or key != 'g':
            return
        if self._dist2() < INTERACT_DIST ** 2:
            self._open()

    # ------------------------------------------------------------------
    def _open(self):
        self._collected = True
        if self._hint:
            destroy(self._hint)
            self._hint = None

        table  = _LOOT[self.floor]
        rng    = random
        gained = []

        coins = rng.randint(*table['coin'])
        gels  = rng.randint(*table['slime_gel'])
        self.item_counts['coin']      = self.item_counts.get('coin', 0) + coins
        self.item_counts['slime_gel'] = self.item_counts.get('slime_gel', 0) + gels
        gained.append(f'+{coins} coin')
        gained.append(f'+{gels} jel')

        hp = rng.randint(*table['health_potion'])
        if hp > 0:
            self.item_counts['health_potion'] = self.item_counts.get('health_potion', 0) + hp
            gained.append(f'+{hp} iksir')

        # Equipment roll — one item from floor pool with rarity
        pool = FLOOR_GEAR_POOL.get(self.floor, [])
        for base_id, chance in pool:
            if rng.random() < chance:
                rarity = roll_rarity(self.floor)
                gear   = make_gear(base_id, rarity)
                self.equipment.add_gear_dict(gear)
                if self.equipment.on_change:
                    self.equipment.on_change()
                gained.append(f'+{gear["name"]}')
                break

        msg_text = '  '.join(gained)
        msg = Text(
            parent=camera.ui, text=f'Sandik: {msg_text}',
            origin=(0, 0), position=(0, -0.10),
            scale=1.0, color=color.lime,
        )
        invoke(destroy, msg, delay=3.5)

        if self.on_collect:
            self.on_collect()

        invoke(destroy, self, delay=0.05)
