import builtins
import math
from ursina import Entity, color, destroy

_BODY_C  = color.rgb(60,  100, 40)
_LIMB_C  = color.rgb(55,  88,  34)
_LEG_C   = color.rgb(48,  75,  28)
_SLOW_C  = color.rgb(40,  180, 200)
_FLASH_C = color.white


class Goblin(Entity):
    MAX_HP    = 20
    SPEED     = 4.5
    DAMAGE    = 5
    ATK_RANGE = 1.5
    ATK_CD    = 1.2

    def __init__(self, position, player, player_state, hud=None, on_death=None):
        super().__init__(position=position)
        self.hp           = self.MAX_HP
        self.player       = player
        self.player_state = player_state
        self.hud          = hud
        self.on_death     = on_death
        self._atk_timer   = 0.0
        self._run_t       = 0.0
        self._slow_t      = 0.0
        self._slow_factor = 1.0
        self._flash_t     = 0.0
        self._base        = builtins.__dict__.get('base')

        # Torso
        self._body = Entity(
            parent=self, model='cube',
            color=_BODY_C,
            scale=(0.55, 0.75, 0.45),
            collider='box',
        )
        # Head
        Entity(
            parent=self._body, model='sphere',
            color=color.rgb(80, 130, 50),
            scale=(0.70, 0.65, 0.65),
            position=(0, 0.72, 0),
        )
        # Eyes
        for ex in (-0.20, 0.20):
            Entity(
                parent=self._body, model='sphere',
                color=color.orange,
                scale=(0.22, 0.18, 0.15),
                position=(ex, 0.72, -0.32),
            )
        # Arms (children of body so they rotate with it)
        self._arm_l = Entity(
            parent=self._body, model='cube',
            color=_LIMB_C,
            scale=(0.26, 0.50, 0.24),
            position=(-0.66, 0.06, 0),
        )
        self._arm_r = Entity(
            parent=self._body, model='cube',
            color=_LIMB_C,
            scale=(0.26, 0.50, 0.24),
            position=(0.66, 0.06, 0),
        )
        # Fists
        for ex, arm in ((-0.66, self._arm_l), (0.66, self._arm_r)):
            Entity(
                parent=self._body, model='sphere',
                color=color.rgb(70, 115, 42),
                scale=(0.20, 0.20, 0.20),
                position=(ex, -0.24, 0),
            )
        # Legs
        self._leg_l = Entity(
            parent=self._body, model='cube',
            color=_LEG_C,
            scale=(0.28, 0.46, 0.26),
            position=(-0.24, -0.76, 0),
        )
        self._leg_r = Entity(
            parent=self._body, model='cube',
            color=_LEG_C,
            scale=(0.28, 0.46, 0.26),
            position=(0.24, -0.76, 0),
        )

        # HP bar
        self._hp_bg = Entity(
            parent=self, model='quad',
            scale=(0.9, 0.10), position=(0, 1.0, 0),
            color=color.dark_gray,
        )
        self._hp_fill = Entity(
            parent=self._hp_bg, model='quad',
            scale=(1, 1), origin=(-0.5, 0),
            position=(-0.5, 0, -0.01),
            color=color.orange,
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

        # Walk animation — speed-scaled
        self._run_t += dt * self._slow_factor
        s = math.sin(self._run_t * 8)
        self._body.y = abs(s) * 0.07

        self._leg_l.rotation_x =  s * 28
        self._leg_r.rotation_x = -s * 28
        self._arm_l.rotation_x = -s * 22
        self._arm_r.rotation_x =  s * 22

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
        # Hit flash
        self._flash_t = 0.13
        for e in (self._body, self._arm_l, self._arm_r, self._leg_l, self._leg_r):
            e.color = _FLASH_C
