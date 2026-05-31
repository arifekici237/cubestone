import sys
import json
import math
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ursina import Ursina, camera, window, Vec3, color, Entity, destroy, time, held_keys, Text
from ursina.lights import DirectionalLight, AmbientLight
from ursina.prefabs.first_person_controller import FirstPersonController

from core.world import World
from core.generation import TerrainGenerator
from core.dungeon import DungeonGenerator
from core.structures import StructureGenerator
from render.chunk_renderer import ChunkRenderer
from systems.block_interaction import BlockInteraction
from systems.day_night import DayNightCycle
from systems.spawn_manager import SpawnManager, CombatHandler
from systems.loot_manager import LootManager
from systems.crafting import CraftingSystem
from systems.healing import HealingSystem
from systems.ability_system import AbilitySystem
from systems.player_class import CLASSES
from ui.hud import HUD
from ui.hotbar import Hotbar
from ui.crafting_ui import CraftingUI
from ui.inventory_ui import InventoryUI
from ui.shop_ui import ShopUI
from ui.minimap import Minimap
from ui.sword_viewmodel import SwordViewModel
from ui.character_ui import CharacterUI
from ui.class_select_ui import ClassSelectUI
from ui import sfx
from entities.merchant import Merchant
from entities.dungeon_chest import DungeonChest
from entities.boss import Boss
from entities.boss_portal import BossPortal
from systems.shop import ShopSystem
from systems.equipment import EquipmentSystem
from systems.gear import make_gear
from persistence.save_manager import SaveManager
from entities.player import PlayerState


def load_settings() -> dict:
    path = Path(__file__).parent.parent / 'config' / 'settings' / 'game_settings.json'
    with open(path) as f:
        return json.load(f)


