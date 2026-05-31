"""Reusable visual effects: floating damage numbers and block-break fragments."""
import builtins
import random as _rand
from ursina import Entity, Text, camera, color, Vec3, invoke, destroy, time


# ── Coordinate helper ────────────────────────────────────────────────────────

def _world_to_screen(world_pos):
    """Project a 3-D Ursina world position onto camera.ui coordinates.
    Returns (sx, sy) or None if behind the camera."""
    try:
        from panda3d.core import Point3, Point2
        base = builtins.__dict__.get('base')
        if not base:
            return None
        # Ursina is Y-up; Panda3D render is Z-up → swap Y/Z
        p = Point3(world_pos.x, world_pos.z, world_pos.y)
        cam_rel = base.cam.getRelativePoint(base.render, p)
        pt2 = Point2()
        if not base.camLens.project(cam_rel, pt2):
            return None   # behind camera
        aspect = base.getAspectRatio()
        return (pt2.x * 0.5 * aspect, pt2.y * 0.5)
    except Exception:
        return None


# ── Floating damage numbers ──────────────────────────────────────────────────

_hit_idx = 0


class _FloatNum(Entity):
    """Self-updating floating text entity that fades and rises over time."""

    def __init__(self, text_str, sx, sy, base_color, sc):
        super().__init__(parent=camera.ui)
        self._t    = 0.0
        self._sx   = sx
        self._sy   = sy
        self._r    = base_color[0]
        self._g    = base_color[1]
        self._b    = base_color[2]
        self._txt  = Text(parent=self, text=text_str,
                          origin=(0, 0),
                          position=(0, 0),
                          scale=sc,
                          color=color.rgba(*base_color, 255))

    def update(self):
        self._t += time.dt
        # Rise and fade over 0.80 s
        progress = min(self._t / 0.80, 1.0)
        self._txt.y  = self._t * 0.28
        alpha = int(255 * (1.0 - progress))
        self._txt.color = color.rgba(self._r, self._g, self._b, alpha)
        if self._t >= 0.85:
            destroy(self)


def show_damage(position, amount: int, critical: bool = False):
    """Show a floating '-amount' (or 'amount!' for criticals) at the enemy."""
    global _hit_idx
    screen = _world_to_screen(position)
    if screen is None:
        return
    sx, sy = screen
    _hit_idx = (_hit_idx + 1) % 7
    offset_x = (_hit_idx - 3) * 0.028   # spread repeated hits horizontally

    if critical:
        base_c = (1.0, 0.88, 0.16)   # golden
        txt    = f'{amount}!'
        sc     = 3.2
    else:
        base_c = (1.0, 0.25, 0.22)   # red
        txt    = f'-{amount}'
        sc     = 2.5

    n = _FloatNum(txt, sx + offset_x, sy + 0.04, base_c, sc)
    n.x = sx + offset_x
    n.y = sy + 0.04


# ── Block-break fragments ────────────────────────────────────────────────────

class _Fragment(Entity):
    """A tiny spinning cube that falls and fades after a block is broken."""

    def __init__(self, pos, vel, c, fade, lifetime):
        super().__init__(model='cube', color=c, scale=_rand.uniform(0.06, 0.13),
                         position=pos)
        self._vx  = vel[0]
        self._vy  = vel[1]
        self._vz  = vel[2]
        self._c   = c
        self._fc  = fade
        self._dur = lifetime
        self._t   = 0.0

    def update(self):
        dt = time.dt
        self._t  += dt
        self._vy -= 14.0 * dt          # fake gravity
        self.x   += self._vx * dt
        self.y   += self._vy * dt
        self.z   += self._vz * dt
        progress  = min(self._t / self._dur, 1.0)
        alpha     = int(220 * (1.0 - progress))
        self.color = color.rgba(self._c[0], self._c[1], self._c[2], alpha)
        if self._t >= self._dur:
            destroy(self)


def block_break_burst(wx: int, wy: int, wz: int, block_id: int):
    """Spawn 8 small fragment cubes bursting from the broken block position."""
    try:
        from render.mesher import _BLOCK_COLORS
        entry = _BLOCK_COLORS.get(block_id)
        if not entry:
            return
        rgb = entry['side']
        rc  = (int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))
        c   = color.rgba(*rc, 220)
        fc  = color.rgba(*rc, 0)
        for _ in range(8):
            vel = (
                _rand.uniform(-4.0, 4.0),
                _rand.uniform(2.5, 6.5),
                _rand.uniform(-4.0, 4.0),
            )
            pos = Vec3(
                wx + 0.5 + _rand.uniform(-0.3, 0.3),
                wy + 0.5 + _rand.uniform(0.0, 0.4),
                wz + 0.5 + _rand.uniform(-0.3, 0.3),
            )
            _Fragment(pos, vel, c, fc, _rand.uniform(0.45, 0.70))
    except Exception:
        pass
