"""Sword viewmodel — first-person, PIL-textured blade."""
import builtins
import math
from PIL import Image
from ursina import Entity, Vec3, color, camera, Texture


def _make_blade_tex():
    """Metallic gradient: bright center, dark edges, slight base fade."""
    W, H = 32, 128
    img = Image.new('RGB', (W, H))
    cx = (W - 1) / 2
    for x in range(W):
        t = abs(x - cx) / cx          # 0 = center, 1 = edge
        base_r, base_g, base_b = 238, 244, 255
        edge_r, edge_g, edge_b = 110, 116, 135
        r = int(base_r + t * (edge_r - base_r))
        g = int(base_g + t * (edge_g - base_g))
        b = int(base_b + t * (edge_b - base_b))
        for y in range(H):
            # Darken near guard (bottom of texture = y=0)
            fade = 0.65 + 0.35 * min(y / 20, 1.0)
            img.putpixel((x, y), (int(r * fade), int(g * fade), int(b * fade)))
    return Texture(img)


def _make_handle_tex():
    """Leather wrap — dark base with alternating cord bands."""
    W, H = 8, 64
    img = Image.new('RGB', (W, H), (62, 36, 10))
    for y in range(H):
        # Band every 8 pixels
        band = (y // 6) % 2
        if band:
            c = (48, 26, 6)
        else:
            c = (74, 46, 14)
        for x in range(W):
            img.putpixel((x, y), c)
    return Texture(img)


class SwordViewModel(Entity):
    SWING_DUR = 0.26

    def __init__(self):
        super().__init__(parent=camera)
        self._rest_pos = Vec3(0.42, -0.32, 0.75)
        self._rest_rot = (8, -18, 0)
        self.position  = self._rest_pos
        self.rotation  = self._rest_rot

        self._base     = builtins.__dict__.get('base')
        self._swing_t  = 0.0
        self._swinging = False
        self._idle_t   = 0.0

        blade_tex  = _make_blade_tex()
        handle_tex = _make_handle_tex()

        # ── Blade ─────────────────────────────────────────────────────
        # Flat wide blade (wider & flatter = more sword-like)
        self._blade = Entity(
            parent=self, model='cube',
            color=color.white,       # white = texture shows true colors
            texture=blade_tex,
            scale=(0.068, 0.011, 0.52),
            position=(0, 0, 0.26),
        )
        # Blood groove — thin dark ridge along center of blade
        Entity(
            parent=self._blade, model='cube',
            color=color.rgb(90, 94, 112),
            scale=(0.09, 1.15, 0.88),
            position=(0, 0, 0),
        )
        # Blade tip bevel
        Entity(
            parent=self, model='cube',
            color=color.rgb(180, 188, 210),
            scale=(0.050, 0.011, 0.055),
            position=(0, 0, 0.525),
            rotation_x=18,
        )

        # ── Crossguard ────────────────────────────────────────────────
        # Main bar
        Entity(
            parent=self, model='cube',
            color=color.rgb(88, 54, 14),
            scale=(0.172, 0.018, 0.032),
            position=(0, 0, 0.0),
        )
        # Guard front ridge
        Entity(
            parent=self, model='cube',
            color=color.rgb(110, 72, 20),
            scale=(0.168, 0.010, 0.010),
            position=(0, 0.012, 0.0),
        )
        # Quillon tips (small spheres at guard ends)
        for gx in (-0.092, 0.092):
            Entity(
                parent=self, model='sphere',
                color=color.rgb(105, 68, 18),
                scale=(0.022, 0.022, 0.022),
                position=(gx, 0, 0),
            )

        # ── Handle ────────────────────────────────────────────────────
        Entity(
            parent=self, model='cube',
            color=color.white,
            texture=handle_tex,
            scale=(0.024, 0.024, 0.162),
            position=(0, 0, -0.094),
        )

        # ── Pommel ────────────────────────────────────────────────────
        Entity(
            parent=self, model='sphere',
            color=color.rgb(100, 62, 16),
            scale=(0.056, 0.056, 0.056),
            position=(0, 0, -0.182),
        )
        # Pommel gem
        Entity(
            parent=self, model='sphere',
            color=color.rgb(200, 80, 80),
            scale=(0.016, 0.016, 0.016),
            position=(0, 0.030, -0.182),
        )

    def _dt(self):
        b = self._base
        return b.clock.getDt() if b else 0.016

    def set_blade_color(self, c):
        # Tint the blade texture with rarity color
        self._blade.color = c

    def swing(self):
        self._swing_t  = 0.0
        self._swinging = True

    def update(self):
        dt = self._dt()
        self._idle_t += dt

        if self._swinging:
            self._swing_t += dt
            t = min(self._swing_t / self.SWING_DUR, 1.0)
            arc = math.sin(t * math.pi)
            self.z          = self._rest_pos.z + arc * 0.20
            self.y          = self._rest_pos.y - arc * 0.06
            self.rotation_x = self._rest_rot[0] - arc * 46
            self.rotation_z = self._rest_rot[2] - arc * 24
            if t >= 1.0:
                self._swinging = False
                self.position  = self._rest_pos
                self.rotation  = self._rest_rot
        else:
            s1 = math.sin(self._idle_t * 1.3)
            s2 = math.sin(self._idle_t * 0.85 + 0.8)
            self.y          = self._rest_pos.y + s1 * 0.007
            self.x          = self._rest_pos.x + s2 * 0.003
            self.rotation_z = self._rest_rot[2] + s1 * 1.6
