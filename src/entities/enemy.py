import builtins
import math
from ursina import Entity, color, Vec3, destroy


class Enemy(Entity):
    MAX_HP    = 30
    SPEED     = 3.0
    DAMAGE    = 8
    ATK_RANGE = 1.5
    ATK_CD    = 1.5

    def __init__(self, position, player, player_state, hud=None, on_death=None):
        super().__init__(position=position)
        self.hp           = self.MAX_HP
        self.player       = player
        self.player_state = player_state
        self.hud          = hud
        self.on_death     = on_death
        self._atk_timer   = 0.0
        self._bounce_t    = 0.0
        self._slow_t      = 0.0
        self._slow_factor = 1.0
        self._base        = builtins.__dict__.get('base')

        self._body = Entity(
            parent=self,
            model='sphere',
            color=color.lime,
            scale=(1.0, 0.65, 1.0),
            collider='sphere',
        )

        for ex in (-0.3, 0.3):
            eye = Entity(
                parent=self._body,
                model='sphere',
                color=color.white,
                scale=(0.28, 0.28, 0.22),
                position=(ex, 0.22, -0.46),
            )
            Entity(
                parent=eye,
                model='sphere',
                color=color.black,
                scale=(0.5, 0.5, 0.35),
                position=(0, 0, -0.52),
            )

        self._hp_bg = Entity(
            parent=self,
            model='quad',
            scale=(1.2, 0.12),
            position=(0, 1.05, 0),
            color=color.dark_gray,
        )
        self._hp_fill = Entity(
            parent=self._hp_bg,
            model='quad',
            scale=(1, 1),
            origin=(-0.5, 0),
            position=(-0.5, 0, -0.01),
            color=color.red,
        )

        self._flash_t    = 0.0
        self._orig_color = None   # lazily captured on first hit

    def _dt(self):
        b = self._base
        return b.clock.getDt() if b else 0.016

    def slow(self, duration: float, factor: float = 0.4):
        """Slow the enemy for `duration` seconds (factor = speed multiplier)."""
        self._slow_t      = duration
        self._slow_factor = factor
        self._body.color  = color.cyan

    def update(self):
        dt = self._dt()

        # Hit flash recovery
        if self._flash_t > 0:
            self._flash_t -= dt
            if self._flash_t <= 0 and self._orig_color is not None:
                self._body.color = color.cyan if self._slow_t > 0 else self._orig_color

        if self._slow_t > 0:
            self._slow_t -= dt
            if self._slow_t <= 0:
                self._slow_factor = 1.0
                self._body.color  = self._orig_color if self._orig_color is not None else color.lime

        dx = self.player.x - self.x
        dy = self.player.y - self.y
        dz = self.player.z - self.z
        dist    = (dx * dx + dy * dy + dz * dz) ** 0.5
        xz_dist = (dx * dx + dz * dz) ** 0.5

        eff_spd = self.SPEED * self._slow_factor
        if dist > self.ATK_RANGE and dist > 0:
            self.x += dx / dist * eff_spd * dt
            self.y += dy / dist * eff_spd * dt
            self.z += dz / dist * eff_spd * dt

        if xz_dist > 0.2:
            self._body.rotation_y = math.degrees(math.atan2(dx, dz))

        self._bounce_t += dt
        self._body.y = abs(math.sin(self._bounce_t * 4)) * 0.15

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
        # White hit flash
        if self._orig_color is None:
            self._orig_color = self._body.color   # lazy-capture original color
        self._body.color = color.white
        self._flash_t    = 0.13
