import builtins
import math
from ursina import Entity, color, destroy

_BONE_C  = color.rgb(220, 218, 200)
_JOINT_C = color.rgb(200, 196, 175)
_SLOW_C  = color.rgb(80, 160, 220)
_FLASH_C = color.white


class Skeleton(Entity):
    MAX_HP    = 35
    SPEED     = 3.5
    DAMAGE    = 8
    ATK_RANGE = 2.0
    ATK_CD    = 1.8

    def __init__(self, position, player, player_state, hud=None, on_death=None):
        super().__init__(position=position)
        self.hp           = self.MAX_HP
        self.player       = player
        self.player_state = player_state
        self.hud          = hud
        self.on_death     = on_death
        self._atk_timer   = 0.0
        self._walk_t      = 0.0
        self._slow_t      = 0.0
        self._slow_factor = 1.0
        self._flash_t     = 0.0
        self._base        = builtins.__dict__.get('base')

        # Ribcage torso — narrow, skeletal
        self._body = Entity(
            parent=self, model='cube',
            color=_BONE_C,
            scale=(0.70, 0.90, 0.38),
            collider='box',
        )
        # Ribcage ribs (3 horizontal bars across chest)
        for ry in (-0.22, 0.0, 0.22):
            Entity(
                parent=self._body, model='cube',
                color=_JOINT_C,
                scale=(1.0, 0.12, 0.55),
                position=(0, ry, 0),
            )
        # Skull
        self._head = Entity(
            parent=self._body, model='cube',
            color=_BONE_C,
            scale=(0.72, 0.68, 0.62),
            position=(0, 0.72, 0),
        )
        # Dark eye sockets
        for ex in (-0.22, 0.22):
            Entity(
                parent=self._head, model='cube',
                color=color.rgb(10, 10, 20),
                scale=(0.24, 0.22, 0.30),
                position=(ex, 0.08, -0.54),
            )
        # Jaw / teeth
        Entity(
            parent=self._head, model='cube',
            color=_BONE_C,
            scale=(0.60, 0.16, 0.40),
            position=(0, -0.34, -0.08),
        )

        # Arms — thin bones
        self._arm_l = Entity(
            parent=self._body, model='cube',
            color=_BONE_C,
            scale=(0.14, 0.58, 0.14),
            position=(-0.46, 0.05, 0),
        )
        self._arm_r = Entity(
            parent=self._body, model='cube',
            color=_BONE_C,
            scale=(0.14, 0.58, 0.14),
            position=(0.46, 0.05, 0),
        )
        # Bony hands (small spheres)
        for hx in (-0.46, 0.46):
            Entity(
                parent=self._body, model='sphere',
                color=_JOINT_C,
                scale=(0.18, 0.18, 0.18),
                position=(hx, -0.34, 0),
            )

        # Leg bones
        self._leg_l = Entity(
            parent=self._body, model='cube',
            color=_BONE_C,
            scale=(0.14, 0.52, 0.14),
            position=(-0.18, -0.70, 0),
        )
        self._leg_r = Entity(
            parent=self._body, model='cube',
            color=_BONE_C,
            scale=(0.14, 0.52, 0.14),
            position=(0.18, -0.70, 0),
        )
        # Knee joints
        for kx in (-0.18, 0.18):
            Entity(
                parent=self._body, model='sphere',
                color=_JOINT_C,
                scale=(0.16, 0.16, 0.16),
                position=(kx, -0.48, 0),
            )

        # HP bar
        self._hp_bg = Entity(
            parent=self, model='quad',
            scale=(1.6, 0.14), position=(0, 1.4, 0),
            color=color.dark_gray,
        )
        self._hp_fill = Entity(
            parent=self._hp_bg, model='quad',
            scale=(1, 1), origin=(-0.5, 0),
            position=(-0.5, 0, -0.01),
            color=color.rgba(160, 200, 240, 255),
        )

    def _dt(self):
        b = self._base
        return b.clock.getDt() if b else 0.016

    def _cur_color(self):
        return _SLOW_C if self._slow_t > 0 else _BONE_C

    def _restore_colors(self):
        c = self._cur_color()
        for e in (self._body, self._arm_l, self._arm_r, self._leg_l, self._leg_r, self._head):
            e.color = c

    def slow(self, duration: float, factor: float = 0.4):
        self._slow_t      = duration
        self._slow_factor = factor
        if self._flash_t <= 0:
            self._restore_colors()

    def update(self):
        dt = self._dt()

        if self._flash_t > 0:
            self._flash_t -= dt
            if self._flash_t <= 0:
                self._restore_colors()

        if self._slow_t > 0:
            self._slow_t -= dt
            if self._slow_t <= 0:
                self._slow_factor = 1.0
                if self._flash_t <= 0:
                    self._restore_colors()

        dx = self.player.x - self.x
        dy = self.player.y - self.y
        dz = self.player.z - self.z
        dist    = (dx*dx + dy*dy + dz*dz) ** 0.5
        xz_dist = (dx*dx + dz*dz) ** 0.5

        eff_spd = self.SPEED * self._slow_factor

        if dist > self.ATK_RANGE and dist > 0:
            self.x += dx / dist * eff_spd * dt
            self.y += dy / dist * eff_spd * dt
            self.z += dz / dist * eff_spd * dt

        if xz_dist > 0.2:
            self._body.rotation_y = math.degrees(math.atan2(dx, dz))

        self._walk_t += dt * self._slow_factor
        s = math.sin(self._walk_t * 6)
        # Skittery, jerky gait — small bob
        self._body.y = abs(s) * 0.06

        self._leg_l.rotation_x =  s * 24
        self._leg_r.rotation_x = -s * 24
        self._arm_l.rotation_x = -s * 20
        self._arm_r.rotation_x =  s * 20

        self._atk_timer -= dt
        if xz_dist < self.ATK_RANGE + 0.5 and self._atk_timer <= 0:
            self.player_state.take_damage(self.DAMAGE)
            if self.hud:
                self.hud.set_health(self.player_state.health, self.player_state.max_health)
            self._atk_timer = self.ATK_CD

    def take_damage(self, amount: int):
        self.hp = max(0, self.hp - amount)
        self._hp_fill.scale_x = self.hp / self.MAX_HP
        if self.hp <= 0:
            destroy(self._hp_bg)
            destroy(self._body)
            if self.on_death:
                self.on_death(self)
            destroy(self)
            return
        self._flash_t = 0.12
        for e in (self._body, self._arm_l, self._arm_r, self._leg_l, self._leg_r, self._head):
            e.color = _FLASH_C
