import builtins
import math
from ursina import Entity, color, destroy

_BODY_C  = color.rgb(70,  90,  60)
_LIMB_C  = color.rgb(60,  78,  50)
_SLOW_C  = color.rgb(40,  120, 160)
_FLASH_C = color.white


class CaveTroll(Entity):
    MAX_HP    = 80
    SPEED     = 1.5
    DAMAGE    = 20
    ATK_RANGE = 2.2
    ATK_CD    = 2.5

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

        # Torso
        self._body = Entity(
            parent=self, model='cube',
            color=_BODY_C,
            scale=(1.3, 1.6, 1.0),
            collider='box',
        )
        # Head
        Entity(
            parent=self._body, model='sphere',
            color=color.rgb(80, 100, 65),
            scale=(0.85, 0.75, 0.75),
            position=(0, 0.67, 0),
        )
        # Angry red eyes
        for ex in (-0.25, 0.25):
            Entity(
                parent=self._body, model='sphere',
                color=color.rgb(200, 40, 40),
                scale=(0.18, 0.18, 0.14),
                position=(ex, 0.68, -0.40),
            )
        # Thick arms
        self._arm_l = Entity(
            parent=self._body, model='cube',
            color=_LIMB_C,
            scale=(0.28, 0.65, 0.28),
            position=(-0.68, 0.05, 0),
        )
        self._arm_r = Entity(
            parent=self._body, model='cube',
            color=_LIMB_C,
            scale=(0.28, 0.65, 0.28),
            position=(0.68, 0.05, 0),
        )
        # Knuckles
        for ex in (-0.68, 0.68):
            Entity(
                parent=self._body, model='sphere',
                color=color.rgb(60, 78, 50),
                scale=(0.24, 0.24, 0.24),
                position=(ex, -0.34, -0.04),
            )
        # Stubby legs
        self._leg_l = Entity(
            parent=self._body, model='cube',
            color=_LIMB_C,
            scale=(0.30, 0.44, 0.30),
            position=(-0.24, -0.77, 0),
        )
        self._leg_r = Entity(
            parent=self._body, model='cube',
            color=_LIMB_C,
            scale=(0.30, 0.44, 0.30),
            position=(0.24, -0.77, 0),
        )

        # HP bar
        self._hp_bg = Entity(
            parent=self, model='quad',
            scale=(2.0, 0.16), position=(0, 1.6, 0),
            color=color.dark_gray,
        )
        self._hp_fill = Entity(
            parent=self._hp_bg, model='quad',
            scale=(1, 1), origin=(-0.5, 0),
            position=(-0.5, 0, -0.01),
            color=color.rgba(200, 40, 40, 255),
        )

    def _dt(self):
        b = self._base
        return b.clock.getDt() if b else 0.016

    def _cur_color(self):
        return _SLOW_C if self._slow_t > 0 else _BODY_C

    def _restore_colors(self):
        c = self._cur_color()
        for e in (self._body, self._arm_l, self._arm_r, self._leg_l, self._leg_r):
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
        s = math.sin(self._walk_t * 3)
        # Heavy stomp — bigger bob amplitude
        self._body.y = abs(s) * 0.14

        self._leg_l.rotation_x =  s * 20
        self._leg_r.rotation_x = -s * 20
        # Arms swing opposite — troll drags arms
        self._arm_l.rotation_x = -s * 18
        self._arm_r.rotation_x =  s * 18

        self._atk_timer -= dt
        if xz_dist < self.ATK_RANGE + 0.8 and self._atk_timer <= 0:
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
        self._flash_t = 0.14
        for e in (self._body, self._arm_l, self._arm_r, self._leg_l, self._leg_r):
            e.color = _FLASH_C
