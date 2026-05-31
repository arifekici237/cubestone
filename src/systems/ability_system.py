"""Active ability system — [Q] first ability, [E] second ability."""
import builtins
from ursina import Entity, Vec3


class AbilitySystem(Entity):
    SPEED_BOOST_DUR  = 2.5
    MAGE_SLOW_DUR    = 3.0
    MAGE_SLOW_FACTOR = 0.35
    IRON_SKIN_DUR    = 4.0
    IRON_SKIN_MULT   = 0.5

    def __init__(self, player, player_state, spawn_manager, equipment, hud):
        super().__init__()
        self.player        = player
        self.player_state  = player_state
        self.spawn_manager = spawn_manager
        self.equipment     = equipment
        self.hud           = hud
        self._cd           = 0.0   # Q cooldown
        self._cd2          = 0.0   # E cooldown
        self._speed_t      = 0.0
        self._iron_skin_t  = 0.0
        self._base         = builtins.__dict__.get('base')

    def _dt(self):
        b = self._base
        return b.clock.getDt() if b else 0.016

    def _cls(self):
        return getattr(self.player_state, 'player_class', None)

    def update(self):
        dt  = self._dt()
        cls = self._cls()

        self._cd  = max(0.0, self._cd  - dt)
        self._cd2 = max(0.0, self._cd2 - dt)

        # Speed boost expiry (Ranger Q)
        if self._speed_t > 0:
            self._speed_t -= dt
            if self._speed_t <= 0:
                self._cancel_speed_boost()

        # Iron skin expiry (Knight E)
        if self._iron_skin_t > 0:
            self._iron_skin_t -= dt
            if self._iron_skin_t <= 0:
                self.player_state.damage_mult = 1.0

        if self.hud and cls:
            self.hud.update_ability(
                cls.ability_name,
                self._cd / cls.ability_cd if cls.ability_cd else 0.0,
            )
            if cls.ability2_cd > 0:
                self.hud.update_ability2(
                    cls.ability2_name,
                    self._cd2 / cls.ability2_cd,
                )

    def input(self, key):
        cls = self._cls()
        if not cls:
            return

        if key == 'q' and self._cd <= 0:
            from ui import sfx
            sfx.play('ability')
            self._activate_q(cls)
            self._cd = cls.ability_cd

        elif key == 'r' and cls.ability2_cd > 0 and self._cd2 <= 0:
            from ui import sfx
            sfx.play('ability', pitch=0.85)
            self._activate_e(cls)
            self._cd2 = cls.ability2_cd

    # ──────────────────────────────────────────────────────────────────
    # Q abilities
    # ──────────────────────────────────────────────────────────────────
    def _activate_q(self, cls):
        name = cls.name
        if name == 'knight':
            self._knight_smash()
        elif name == 'ranger':
            self._ranger_dash()
        elif name == 'mage':
            self._mage_blizzard()

    def _knight_smash(self):
        """3x melee damage + knockback to all enemies within 5 units. Orange shockwave."""
        from ui.ability_fx import ExpandingRing
        from ui.particles import show_damage
        px, py, pz = self.player.x, self.player.y, self.player.z
        REACH = 5.0
        dmg   = (15 + self.equipment.damage_bonus()) * 3
        for enemy in self._all_targets():
            dx = enemy.x - px
            dy = enemy.y - py
            dz = enemy.z - pz
            dist = (dx*dx + dy*dy + dz*dz) ** 0.5
            if dist <= REACH:
                epos = Vec3(enemy.x, enemy.y, enemy.z)   # save before destroy
                enemy.take_damage(dmg)
                show_damage(epos, dmg, critical=True)
                # Knockback only if enemy survived the hit
                if getattr(enemy, 'hp', 0) > 0:
                    xz = (dx*dx + dz*dz) ** 0.5 + 0.01
                    enemy.x += (dx / xz) * 3.5
                    enemy.z += (dz / xz) * 3.5
        ExpandingRing(
            Vec3(px, py, pz),
            col=(0.95, 0.55, 0.05, 0.85),
            max_radius=REACH,
            duration=0.40,
        )

    def _ranger_dash(self):
        """2.5× speed for SPEED_BOOST_DUR seconds + ghost afterimage."""
        from ui.ability_fx import GhostImage
        GhostImage(self.player.position)
        self._speed_t = self.SPEED_BOOST_DUR
        self.player._ability_speed_mult = 2.5

    def _mage_blizzard(self):
        """Slow all enemies within 12 units. Blue frost ring."""
        from ui.ability_fx import ExpandingRing
        px, py, pz = self.player.x, self.player.y, self.player.z
        REACH = 12.0
        for enemy in self._all_targets():
            dx = enemy.x - px
            dy = enemy.y - py
            dz = enemy.z - pz
            if (dx*dx + dy*dy + dz*dz) ** 0.5 <= REACH:
                if hasattr(enemy, 'slow'):
                    enemy.slow(self.MAGE_SLOW_DUR, self.MAGE_SLOW_FACTOR)
        ExpandingRing(
            Vec3(px, py, pz),
            col=(0.20, 0.60, 1.00, 0.80),
            max_radius=REACH,
            duration=0.55,
        )

    # ──────────────────────────────────────────────────────────────────
    # E abilities
    # ──────────────────────────────────────────────────────────────────
    def _activate_e(self, cls):
        name = cls.name
        if name == 'knight':
            self._knight_iron_skin()
        elif name == 'ranger':
            self._ranger_sharpshot()
        elif name == 'mage':
            self._mage_fireball()

    def _knight_iron_skin(self):
        """50% damage reduction for IRON_SKIN_DUR seconds. Golden ring."""
        from ui.ability_fx import ExpandingRing
        self.player_state.damage_mult = self.IRON_SKIN_MULT
        self._iron_skin_t = self.IRON_SKIN_DUR
        px, py, pz = self.player.x, self.player.y, self.player.z
        ExpandingRing(
            Vec3(px, py, pz),
            col=(1.00, 0.85, 0.10, 0.90),
            max_radius=2.5,
            duration=0.35,
        )

    def _ranger_sharpshot(self):
        """Instantly deal 4x damage to the nearest enemy within 20 units."""
        from ui.ability_fx import ExpandingRing
        from ui.particles import show_damage
        enemy = self._nearest_enemy(max_range=20.0)
        if enemy:
            dmg  = (15 + self.equipment.damage_bonus()) * 4
            epos = Vec3(enemy.x, enemy.y, enemy.z)
            enemy.take_damage(dmg)
            show_damage(epos, dmg, critical=True)
            ExpandingRing(
                epos,
                col=(0.30, 1.00, 0.30, 0.85),
                max_radius=2.5,
                duration=0.30,
            )

    def _mage_fireball(self):
        """Launch a fireball in the camera's look direction."""
        from ursina import camera
        from ui.ability_fx import Fireball
        fwd = camera.forward
        dmg = (15 + self.equipment.damage_bonus()) * 3
        spawn_pos = Vec3(
            self.player.x + fwd.x * 1.5,
            self.player.y + 1.2,
            self.player.z + fwd.z * 1.5,
        )
        Fireball(
            position=spawn_pos,
            direction=fwd,
            targets_getter=self._all_targets,
            damage=dmg,
        )

    # ──────────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────────
    def _all_targets(self):
        return list(self.spawn_manager._enemies) + list(self.spawn_manager._bosses)

    def _nearest_enemy(self, max_range=20.0):
        px, py, pz = self.player.x, self.player.y, self.player.z
        best, best_d = None, max_range * max_range
        for enemy in self._all_targets():
            dx = enemy.x - px
            dy = enemy.y - py
            dz = enemy.z - pz
            d2 = dx*dx + dy*dy + dz*dz
            if d2 < best_d:
                best_d, best = d2, enemy
        return best

    def _cancel_speed_boost(self):
        self.player._ability_speed_mult = 1.0
