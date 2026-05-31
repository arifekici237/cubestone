import builtins
from math import floor
from ursina import Entity, camera, Vec3, color, destroy


class BlockInteraction(Entity):
    """Left-click break, right-click place. Tracks modifications for saving."""

    REACH = 8
    STEP  = 0.05

    def __init__(self, world, renderer_map: dict, player, chunk_size: int,
                 hud=None, hotbar=None, crafting_ui=None, inventory_ui=None,
                 shop_ui=None, character_ui=None, save_manager=None,
                 initial_mods: dict = None, block_counts: dict = None,
                 item_counts: dict = None, equipment=None, player_state=None):
        super().__init__()
        self.world = world
        self.renderer_map = renderer_map
        self.player = player
        self.chunk_size = chunk_size
        self.hud          = hud
        self.hotbar       = hotbar
        self.crafting_ui  = crafting_ui
        self.inventory_ui = inventory_ui
        self.shop_ui      = shop_ui
        self.character_ui = character_ui
        self.save_manager = save_manager
        self.item_counts  = item_counts if item_counts is not None else {}
        self.equipment    = equipment
        self.player_state = player_state
        self.selected_block = 1
        self.block_counts: dict = block_counts if block_counts is not None else {}
        self.modifications: dict = dict(initial_mods) if initial_mods else {}

        # Block hover highlight — wireframe cube drawn around targeted block
        self._highlight = Entity(
            model='cube',
            color=color.rgba(1.0, 1.0, 0.31, 1.0),   # bright yellow wireframe
            scale=1.015,
            enabled=False,
        )
        try:
            self._highlight.setRenderModeWireframe(True)
            self._highlight.setRenderModeThickness(2)
        except Exception:
            pass   # fallback: just a faint cube if wireframe API unavailable

        # Torch point lights: (wx,wy,wz) → light NodePath
        self._torch_lights: dict = {}
        # Restore lights for torches that were saved and re-applied
        if initial_mods:
            for (wx, wy, wz), bid in initial_mods.items():
                if bid == 17:
                    self._spawn_torch_light(wx, wy, wz)

    # ------------------------------------------------------------------
    def update(self):
        # Hide highlight whenever any UI panel is open
        if any(getattr(ui, 'is_open', False)
               for ui in (self.crafting_ui, self.inventory_ui,
                          self.shop_ui, self.character_ui) if ui):
            self._highlight.enabled = False
            return
        hit, _ = self._cast()
        if hit:
            bx, by, bz = hit
            self._highlight.position = Vec3(bx + 0.5, by + 0.5, bz + 0.5)
            self._highlight.enabled = True
        else:
            self._highlight.enabled = False

    # ------------------------------------------------------------------
    def input(self, key):
        if self.crafting_ui and self.crafting_ui.is_open:
            return
        if self.inventory_ui and self.inventory_ui.is_open:
            return
        if self.shop_ui and self.shop_ui.is_open:
            return
        if self.character_ui and self.character_ui.is_open:
            return
        if key == 'left mouse down':
            self._break()
        elif key == 'right mouse down':
            self._place()
        elif key in ('1', '2', '3', '4', '5', '6', '7', '8', '9'):
            from ui.hotbar import SLOTS
            idx = int(key) - 1
            if 0 <= idx < len(SLOTS):
                self.selected_block = SLOTS[idx]
                if self.hotbar:
                    self.hotbar.select(self.selected_block)
        elif key == 'f5':
            self._save()

    # ------------------------------------------------------------------
    def _cast(self):
        origin = Vec3(camera.world_position)
        direction = Vec3(camera.forward).normalized()
        prev = None
        t = self.STEP
        while t <= self.REACH:
            p = origin + direction * t
            bx, by, bz = floor(p.x), floor(p.y), floor(p.z)
            if self.world.get_block(bx, by, bz) != 0:
                return (bx, by, bz), prev
            prev = (bx, by, bz)
            t += self.STEP
        return None, None

    def _break(self):
        hit, _ = self._cast()
        if hit is None:
            return
        bx, by, bz = hit
        broken_id = self.world.get_block(bx, by, bz)
        self.world.set_block(bx, by, bz, 0)
        self.modifications[(bx, by, bz)] = 0
        if broken_id:
            self.block_counts[broken_id] = self.block_counts.get(broken_id, 0) + 1
            if broken_id == 17:
                self._remove_torch_light(bx, by, bz)
            try:
                from ui.particles import block_break_burst
                block_break_burst(bx, by, bz, broken_id)
            except Exception:
                pass
            from ui import sfx
            sfx.play('block_break')
        self._rebuild(bx, by, bz)

    def _place(self):
        _, prev = self._cast()
        if prev is None:
            return
        bx, by, bz = prev
        bid = self.selected_block
        if self.world.get_block(bx, by, bz) == 0:
            if self.block_counts.get(bid, 0) <= 0:
                return
            self.world.set_block(bx, by, bz, bid)
            self.modifications[(bx, by, bz)] = bid
            self.block_counts[bid] -= 1
            if bid == 17:
                self._spawn_torch_light(bx, by, bz)
            if self.hotbar:
                self.hotbar.update_count(bid)
            from ui import sfx
            sfx.play('block_place')
            self._rebuild(bx, by, bz)

    def _rebuild(self, bx: int, by: int, bz: int):
        s = self.chunk_size
        cx, lx = divmod(bx, s)
        cy, ly = divmod(by, s)
        cz, lz = divmod(bz, s)

        to_rebuild = {(cx, cy, cz)}
        if lx == 0:     to_rebuild.add((cx - 1, cy, cz))
        if lx == s - 1: to_rebuild.add((cx + 1, cy, cz))
        if ly == 0:     to_rebuild.add((cx, cy - 1, cz))
        if ly == s - 1: to_rebuild.add((cx, cy + 1, cz))
        if lz == 0:     to_rebuild.add((cx, cy, cz - 1))
        if lz == s - 1: to_rebuild.add((cx, cy, cz + 1))

        for key in to_rebuild:
            renderer = self.renderer_map.get(key)
            if renderer:
                renderer.rebuild()
                renderer.collider = 'mesh'

    def _spawn_torch_light(self, wx: int, wy: int, wz: int):
        """Bright PointLight + small flame sphere at torch position."""
        try:
            from panda3d.core import PointLight as PL
            from ursina import Entity, Vec3
            base = builtins.__dict__.get('base')
            if not base:
                return
            # Panda3D PointLight (bright warm orange)
            p = PL(f'tl_{wx}_{wy}_{wz}')
            p.setColor((4.5, 3.0, 1.0, 1.0))    # high-intensity warm light
            p.setAttenuation((1.0, 0.04, 0.008)) # reaches ~10 blocks
            # Ursina Y-up → Panda3D Z-up: (ux, uy, uz) → setPos(ux, uz, uy)
            light_np = base.render.attachNewNode(p)
            light_np.setPos(wx + 0.5, wz + 0.5, wy + 0.5)
            base.render.setLight(light_np)
            # Visual flame sphere (small glowing ball above the block)
            flame = Entity(
                model='sphere',
                color=color.rgba(1.0, 0.80, 0.18, 1.0),
                scale=0.14,
                position=Vec3(wx + 0.5, wy + 0.82, wz + 0.5),
            )
            self._torch_lights[(wx, wy, wz)] = (light_np, flame)
        except Exception as e:
            print(f'[torch] {e}')

    def _remove_torch_light(self, wx: int, wy: int, wz: int):
        entry = self._torch_lights.pop((wx, wy, wz), None)
        if not entry:
            return
        try:
            light_np, flame = entry
            base = builtins.__dict__.get('base')
            if base:
                base.render.clearLight(light_np)
            light_np.removeNode()
            destroy(flame)
        except Exception:
            pass

    def _save(self):
        if not self.save_manager:
            return
        cls_name = ''
        if self.player_state and getattr(self.player_state, 'player_class', None):
            cls_name = self.player_state.player_class.name
        if self.equipment:
            self.save_manager.save_all(
                self.modifications, self.item_counts,
                self.equipment, cls_name
            )
        else:
            self.save_manager.save(self.modifications)
