import builtins
import random
import math
from ursina import Entity, Vec3

from entities.enemy import Enemy
from ui import sfx


class SpawnManager(Entity):
    MAX_ENEMIES  = 6
    SPAWN_RADIUS = 12.0
    SPAWN_MIN    = 5.0
    RESPAWN_CD   = 8.0
    DUNGEON_Y    = 20   # below this height counts as underground

    _XP_REWARDS = {'slime': 12, 'goblin': 20, 'troll': 35, 'skeleton': 28}

    def __init__(self, player, player_state, hud=None, loot_manager=None):
        super().__init__()
        self.player        = player
        self.player_state  = player_state
        self.hud           = hud
        self.loot_manager  = loot_manager
        self._enemies      = []
        self._bosses       = []
        self._respawn_t    = 0.0
        self._base         = builtins.__dict__.get('base')
        self._init_timer   = 2.0

    def update(self):
        dt = self._dt()
        if self._init_timer > 0:
            self._init_timer -= dt
            if self._init_timer <= 0:
                for _ in range(3):
                    self._spawn_one()
            return
        if len(self._enemies) < self.MAX_ENEMIES:
            self._respawn_t -= dt
            if self._respawn_t <= 0:
                self._spawn_one()
                self._respawn_t = self.RESPAWN_CD

    def _dt(self):
        b = self._base
        return b.clock.getDt() if b else 0.016

    def _spawn_one(self):
        angle = random.uniform(0, 6.2832)
        r     = random.uniform(self.SPAWN_MIN, self.SPAWN_RADIUS)
        px, py, pz = self.player.x, self.player.y, self.player.z
        pos = Vec3(
            px + r * math.cos(angle),
            py + 1.0,
            pz + r * math.sin(angle),
        )

        if py < -2:
            # Deep dungeon floors 4-5: undead skeletons
            from entities.skeleton import Skeleton
            e = Skeleton(
                position=pos,
                player=self.player,
                player_state=self.player_state,
                hud=self.hud,
                on_death=lambda enemy: self._on_enemy_death(enemy, 'skeleton'),
            )
        elif py < 6:
            # Mid dungeon floors 2-3: heavy cave trolls
            from entities.cave_troll import CaveTroll
            e = CaveTroll(
                position=pos,
                player=self.player,
                player_state=self.player_state,
                hud=self.hud,
                on_death=lambda enemy: self._on_enemy_death(enemy, 'troll'),
            )
        elif py < self.DUNGEON_Y:
            # Shallow dungeon floor 1: mixed trolls and goblins
            if random.random() < 0.50:
                from entities.cave_troll import CaveTroll
                e = CaveTroll(
                    position=pos,
                    player=self.player,
                    player_state=self.player_state,
                    hud=self.hud,
                    on_death=lambda enemy: self._on_enemy_death(enemy, 'troll'),
                )
            else:
                from entities.goblin import Goblin
                e = Goblin(
                    position=pos,
                    player=self.player,
                    player_state=self.player_state,
                    hud=self.hud,
                    on_death=lambda enemy: self._on_enemy_death(enemy, 'goblin'),
                )
        elif random.random() < 0.40:
            from entities.goblin import Goblin
            e = Goblin(
                position=pos,
                player=self.player,
                player_state=self.player_state,
                hud=self.hud,
                on_death=lambda enemy: self._on_enemy_death(enemy, 'goblin'),
            )
        else:
            e = Enemy(
                position=pos,
                player=self.player,
                player_state=self.player_state,
                hud=self.hud,
                on_death=lambda enemy: self._on_enemy_death(enemy, 'slime'),
            )

        self._enemies.append(e)
        print(f'[spawn] Enemy at {pos}, total={len(self._enemies)}')

    def register_boss(self, boss):
        self._bosses.append(boss)
        original_on_death = boss.on_death
        def _wrapped(b):
            if b in self._bosses:
                self._bosses.remove(b)
            if original_on_death:
                original_on_death(b)
        boss.on_death = _wrapped

    def _on_enemy_death(self, enemy, enemy_type: str = 'slime'):
        sfx.play('enemy_death')
        if self.loot_manager:
            from systems.loot import roll_loot, roll_gear_drop
            self.loot_manager.spawn_at(enemy.position, roll_loot(enemy_type))
            gear = roll_gear_drop(enemy_type)
            if gear:
                self.loot_manager.give_gear(gear)
        if enemy in self._enemies:
            self._enemies.remove(enemy)
        # Grant XP and update HUD
        xp = self._XP_REWARDS.get(enemy_type, 10)
        if self.player_state and hasattr(self.player_state, 'gain_xp'):
            leveled = self.player_state.gain_xp(xp)
            if self.hud and hasattr(self.hud, 'set_xp'):
                ratio = (self.player_state.xp / self.player_state.xp_to_next
                         if self.player_state.xp_to_next > 0 else 0.0)
                self.hud.set_xp(ratio, self.player_state.level)
                if leveled:
                    sfx.play('levelup')
                    self.hud.set_health(self.player_state.health,
                                        self.player_state.max_health)


class CombatHandler(Entity):
    REACH       = 3.0
    BASE_DAMAGE = 15
    CD          = 0.5

    def __init__(self, player, spawn_manager: SpawnManager, hud=None, sword=None, equipment=None):
        super().__init__()
        self.player        = player
        self.spawn_manager = spawn_manager
        self.hud           = hud
        self.sword         = sword
        self.equipment     = equipment
        self._cd_t         = 0.0
        self._base         = builtins.__dict__.get('base')

    def _dt(self):
        b = self._base
        return b.clock.getDt() if b else 0.016

    def update(self):
        self._cd_t = max(0.0, self._cd_t - self._dt())

    def input(self, key):
        if key == 'f' and self._cd_t <= 0:
            if self.sword:
                self.sword.swing()
            self._melee()
            self._cd_t = self.CD

    def _melee(self):
        px, py, pz = self.player.x, self.player.y, self.player.z
        dmg = self.BASE_DAMAGE + (self.equipment.damage_bonus() if self.equipment else 0)
        all_targets = list(self.spawn_manager._enemies) + list(self.spawn_manager._bosses)
        hit_any = False
        for enemy in all_targets:
            dx = enemy.x - px
            dy = enemy.y - py
            dz = enemy.z - pz
            dist = (dx * dx + dy * dy + dz * dz) ** 0.5
            if dist <= self.REACH:
                epos = Vec3(enemy.x, enemy.y, enemy.z)   # save before possible destroy
                enemy.take_damage(dmg)
                hit_any = True
                try:
                    from ui.particles import show_damage
                    show_damage(epos, dmg)
                except Exception:
                    pass
        # One thwack per swing even if several enemies are struck at once
        if hit_any:
            sfx.play('hit')
