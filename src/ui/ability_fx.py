"""Visual effects for active abilities."""
import builtins
from ursina import Entity, Vec3, color, destroy


class ExpandingRing(Entity):
    """Flat disk that expands from 0 to max_radius then destroys itself."""
    def __init__(self, position, col, max_radius=5.0, duration=0.45):
        super().__init__(
            model='quad',
            color=col,
            position=(position.x, position.y + 0.15, position.z),
            rotation_x=90,
            scale=0.2,
        )
        self._target = max_radius * 2.0  # quad scale = diameter
        self._dur    = duration
        self._t      = 0.0
        self._base   = builtins.__dict__.get('base')

    def _dt(self):
        b = self._base
        return b.clock.getDt() if b else 0.016

    def update(self):
        self._t += self._dt()
        t = min(self._t / self._dur, 1.0)
        self.scale = self._target * t
        if t >= 1.0:
            destroy(self)


class GhostImage(Entity):
    """Brief translucent afterimage of the player at a fixed position."""
    def __init__(self, position, duration=0.40):
        super().__init__(
            model='cube',
            color=color.rgba(60, 180, 255, 100),
            position=position,
            scale=(0.55, 1.75, 0.30),
        )
        self._dur  = duration
        self._t    = 0.0
        self._base = builtins.__dict__.get('base')

    def _dt(self):
        b = self._base
        return b.clock.getDt() if b else 0.016

    def update(self):
        self._t += self._dt()
        if self._t >= self._dur:
            destroy(self)


class Fireball(Entity):
    """Projectile that travels in a direction and damages the first enemy it hits."""
    SPEED  = 16.0
    RADIUS = 1.8

    def __init__(self, position, direction, targets_getter, damage):
        super().__init__(
            model='sphere',
            color=color.rgb(255, 100, 10),
            position=position,
            scale=0.55,
        )
        # Inner yellow glow
        Entity(
            parent=self, model='sphere',
            color=color.rgb(255, 230, 50),
            scale=0.45,
            position=(0, 0, 0),
        )
        self._dir     = direction   # normalized Vec3
        self._targets = targets_getter
        self._damage  = damage
        self._life    = 0.0
        self._base    = builtins.__dict__.get('base')

    def _dt(self):
        b = self._base
        return b.clock.getDt() if b else 0.016

    def update(self):
        dt = self._dt()
        self._life += dt
        if self._life > 3.5:
            destroy(self)
            return

        self.x += self._dir.x * self.SPEED * dt
        self.y += self._dir.y * self.SPEED * dt
        self.z += self._dir.z * self.SPEED * dt

        for enemy in list(self._targets()):
            dx = enemy.x - self.x
            dy = enemy.y - self.y
            dz = enemy.z - self.z
            if (dx*dx + dy*dy + dz*dz) ** 0.5 <= self.RADIUS:
                epos = Vec3(enemy.x, enemy.y, enemy.z)
                enemy.take_damage(self._damage)
                try:
                    from ui.particles import show_damage
                    show_damage(epos, self._damage, critical=True)
                except Exception:
                    pass
                ExpandingRing(epos, color.rgba(1.0, 0.55, 0.04, 0.70), max_radius=3.0, duration=0.35)
                destroy(self)
                return
