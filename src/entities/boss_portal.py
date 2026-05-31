"""Teleport portal — auto-teleports when stepped on, or press [G] from nearby."""
import builtins
import math
import time as _time
from ursina import Entity, Text, color, camera, destroy, Vec3

KEY_RANGE   = 5.0    # press [G] within this distance
TOUCH_RANGE = 2.2    # auto-teleport when standing this close
GLOBAL_CD   = 1.2    # seconds between any teleports (prevents bounce)


class BossPortal(Entity):
    """Glowing portal with a tall beam. Step onto it (or press [G]) to teleport."""

    _last_tp = 0.0   # class-wide cooldown timestamp

    def __init__(self, position, target, player, label='Arena',
                 rgb=(0.35, 0.65, 1.0)):
        pos = position if isinstance(position, Vec3) else Vec3(*position)
        super().__init__(position=pos)
        self.player  = player
        self.target  = target if isinstance(target, Vec3) else Vec3(*target)
        self.label   = label
        self.sibling = None      # the paired return portal (set externally)
        self._base   = builtins.__dict__.get('base')
        self._hint   = None
        self._near   = False
        self._armed  = True      # must leave & re-enter to auto-trigger again
        self._t      = 0.0

        r, g, b = rgb
        self._core = Entity(
            parent=self, model='cube',
            color=color.rgba(r, g, b, 0.65), scale=(0.9, 2.4, 0.9))
        # Tall beam visible from far
        self._beam = Entity(
            parent=self, model='cube',
            color=color.rgba(min(1, r + 0.2), min(1, g + 0.2), min(1, b + 0.2), 0.28),
            scale=(0.45, 40, 0.45), position=(0, 19, 0))
        self._ring = Entity(
            parent=self, model='quad', double_sided=True,
            color=color.rgba(min(1, r + 0.35), min(1, g + 0.35), min(1, b + 0.35), 0.9),
            scale=(2.0, 2.0), rotation_x=90)
        self._ring2 = Entity(
            parent=self, model='quad', double_sided=True,
            color=color.rgba(min(1, r + 0.2), min(1, g + 0.2), min(1, b + 0.2), 0.6),
            scale=(1.4, 1.4), rotation_x=90, position=(0, 0.8, 0))
        Entity(parent=self, model='cube',
               color=color.rgba(r * 0.55, g * 0.55, b * 0.55, 0.95),
               scale=(2.2, 0.16, 2.2), position=(0, -1.18, 0))

    # ------------------------------------------------------------------
    def _dist2(self) -> float:
        dx = self.player.x - self.x
        dy = self.player.y - self.y
        dz = self.player.z - self.z
        return dx * dx + dy * dy + dz * dz

    def _cooldown_ok(self) -> bool:
        return _time.time() - BossPortal._last_tp > GLOBAL_CD

    def _teleport(self):
        t = self.target
        self.player.position = Vec3(t.x, t.y, t.z)
        if hasattr(self.player, '_kb_vel'):
            self.player._kb_vel = (0.0, 0.0)
        BossPortal._last_tp = _time.time()
        self._armed = False
        if self.sibling:            # don't bounce back off the arrival portal
            self.sibling._armed = False
        print(f'[portal] teleport -> ({t.x:.0f}, {t.y:.0f}, {t.z:.0f})')
        if self._hint:
            destroy(self._hint)
            self._hint = None
        self._near = False

    def update(self):
        dt = self._base.clock.getDt() if self._base else 0.016
        self._t += dt
        self._ring.rotation_y  = (self._t * 130) % 360
        self._ring2.rotation_y = (-self._t * 95) % 360
        s = 1.0 + 0.14 * math.sin(self._t * 3.0)
        self._core.scale_y = 2.4 * s
        self._core.rotation_y = (self._t * 40) % 360

        d2 = self._dist2()

        # Re-arm once the player walks away
        if d2 > TOUCH_RANGE ** 2:
            self._armed = True
        # Auto-teleport when stepped on
        elif self._armed and self._cooldown_ok():
            self._teleport()
            return

        # Proximity hint
        near = d2 < KEY_RANGE ** 2
        if near and not self._near:
            self._hint = Text(
                parent=camera.ui, text=f'[G] {self.label}',
                origin=(0, 0), position=(0, -0.18),
                scale=1.4, color=color.cyan)
        elif not near and self._near and self._hint:
            destroy(self._hint)
            self._hint = None
        self._near = near

    def input(self, key):
        if key == 'g' and self._cooldown_ok() and self._dist2() < KEY_RANGE ** 2:
            self._teleport()
