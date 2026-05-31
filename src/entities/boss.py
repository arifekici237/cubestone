"""
Final Boss enemy — large, high HP, drops rare/epic gear on death.
Spawns inside towers and shrines.
"""
import builtins
import math
import random
from ursina import Entity, color, Vec3, destroy, Text, camera, invoke

from systems.gear import FLOOR_GEAR_POOL, make_gear


_BOSS_NAMES = {
    'tower':          'Kule Bekcisi',
    'shrine':         'Tapinak Muhafizi',
    'stronghold':     'Kale Lordu',
    'desert_pyramid': 'Col Firavunu',
    'snow_tower':     'Buz Lordu',
    'forest_shrine':  'Orman Ruhu',
    'dungeon_vault':  'Dungeon Lordu',   # underground vault boss
    'sky_citadel':    'Gok Kalesi Hukumdari',  # sky arena boss
}
_BOSS_DROPS = {
    'tower':          2,
    'shrine':         3,
    'stronghold':     2,
    'desert_pyramid': 3,
    'snow_tower':     2,
    'forest_shrine':  3,
    'dungeon_vault':  5,   # most drops — hardest to reach
    'sky_citadel':    5,
}

_BODY_C   = color.rgb(60,  20,  80)
_SLOW_C   = color.rgb(40,  80, 120)
_FLASH_C  = color.white
_CHARGE_C = color.rgb(200, 60,  20)


