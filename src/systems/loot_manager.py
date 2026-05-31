import builtins
from typing import Callable, Optional
from ursina import Entity, Text, camera, color, destroy, invoke

from entities.loot_drop import LootDrop

PICKUP_RADIUS = 2.2


class LootManager(Entity):
    def __init__(self, player, item_counts: dict, equipment=None,
                 on_collect: Optional[Callable] = None):
        super().__init__()
        self.player      = player
        self.item_counts = item_counts
        self.equipment   = equipment
        self.on_collect  = on_collect
        self._drops: list = []
        self._base = builtins.__dict__.get('base')

    def spawn_at(self, position, loot_list):
        for item_id, count in loot_list:
            drop = LootDrop(position=position, item_id=item_id, count=count)
            self._drops.append(drop)

    def give_gear(self, gear: dict):
        """Instantly add a gear dict to player's bag and notify."""
        if self.equipment:
            self.equipment.add_gear_dict(gear)
            if self.equipment.on_change:
                self.equipment.on_change()
            from ui import sfx
            sfx.play('pickup', pitch=1.2)   # brighter ding for rare gear
            msg = Text(
                parent=camera.ui, text=f'Dugtu: +{gear["name"]}',
                origin=(0, 0), position=(0, -0.18),
                scale=1.0, color=color.rgb(*gear['color']),
            )
            invoke(destroy, msg, delay=3.0)

    def update(self):
        if not self._drops:
            return
        px, py, pz = self.player.x, self.player.y, self.player.z
        collected = []
        for drop in self._drops:
            dx, dy, dz = drop.x - px, drop.y - py, drop.z - pz
            if (dx*dx + dy*dy + dz*dz) ** 0.5 <= PICKUP_RADIUS:
                self.item_counts[drop.item_id] = (
                    self.item_counts.get(drop.item_id, 0) + drop.count
                )
                if self.on_collect:
                    self.on_collect(drop.item_id, drop.count)
                from ui import sfx
                sfx.play('pickup')
                collected.append(drop)
        for drop in collected:
            self._drops.remove(drop)
            destroy(drop)
