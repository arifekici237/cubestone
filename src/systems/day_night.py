import math
import builtins
from ursina import Entity, Vec3, color


class DayNightCycle(Entity):
    """Rotates the sun and changes sky/ambient colour each frame."""

    _SKY = {
        'night': (10,  15,  40),
        'dawn':  (210, 110,  50),
        'day':   (100, 160, 220),
        'dusk':  (200,  80,  30),
    }

    def __init__(self, sun, ambient, cycle_seconds: float = 120.0):
        super().__init__()
        self.sun = sun
        self.ambient = ambient
        self.cycle_seconds = cycle_seconds
        self.t = 0.25
        self._step = 1.0 / (cycle_seconds * 60)
        self._base = builtins.__dict__.get('base')  # Panda3D ShowBase

    def update(self):
        self.t = (self.t + self._step) % 1.0
        angle = self.t * 2 * math.pi

        sx = math.sin(angle)
        sy = -math.cos(angle)
        if abs(sx) > 0.01 or abs(sy) > 0.01:
            self.sun.look_at(Vec3(sx, sy, 0.3))

        day_factor = max(0.0, sy)

        if self.t < 0.25:
            rgb = self._lerp(self._SKY['night'], self._SKY['dawn'],  self.t / 0.25)
        elif self.t < 0.5:
            rgb = self._lerp(self._SKY['dawn'],  self._SKY['day'],   (self.t - 0.25) / 0.25)
        elif self.t < 0.75:
            rgb = self._lerp(self._SKY['day'],   self._SKY['dusk'],  (self.t - 0.5)  / 0.25)
        else:
            rgb = self._lerp(self._SKY['dusk'],  self._SKY['night'], (self.t - 0.75) / 0.25)

        if self._base:
            self._base.setBackgroundColor(rgb[0]/255, rgb[1]/255, rgb[2]/255, 1)

        amb = int(50 + day_factor * 110)
        self.ambient.color = color.rgba(amb, amb, amb, 255)

    @staticmethod
    def _lerp(a, b, t):
        return (
            int(a[0] + (b[0] - a[0]) * t),
            int(a[1] + (b[1] - a[1]) * t),
            int(a[2] + (b[2] - a[2]) * t),
        )