def main() -> None:
    settings = load_settings()

    app = Ursina()
    window.title = 'Cubestone'
    window.color = color.rgb(85, 155, 225)   # brighter sky blue

    # ── Ses: SFX önbelleğini yükle + döngülü fon müziği başlat ─────────
    sfx.init()
    sfx.start_music()

    sun     = DirectionalLight()
    sun.look_at(Vec3(1, -2, 1))
    ambient = AmbientLight(color=color.rgba(100, 100, 100, 255))

    # ── Zindan + Terrain + Yapılar ────────────────────────────────────
    dungeon    = DungeonGenerator(seed=settings['seed'])
    struct_gen = StructureGenerator(seed=settings['seed'])
    chunk_size = settings['chunk_size']
    world      = World(chunk_size=chunk_size)
    generator  = TerrainGenerator(
        seed=settings['seed'],
        base_height=settings['base_terrain_height'],
        amplitude=settings['terrain_amplitude'],
        dungeon=dungeon,
    )
    player_state = PlayerState()

    # ── Kayıt ─────────────────────────────────────────────────────────
    save_manager = SaveManager()
    saved        = save_manager.load_all()
    saved_mods   = {}
    if saved:
        # Parse block modifications from new or old format
        raw_blocks = saved.get('blocks', saved)
        saved_mods = {
            tuple(int(x) for x in k.split(',')): v
            for k, v in raw_blocks.items()
            if ',' in k
        }
        if saved_mods:
            print(f'Loaded {len(saved_mods)} saved block changes.')

    # ── Chunk oluştur (generate only, no rendering yet) ────────────────
    rd = settings['render_distance']
    COLL_R = 1  # only player's own chunk gets mesh colliders (block interaction)
    for cx in range(-rd, rd):
        for cz in range(-rd, rd):
            for cy in range(0, 6):
                chunk = world.get_or_create_chunk(cx, cy, cz)
                generator.generate_chunk(chunk)

    # ── Yapıları yerleştir (bloklara yaz) ──────────────────────────────
    structure_data = struct_gen.place_all(world, generator, rd)

    # Test arenaları — spawn yakınında bir Gök Kalesi + bir Dungeon Vault
    # (uzaktaki rastgele arenalar yürümeden bulunamadığı için)
    structure_data.append(
        struct_gen.place_test_arena(world, generator, 25, 0, 'sky_citadel'))
    structure_data.append(
        struct_gen.place_test_arena(world, generator, 0, 28, 'dungeon_vault'))

    # ── Kayıtlı blok değişikliklerini uygula ───────────────────────────
    if saved_mods:
        for (wx, wy, wz), bid in saved_mods.items():
            world.set_block(wx, wy, wz, bid)

    # ── Şimdi renderer'ları oluştur (mesh collider yok, boş chunk'lar skip) ─
    renderer_map = {}
    for cx in range(-rd, rd):
        for cz in range(-rd, rd):
            for cy in range(0, 6):
                chunk = world.get_or_create_chunk(cx, cy, cz)
                if chunk.is_empty():
                    continue
                renderer_map[(cx, cy, cz)] = ChunkRenderer(
                    chunk, neighbor_getter=world.get_block, with_collider=False
                )

    # ── Oyuncu ────────────────────────────────────────────────────────
    # Spawn directly on terrain surface, not high above (no long fall on start)
    spawn_surface = generator.get_surface_height(0, 0)
    spawn_y       = float(spawn_surface + 2)
    player  = FirstPersonController(
        position=Vec3(0, spawn_y, 0),
        speed=0, jump_height=6,            # speed=0: FPC movement disabled
        mouse_sensitivity=Vec3(40, 40, 0),
    )
    camera.fov = 100
    # FPC raycasts walk the entire scene tree each frame; redirect them to
    # an empty target so they return instantly instead of visiting all chunks.
    player.traverse_target = Entity(add_to_scene_entities=False)
    player._ability_speed_mult = 1.0   # modified by AbilitySystem ranger dash
    player._kb_vel             = (0.0, 0.0)   # knockback impulse (x, z)

    # ── Envanter ──────────────────────────────────────────────────────
    block_counts = {i: 0 for i in range(1, 18)}   # 1-17 (17=torch)
    item_counts  = {}

    # Başlangıç stoku
    block_counts[2]  = 20   # dirt
    block_counts[3]  = 20   # stone
    block_counts[4]  = 15   # wood
    block_counts[1]  = 10   # grass
    block_counts[17] = 8    # torch (meşale)

    # ── HUD + Hotbar ──────────────────────────────────────────────────
    hud    = HUD()
    hud.set_health(player_state.health, player_state.max_health)
    hotbar = Hotbar(block_counts=block_counts)
    hotbar.select(1)

    # ── Ekipman sistemi ───────────────────────────────────────────────
    sword = SwordViewModel()
    equipment = EquipmentSystem(
        player=player,
        player_state=player_state,
        sword=sword,
        on_change=lambda: hud.update_equipment(equipment),
    )

    # ── Kayıtlı oyuncu verilerini geri yükle ─────────────────────────
    if saved.get('version') == 2:
        # Item counts (consumables)
        for k, v in saved.get('item_counts', {}).items():
            item_counts[k] = v
        # Gear
        gear_bag_data = saved.get('gear_bag', [])
        equipped_data = saved.get('equipped', {})
        if gear_bag_data or equipped_data:
            equipment.restore_gear(gear_bag_data, equipped_data)
        # Player class
        cls_name = saved.get('player_class', '')
        if cls_name and cls_name in CLASSES:
            cls = CLASSES[cls_name]
            player_state.apply_class(cls)
            equipment.set_class_stats(cls.base_atk, cls.base_spd)
            hud.set_class_label(cls.label, cls.color)
            hud.set_health(player_state.health, player_state.max_health)
        hud.update_items(item_counts)
        hud.update_equipment(equipment)

    # ── Crafting ──────────────────────────────────────────────────────
    crafting    = CraftingSystem(block_counts=block_counts, item_counts=item_counts,
                                 equipment=equipment)
    crafting_ui = CraftingUI(crafting=crafting, hotbar=hotbar, hud=hud)

    # ── Envanter ekranı ───────────────────────────────────────────────
    inventory_ui = InventoryUI(block_counts=block_counts, item_counts=item_counts,
                               equipment=equipment)

    # ── Tüccar + Mağaza ───────────────────────────────────────────────
    merchant_y  = generator.get_surface_height(8, 0) + 1
    merchant    = Merchant(position=Vec3(8, merchant_y, 0))
    shop_system = ShopSystem(block_counts=block_counts, item_counts=item_counts,
                             equipment=equipment)
    shop_ui = ShopUI(player=player, merchant=merchant, shop=shop_system)

    # ── Karakter ekranı ───────────────────────────────────────────────
    character_ui = CharacterUI(equipment=equipment, player_state=player_state,
                               item_counts=item_counts)

    # ── Minimap ───────────────────────────────────────────────────────
    Minimap(world=world, player=player)

    # ── Loot manager ─────────────────────────────────────────────────
    loot_manager = LootManager(
        player=player,
        item_counts=item_counts,
        equipment=equipment,
        on_collect=lambda item_id, count: hud.update_items(item_counts),
    )

    # ── Düşman spawn ──────────────────────────────────────────────────
    spawn_manager = SpawnManager(
        player=player,
        player_state=player_state,
        hud=hud,
        loot_manager=loot_manager,
    )
    CombatHandler(player=player, spawn_manager=spawn_manager, hud=hud, sword=sword,
                  equipment=equipment)

    # ── Yetenek sistemi ───────────────────────────────────────────────
    ability_system = AbilitySystem(
        player=player,
        player_state=player_state,
        spawn_manager=spawn_manager,
        equipment=equipment,
        hud=hud,
    )

    # ── İyileştirme ───────────────────────────────────────────────────
    HealingSystem(player_state=player_state, item_counts=item_counts, hud=hud)

    # ── Blok etkileşimi ───────────────────────────────────────────────
    BlockInteraction(
        world=world,
        renderer_map=renderer_map,
        player=player,
        chunk_size=chunk_size,
        hud=hud,
        hotbar=hotbar,
        crafting_ui=crafting_ui,
        inventory_ui=inventory_ui,
        shop_ui=shop_ui,
        character_ui=character_ui,
        save_manager=save_manager,
        initial_mods=saved_mods,
        block_counts=block_counts,
        item_counts=item_counts,
        equipment=equipment,
        player_state=player_state,
    )

    # ── Gece/gündüz döngüsü ───────────────────────────────────────────
    DayNightCycle(sun=sun, ambient=ambient, cycle_seconds=120.0)

    # ── Zindan sandıkları ─────────────────────────────────────────────
    for cx_pos, cy_pos, cz_pos, floor_idx in dungeon.get_chest_rooms():
        DungeonChest(
            position=Vec3(cx_pos, cy_pos, cz_pos),
            player=player,
            item_counts=item_counts,
            equipment=equipment,
            floor=floor_idx,
            on_collect=lambda: hud.update_items(item_counts),
        )

    # ── Yapı sandıkları ───────────────────────────────────────────────
    for sinfo in structure_data:
        DungeonChest(
            position=Vec3(sinfo['chest_wx'], sinfo['chest_wy'], sinfo['chest_wz']),
            player=player,
            item_counts=item_counts,
            equipment=equipment,
            floor=sinfo['floor'],
            on_collect=lambda: hud.update_items(item_counts),
        )

    # ── Yapı bossları ────────────────────────────────────────────────
    for sinfo in structure_data:
        if sinfo['boss']:
            boss = Boss(
                position=Vec3(sinfo['boss_wx'], sinfo['boss_wy'], sinfo['boss_wz']),
                player=player,
                player_state=player_state,
                hud=hud,
                equipment=equipment,
                floor=sinfo['floor'],
                structure_type=sinfo['type'],
            )
            spawn_manager.register_boss(boss)

    # ── Işınlanma portalları (arena yapıları) ─────────────────────────
    def _arena_light(world_pos):
        """Bright warm point light to illuminate a boss arena room."""
        try:
            from panda3d.core import PointLight as PL
            base = builtins.__dict__.get('base')
            if not base:
                return
            wx, wy, wz = world_pos
            p = PL(f'arena_{int(wx)}_{int(wy)}_{int(wz)}')
            p.setColor((3.0, 2.6, 2.0, 1.0))
            p.setAttenuation((1.0, 0.025, 0.0))   # wide reach
            np = base.render.attachNewNode(p)
            np.setPos(wx + 0.5, wz + 0.5, wy + 2.5)   # Ursina Y-up → Panda Z-up
            base.render.setLight(np)
        except Exception:
            pass

    def spawn_portals(sinfo):
        if 'portal_a' not in sinfo:
            return
        sky = sinfo['type'] == 'sky_citadel'
        rgb = (0.45, 0.75, 1.0) if sky else (0.85, 0.35, 1.0)
        # Entry pad → arena
        p_in = BossPortal(
            position=Vec3(*sinfo['portal_a']),
            target=Vec3(*sinfo['portal_a_to']),
            player=player, label='Arenaya Isinlan', rgb=rgb,
        )
        # Arena → entry pad (return)
        p_out = BossPortal(
            position=Vec3(*sinfo['portal_b']),
            target=Vec3(*sinfo['portal_b_to']),
            player=player, label='Geri Don', rgb=rgb,
        )
        # Pair them so arriving on one doesn't bounce straight back
        p_in.sibling  = p_out
        p_out.sibling = p_in
        # Light up the arena room
        _arena_light(sinfo['portal_a_to'])

    import builtins
    for sinfo in structure_data:
        spawn_portals(sinfo)

    # ── Respawn ───────────────────────────────────────────────────────
    spawn_pos = Vec3(0, spawn_y, 0)

    class RespawnSystem(Entity):
        def update(self_):
            if player.y < -10:
                player.position = spawn_pos
                if hasattr(player, 'velocity'):
                    player.velocity = Vec3(0, 0, 0)

    RespawnSystem()

    def _solid(x, y, z):
        return world.get_block(int(x), int(y), int(z)) != 0

    class MovementSystem(Entity):
        """Horizontal movement with world.get_block() wall collision (replaces FPC speed)."""
        SPEED        = 15.0
        WATER_MULT   = 0.45   # speed multiplier when in water
        SPRINT_MULT  = 1.80   # Left Shift sprint multiplier
        SPRINT_FOV   = 108.0
        NORMAL_FOV   = 100.0

        def _body_blocks(self_, x, z, y_feet):
            px = math.floor(x); pz = math.floor(z)
            for py in (y_feet, y_feet + 1):
                if _solid(px, py, pz):
                    return True
            return False

        def update(self_):
            fwd   = held_keys['w'] - held_keys['s']
            right = held_keys['d'] - held_keys['a']
            moving = fwd != 0 or right != 0
            y_feet   = math.floor(player.y)
            in_water = world.get_block(math.floor(player.x), y_feet, math.floor(player.z)) == 16

            # Sprint — only on ground, not in water
            is_sprinting = (held_keys['left shift'] and moving and not in_water)
            sprint_mult  = self_.SPRINT_MULT if is_sprinting else 1.0

            # FOV: smoothly lerp toward sprint/normal target
            target_fov = self_.SPRINT_FOV if is_sprinting else self_.NORMAL_FOV
            camera.fov += (target_fov - camera.fov) * min(1.0, time.dt * 8)

            # Knockback impulse (apply even when not pressing WASD)
            kbx, kbz = getattr(player, '_kb_vel', (0.0, 0.0))
            if abs(kbx) > 0.05 or abs(kbz) > 0.05:
                nb_x = player.x + kbx * time.dt
                if not self_._body_blocks(nb_x, player.z, y_feet):
                    player.x = nb_x
                nb_z = player.z + kbz * time.dt
                if not self_._body_blocks(player.x, nb_z, y_feet):
                    player.z = nb_z
                decay = max(0.0, 1.0 - 11.0 * time.dt)
                player._kb_vel = (kbx * decay, kbz * decay)

            if not moving:
                return
            direction = (player.forward * fwd + player.right * right).normalized()
            wx, wz    = direction.x, direction.z

            water_mult = self_.WATER_MULT if in_water else 1.0
            dash_mult  = getattr(player, '_ability_speed_mult', 1.0)
            speed_mult = max(sprint_mult, dash_mult)
            step       = self_.SPEED * water_mult * speed_mult * time.dt

            new_x = player.x + wx * step
            if not self_._body_blocks(new_x, player.z, y_feet):
                player.x = new_x

            new_z = player.z + wz * step
            if not self_._body_blocks(player.x, new_z, y_feet):
                player.z = new_z

    MovementSystem()

    class TerrainPhysics(Entity):
        """Path-scan vertical physics — checks every block in the fall path."""
        _G         = 28.0
        _JUMP      = 10.0
        _VMAX      = 30.0
        _FOOT      = 0.35   # foot radius for multi-column ground check
        _FALL_THR  = 14.0   # vy at landing that triggers fall damage
        _SWIM_UP   = 5.0    # upward velocity when swimming (space in water)
        _WATER_G   = 4.0    # gravity while submerged (buoyancy)
        _WATER_VMAX = 3.0   # max sinking speed in water

        def __init__(self_):
            super().__init__()
            self_.vy         = 0.0
            self_.grounded   = False
            self_.jumps_left = 2      # double jump counter
            player.gravity   = 0
            player.jump      = self_._jump

        def _jump(self_):
            if self_.grounded:
                self_.vy         = self_._JUMP
                self_.grounded   = False
                self_.jumps_left = 1          # first jump used; one more available
                sfx.play('jump')
            elif self_._in_water():
                self_.vy = self_._SWIM_UP
            elif self_.jumps_left > 0:
                self_.vy         = self_._JUMP * 0.82   # slightly weaker second jump
                self_.jumps_left = 0
                sfx.play('jump', pitch=1.15)   # higher pitch for the second jump

        def _in_water(self_):
            px, pz = math.floor(player.x), math.floor(player.z)
            foot   = math.floor(player.y)
            return world.get_block(px, foot, pz) == 16

        def _foot_cols(self_):
            x, z = player.x, player.z
            r = self_._FOOT
            seen, cols = set(), []
            for fx, fz in ((x, z), (x+r, z), (x-r, z), (x, z+r), (x, z-r)):
                c = (math.floor(fx), math.floor(fz))
                if c not in seen:
                    seen.add(c)
                    cols.append(c)
            return cols

        def update(self_):
            px = math.floor(player.x)
            pz = math.floor(player.z)

            cx_p = px // chunk_size
            cz_p = pz // chunk_size
            if (cx_p, cz_p) not in _gen_cols:
                self_.vy = 0.0
                return

            # ── Water physics ──────────────────────────────────────────
            if self_._in_water():
                self_.grounded = False
                self_.vy = max(self_.vy - self_._WATER_G * time.dt,
                               -self_._WATER_VMAX)
                player.y += self_.vy * time.dt
                return

            # ── Normal physics ─────────────────────────────────────────
            foot = math.floor(player.y)
            if _solid(px, foot, pz):
                if not _solid(px, foot + 1, pz):
                    player.y         = float(foot + 1)
                    self_.vy         = 0.0
                    self_.grounded   = True
                    self_.jumps_left = 2
                    return
                top = foot
                while top < foot + 2 and _solid(px, top + 1, pz):
                    top += 1
                player.y         = float(top + 1)
                self_.vy         = 0.0
                self_.grounded   = True
                self_.jumps_left = 2
                return

            self_.vy = max(self_.vy - self_._G * time.dt, -self_._VMAX)
            new_y   = player.y + self_.vy * time.dt

            if self_.vy < 0:
                start_y = math.floor(player.y) - 1
                end_y   = math.floor(new_y) - 2
                best_land = None
                for fpx, fpz in self_._foot_cols():
                    for y in range(start_y, end_y, -1):
                        if _solid(fpx, y, fpz):
                            land_y = float(y + 1)
                            if best_land is None or land_y > best_land:
                                best_land = land_y
                            break
                if best_land is not None:
                    # Fall damage: hitting water absorbs all fall damage
                    fall_bid = world.get_block(px, math.floor(best_land) - 1, pz)
                    if fall_bid != 16:
                        fall_speed = -self_.vy
                        if fall_speed > self_._FALL_THR:
                            dmg = int((fall_speed - self_._FALL_THR) * 3)
                            player_state.take_damage(dmg)
                            hud.set_health(player_state.health,
                                           player_state.max_health)
                    player.y         = best_land
                    self_.vy         = 0.0
                    self_.grounded   = True
                    self_.jumps_left = 2
                else:
                    player.y       = new_y
                    self_.grounded = False
            else:
                start_y = math.floor(player.y + 1.7)
                end_y   = math.floor(new_y + 1.7) + 1
                for y in range(start_y, end_y):
                    if _solid(px, y, pz):
                        player.y = float(y) - 1.71
                        self_.vy = 0.0
                        return
                player.y       = new_y
                self_.grounded = False

    TerrainPhysics()

    # ── Sınıf seçim ekranı (yeni oyun veya kayıtsız) ──────────────────
    if not saved.get('player_class'):
        def _on_class_select(cls_name: str):
            cls = CLASSES.get(cls_name, CLASSES['knight'])
            player_state.apply_class(cls)
            equipment.set_class_stats(cls.base_atk, cls.base_spd)
            hud.set_class_label(cls.label, cls.color)
            hud.set_health(player_state.health, player_state.max_health)

        ClassSelectUI(on_select=_on_class_select)
    else:
        # Class already loaded from save — show ability hint
        cls = CLASSES.get(saved.get('player_class', 'knight'), CLASSES['knight'])
        if cls:
            hud.update_ability(cls.ability_name, 0.0)

    # ── Chunk streaming — world expands as player walks ──────────────
    _gen_cols = {(dcx, dcz) for dcx in range(-rd, rd) for dcz in range(-rd, rd)}

    class ChunkStreamer(Entity):
        """Queue-based streamer — at most GEN_PER_FRAME columns generated per frame, no big freezes."""
        GEN_PER_FRAME = 1

        def __init__(self_):
            super().__init__()
            self_._cx = 0
            self_._cz = 0
            self_._gen_queue    = []   # cols needing generation
            self_._render_queue = []   # cols needing render/rebuild
            self_._target       = set(_gen_cols)

        def _on_chunk_change(self_, cx, cz):
            target = {(cx + dx, cz + dz)
                      for dx in range(-rd, rd)
                      for dz in range(-rd, rd)}
            self_._target = target

            for key in list(renderer_map.keys()):
                if (key[0], key[2]) not in target:
                    destroy(renderer_map.pop(key))

            for col in target - _gen_cols:
                if col not in self_._gen_queue:
                    self_._gen_queue.append(col)

            for col in target & _gen_cols:
                ncx, ncz = col
                for ncy in range(0, 6):
                    rkey = (ncx, ncy, ncz)
                    if rkey in renderer_map:
                        continue
                    chunk = world.get_chunk(ncx, ncy, ncz)
                    if chunk and not chunk.is_empty():
                        if col not in self_._render_queue:
                            self_._render_queue.append(col)
                        break

            new_structs = struct_gen.place_around(
                world, generator, cx, cz, chunk_size, rd)

            for sinfo in new_structs:
                DungeonChest(
                    position=Vec3(sinfo['chest_wx'], sinfo['chest_wy'], sinfo['chest_wz']),
                    player=player, item_counts=item_counts, equipment=equipment,
                    floor=sinfo['floor'],
                    on_collect=lambda: hud.update_items(item_counts),
                )
                if sinfo['boss']:
                    b = Boss(
                        position=Vec3(sinfo['boss_wx'], sinfo['boss_wy'], sinfo['boss_wz']),
                        player=player, player_state=player_state, hud=hud,
                        equipment=equipment, floor=sinfo['floor'],
                        structure_type=sinfo['type'],
                    )
                    spawn_manager.register_boss(b)
                spawn_portals(sinfo)

            for s in new_structs:
                scx = s['wx'] // chunk_size
                scz = s['wz'] // chunk_size
                for ddx in (-1, 0, 1):
                    for ddz in (-1, 0, 1):
                        col = (scx + ddx, scz + ddz)
                        if col in target and col not in self_._render_queue:
                            self_._render_queue.append(col)

        def _render_col(self_, ncx, ncz):
            for ncy in range(0, 6):
                rkey = (ncx, ncy, ncz)
                chunk = world.get_chunk(ncx, ncy, ncz)
                if chunk is None or chunk.is_empty():
                    continue
                if rkey in renderer_map:
                    renderer_map[rkey].rebuild()
                else:
                    renderer_map[rkey] = ChunkRenderer(
                        chunk, neighbor_getter=world.get_block,
                        with_collider=False)

        def update(self_):
            cx = int(player.x) // chunk_size
            cz = int(player.z) // chunk_size
            if cx != self_._cx or cz != self_._cz:
                self_._cx = cx
                self_._cz = cz
                self_._on_chunk_change(cx, cz)

            budget = self_.GEN_PER_FRAME
            while budget > 0 and self_._gen_queue:
                ncx, ncz = self_._gen_queue.pop(0)
                if (ncx, ncz) not in self_._target:
                    continue
                for ncy in range(0, 6):
                    chunk = world.get_or_create_chunk(ncx, ncy, ncz)
                    generator.generate_chunk(chunk)
                _gen_cols.add((ncx, ncz))
                self_._render_col(ncx, ncz)
                budget -= 1

            while budget > 0 and self_._render_queue:
                ncx, ncz = self_._render_queue.pop(0)
                if (ncx, ncz) not in self_._target:
                    continue
                self_._render_col(ncx, ncz)
                budget -= 1

    ChunkStreamer()

    # ── Savaş geri bildirimi: hasar flash, HP regen, knockback ───────────
    class CombatFeedback(Entity):
        """Screen flash, HP regen, knockback, death + respawn."""
        REGEN_DELAY  = 6.0
        REGEN_RATE   = 1.5
        KB_FORCE     = 9.0
        RESPAWN_WAIT = 2.5   # seconds before respawn after death

        def __init__(self_):
            super().__init__(parent=camera.ui)
            self_._flash_overlay = Entity(
                parent=camera.ui, model='quad',
                color=color.rgba(1.0, 0.0, 0.0, 0.0),
                scale=(4, 3), z=-0.05,
            )
            # Black screen for death
            self_._death_overlay = Entity(
                parent=camera.ui, model='quad',
                color=color.rgba(0.0, 0.0, 0.0, 0.0),
                scale=(4, 3), z=-0.06,
            )
            self_._death_text = Text(
                parent=camera.ui, text='',
                origin=(0, 0), position=(0, 0.08),
                scale=2.4, color=color.rgba(0.9, 0.15, 0.15, 0.0),
            )
            self_._last_hp   = player_state.health
            self_._no_dmg_t  = 0.0
            self_._regen_acc = 0.0
            self_._flash_t   = 0.0
            self_._dead      = False
            self_._dead_t    = 0.0

        def update(self_):
            dt = time.dt

            # ── Ölüm / respawn ────────────────────────────────────────
            if self_._dead:
                self_._dead_t -= dt
                fade = max(0.0, self_._dead_t / self_.RESPAWN_WAIT)
                self_._death_overlay.color = color.rgba(0.0, 0.0, 0.0,
                                                        0.88 * fade + 0.12)
                if self_._dead_t <= 0:
                    # Respawn
                    self_._dead = False
                    player.position = spawn_pos
                    player._kb_vel  = (0.0, 0.0)
                    player_state.health = player_state.max_health
                    hud.set_health(player_state.health, player_state.max_health)
                    self_._last_hp = player_state.health
                    self_._no_dmg_t = 0.0
                    self_._death_overlay.color = color.rgba(0.0, 0.0, 0.0, 0.0)
                    self_._death_text.color    = color.rgba(0.9, 0.15, 0.15, 0.0)
                    self_._death_text.text     = ''
                return

            hp = player_state.health

            # ── Ölüm tespiti ─────────────────────────────────────────
            if hp <= 0 and self_._last_hp > 0:
                self_._dead   = True
                self_._dead_t = self_.RESPAWN_WAIT
                self_._death_overlay.color = color.rgba(0.0, 0.0, 0.0, 0.88)
                self_._death_text.text  = 'ÖLDÜN\nYeniden Doğuyorsun...'
                self_._death_text.color = color.rgba(0.9, 0.15, 0.15, 1.0)
                self_._last_hp = 0
                sfx.play('death')
                return

            if hp < self_._last_hp and hp > 0:
                # ── Hasar alındı ─────────────────────────────────────
                self_._flash_t  = 0.38
                sfx.play('hurt')
                self_._no_dmg_t = 0.0
                self_._regen_acc = 0.0
                all_ents = list(spawn_manager._enemies) + list(spawn_manager._bosses)
                best_d, kb = 99.0, None
                for e in all_ents:
                    dx = player.x - e.x
                    dz = player.z - e.z
                    d  = (dx * dx + dz * dz) ** 0.5
                    if d < best_d:
                        best_d = d
                        if d > 0:
                            kb = (dx / d * self_.KB_FORCE, dz / d * self_.KB_FORCE)
                if kb:
                    player._kb_vel = kb

            self_._last_hp = hp

            # ── Ekran kızarma ─────────────────────────────────────────
            if self_._flash_t > 0:
                self_._flash_t -= dt
                alpha = max(0.0, 0.50 * (self_._flash_t / 0.38))
                self_._flash_overlay.color = color.rgba(1.0, 0.0, 0.0, alpha)

            # ── Pasif can yenilenmesi ─────────────────────────────────
            if hp > 0:
                self_._no_dmg_t += dt
            if (hp < player_state.max_health and hp > 0
                    and self_._no_dmg_t >= self_.REGEN_DELAY):
                self_._regen_acc += self_.REGEN_RATE * dt
                if self_._regen_acc >= 1.0:
                    healed = int(self_._regen_acc)
                    self_._regen_acc -= healed
                    player_state.heal(healed)
                    hud.set_health(player_state.health, player_state.max_health)

    CombatFeedback()

    app.run()


if __name__ == '__main__':
    main()
