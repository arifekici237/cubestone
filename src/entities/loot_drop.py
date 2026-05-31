import math
import builtins
from ursina import Entity, color, Vec3

_ITEM_COLORS = {
    'coin':      color.yellow,
    'slime_gel': color.lime,
}


class LootDrop(Entity):
    def __init__(self, position: Vec3, item_id: str, count: int):
        super().__init__(
            model='sphere',
            color=_ITEM_COLORS.get(item_id, color.white),
            scale=0.28,
            position=Vec3(position.x, position.y + 0.5, position.z),
        )
        self.item_id  = item_id
        self.count    = count
        self._t       = 0.0
        self._base_y  = position.y + 0.5
        self._base    = builtins.__dict__.get('base')

    def _dt(self):
        b = self._base
        return b.clock.getDt() if b else 0.016

    def update(self):
        dt = self._dt()
        self._t += dt
        self.y = self._base_y + math.sin(self._t * 3.5) * 0.18
        self.rotation_y += 120 * dt