class Boss(Entity):
    MAX_HP      = 350
    SPEED       = 1.8
    DAMAGE      = 30
    ATK_RANGE   = 2.5
    ATK_CD      = 2.0
    CHARGE_CD   = 8.0
    AGGRO_RANGE = 18.0   # boss activates only when player gets this close
    DEAGGRO     = 36.0   # loses interest if player runs this far away

    def __init__(self, position, player, player_state, hud=None,
                 equipment=None, floor: int = 1,
                 structure_type: str = 'tower', on_death=None):
        super().__init__(position=position)
        # Arena bosses (vault / citadel) are significantly stronger
        if structure_type in ('dungeon_vault', 'sky_citadel'):
            self.MAX_HP = 600
            self.DAMAGE = 45
            self.SPEED  = 2.2
        self.hp             = self.MAX_HP
        self.player         = player
        self.player_state   = player_state
        self.hud            = hud
        self.equipment      = equipment
        self.floor          = floor
        self.structure_type = structure_type
        self.on_death       = on_death
        self._atk_timer     = 0.0
        self._charge_timer  = self.CHARGE_CD
        self._walk_t        = 0.0
        self._slow_t        = 0.0
        self._slow_factor   = 1.0
        self._flash_t       = 0.0
        self._charging      = False
        self._aggro         = False
        self._base          = builtins.__dict__.get('base')

        boss_name = _BOSS_NAMES.get(structure_type, 'Canavar')

        # Main body
        self._body = Entity(
            parent=self, model='cube',
            color=_BODY_C,
            scale=(2.0, 2.4, 1.6),
            collider='box',
        )
        # Armored chest plate
        Entity(
            parent=self._body, model='cube',
            color=color.rgb(110, 70, 25),
            scale=(0.80, 0.46, 0.42),
            position=(0, 0.12, -0.52),
        )
        # Chest plate bolts
        for bx in (-0.22, 0.22):
            Entity(
                parent=self._body, model='sphere',
                color=color.rgb(160, 130, 50),
                scale=(0.08, 0.08, 0.06),
                position=(bx, 0.12, -0.74),
            )
        # Head
        self._head = Entity(
            parent=self._body, model='cube',
            color=color.rgb(50, 15, 70),
            scale=(0.70, 0.60, 0.60),
            position=(0, 0.60, 0),
        )
        # Glowing red eyes + orange core
        for ex in (-0.22, 0.22):
            eye = Entity(
                parent=self._head, model='sphere',
                color=color.rgb(255, 40, 0),
                scale=(0.25, 0.20, 0.15),
                position=(ex, 0, -0.52),
            )
            Entity(
                parent=eye, model='sphere',
                color=color.rgb(255, 200, 60),
                scale=(0.40, 0.40, 0.30),
                position=(0, 0, -0.55),
            )
        # Horns on head
        for hx in (-0.28, 0.28):
            Entity(
                parent=self._head, model='cube',
                color=color.rgb(35, 10, 55),
                scale=(0.12, 0.30, 0.10),
                position=(hx, 0.48, 0),
                rotation_z=hx * 25,
            )
        # Shoulder spikes
        for sx in (-0.62, 0.62):
            Entity(
                parent=self._body, model='cube',
                color=color.rgb(80, 50, 15),
                scale=(0.22, 0.42, 0.22),
                position=(sx, 0.30, 0),
            )
            # Spike tip
            Entity(
                parent=self._body, model='sphere',
                color=color.rgb(110, 70, 20),
                scale=(0.18, 0.18, 0.18),
                position=(sx, 0.56, 0),
            )
        # Arms
        self._arm_l = Entity(
            parent=self._body, model='cube',
            color=color.rgb(55, 18, 72),
            scale=(0.26, 0.68, 0.26),
            position=(-0.68, 0.10, 0),
        )
        self._arm_r = Entity(
            parent=self._body, model='cube',
            color=color.rgb(55, 18, 72),
            scale=(0.26, 0.68, 0.26),
            position=(0.68, 0.10, 0),
        )
        # Right arm weapon (club/mace)
        Entity(
            parent=self._arm_r, model='cube',
            color=color.rgb(90, 55, 15),
            scale=(0.40, 0.16, 0.40),
            position=(0, -0.64, 0),
        )
        Entity(
            parent=self._arm_r, model='cube',
            color=color.rgb(70, 40, 10),
            scale=(0.18, 0.40, 0.18),
            position=(0, -0.40, 0),
        )

        # HP bar
        self._hp_bg = Entity(
            parent=self, model='quad',
            scale=(3.0, 0.20), position=(0, 2.2, 0),
            color=color.rgba(20, 10, 30, 220),
        )
        self._hp_fill = Entity(
            parent=self._hp_bg, model='quad',
            scale=(1, 1), origin=(-0.5, 0),
            position=(-0.5, 0, -0.01),
            color=color.rgb(180, 20, 220),
        )
        self._name_text = Text(
            parent=self,
            text=boss_name,
            origin=(0, -0.5), position=(0, 2.6, 0),
            scale=3.5, color=color.rgb(220, 160, 255),
            billboard=True,
        )

    def _dt(self):
        b = self._base
        return b.clock.getDt() if b else 0.016

    def _cur_color(self):
        return _SLOW_C if self._slow_t > 0 else _BODY_C

    def _restore_colors(self):
        c = self._cur_color()
        for e in (self._body, self._arm_l, self._arm_r):
            e.color = c

    def slow(self, duration: float, factor: float = 0.4):
        self._slow_t      = duration
        self._slow_factor = factor
        if self._flash_t <= 0 and not self._charging:
            self._restore_colors()

    def update(self):
        dt = self._dt()

        if self._flash_t > 0:
            self._flash_t -= dt
            if self._flash_t <= 0:
                if not self._charging:
                    self._restore_colors()

        if self._slow_t > 0:
            self._slow_t -= dt
            if self._slow_t <= 0:
                self._slow_factor = 1.0
                if self._flash_t <= 0 and not self._charging:
                    self._restore_colors()

        dx = self.player.x - self.x
        dy = self.player.y - self.y
        dz = self.player.z - self.z
        dist    = (dx*dx + dy*dy + dz*dz) ** 0.5
        xz_dist = (dx*dx + dz*dz) ** 0.5

        # Aggro / deaggro
        if not self._aggro and dist < self.AGGRO_RANGE:
            self._aggro = True
        elif self._aggro and dist > self.DEAGGRO:
            self._aggro = False
            self._charging = False

        if not self._aggro:
            # Idle bob only — boss stays put
            self._walk_t += dt * 0.3
            s = math.sin(self._walk_t * 2.0)
            self._body.y = abs(s) * 0.06
            return

        eff_spd = self.SPEED * self._slow_factor

        # Charge countdown
        self._charge_timer -= dt
        if self._charge_timer <= 0 and dist < self.AGGRO_RANGE:
            self._charging     = True
            self._charge_timer = self.CHARGE_CD
        if self._charging:
            eff_spd = self.SPEED * 4
            if dist <= self.ATK_RANGE + 0.5:
                self._charging = False

        if dist > self.ATK_RANGE and dist > 0:
            self.x += dx / dist * eff_spd * dt
            self.y += dy / dist * eff_spd * dt
            self.z += dz / dist * eff_spd * dt

        if xz_dist > 0.2:
            self._body.rotation_y = math.degrees(math.atan2(dx, dz))

        self._walk_t += dt * self._slow_factor
        s = math.sin(self._walk_t * 2.5)

        # Stomp bob — wider during charge
        bob_amp = 0.20 if self._charging else 0.12
        self._body.y = abs(s) * bob_amp

        # Arm swing
        self._arm_l.rotation_x = -s * 22
        self._arm_r.rotation_x =  s * 22

        # Charge color pulse
        if self._charging and self._flash_t <= 0:
            pulse = (math.sin(self._walk_t * 12) + 1) * 0.5
            r = int(60 + pulse * 140)
            for e in (self._body, self._arm_l, self._arm_r):
                e.color = color.rgb(r, 20, 40)
        elif not self._charging and self._flash_t <= 0:
            self._restore_colors()

        self._atk_timer -= dt
        if xz_dist < self.ATK_RANGE + 1.0 and self._atk_timer <= 0:
            self.player_state.take_damage(self.DAMAGE)
            if self.hud:
                self.hud.set_health(self.player_state.health,
                                    self.player_state.max_health)
            self._atk_timer = self.ATK_CD

    def take_damage(self, amount: int):
        self.hp = max(0, self.hp - amount)
        ratio = self.hp / self.MAX_HP
        self._hp_fill.scale_x = ratio
        r = int(180 + (1 - ratio) * 75)
        g = int(20 * ratio)
        self._hp_fill.color = color.rgb(r, g, 220)

        if self.hp <= 0:
            self._die()
            return

        self._flash_t = 0.15
        for e in (self._body, self._arm_l, self._arm_r):
            e.color = _FLASH_C

    def _die(self):
        drop_count = _BOSS_DROPS.get(self.structure_type, 2)
        if self.equipment:
            pool = FLOOR_GEAR_POOL.get(min(self.floor + 1, 2), [])
            if not pool:
                pool = FLOOR_GEAR_POOL.get(self.floor, [])
            for _ in range(drop_count):
                base_id = random.choice(pool)[0]
                r = random.random()
                rarity = 'epic' if r < 0.40 else 'rare' if r < 0.80 else 'uncommon'
                self.equipment.add_gear_dict(make_gear(base_id, rarity))
            if self.equipment.on_change:
                self.equipment.on_change()

        boss_name = _BOSS_NAMES.get(self.structure_type, 'Boss')
        msg = Text(
            parent=camera.ui,
            text=f'[BOSS ÖLDÜRÜLDÜ] {boss_name}!  +{drop_count} Efsanevi Ekipman!',
            origin=(0, 0), position=(0, 0.15),
            scale=1.3, color=color.rgb(255, 180, 50),
        )
        invoke(destroy, msg, delay=5.0)

        if self.on_death:
            self.on_death(self)

        destroy(self._name_text)
        destroy(self._hp_bg)
        destroy(self._body)
        destroy(self)
