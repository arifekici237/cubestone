from PIL import Image
from ursina import Entity, camera, Texture, color

# Map covers MAP_R blocks in each direction from the player
MAP_R    = 20          # half-size in blocks (40×40 total)
IMG_SIZE = 40          # texture pixels (1 per block — 4× fewer lookups)

# Surface block colors (RGB)
_COLORS = {
    0:  (100, 140, 200),   # air / sky
    1:  ( 69, 153,  36),   # grass
    2:  (115,  72,  20),   # dirt
    3:  (128, 128, 128),   # stone
    4:  (102,  64,  26),   # wood
    5:  (184, 184, 194),   # smooth stone
    6:  (217, 184, 115),   # planks
    7:  ( 89,  71,  46),   # mud
    8:  (242, 209,  25),   # gold
    9:  (212, 195, 110),   # sand
    10: (190, 170,  90),   # sandstone
    11: (230, 240, 255),   # snow
    12: ( 40, 130,  20),   # dark grass
    13: (170, 110,  80),   # iron ore
    14: ( 70,  70,  70),   # coal ore
    15: ( 40, 160,  30),   # leaves
    16: ( 30, 120, 220),   # water
}
_DEFAULT_COLOR = (50, 50, 50)


class Minimap(Entity):
    UPDATE_DIST = 16   # rebuild texture when player moves this many blocks

    def __init__(self, world, player):
        super().__init__(parent=camera.ui)
        self.world    = world
        self.player   = player
        self._last_px = None
        self._last_pz = None

        # Background border
        Entity(parent=self, model='quad',
               color=color.rgba(0.0, 0.0, 0.0, 0.80),
               scale=(0.185, 0.185),
               position=(0.775, 0.395))

        # Map quad — texture updated dynamically
        self._quad = Entity(
            parent=self, model='quad',
            scale=(0.170, 0.170),
            position=(0.775, 0.395, -0.001),
        )

        # Player dot overlay (small yellow square on top)
        Entity(parent=self, model='quad',
               color=color.yellow,
               scale=(0.010, 0.010),
               position=(0.775, 0.395, -0.002))

        self._refresh()

    # ------------------------------------------------------------------
    def _surface_block(self, wx: int, wz: int) -> int:
        # Terrain max ~ base + amplitude. Scan only the terrain band.
        for wy in range(56, 24, -1):
            b = self.world.get_block(wx, wy, wz)
            if b != 0:
                return b
        return 0

    def _refresh(self):
        px = int(self.player.x)
        pz = int(self.player.z)
        self._last_px = px
        self._last_pz = pz

        img  = Image.new('RGBA', (IMG_SIZE, IMG_SIZE))
        step = (MAP_R * 2) / IMG_SIZE   # blocks per pixel

        for ix in range(IMG_SIZE):
            for iz in range(IMG_SIZE):
                wx = px + int((ix - IMG_SIZE // 2) * step)
                wz = pz + int((iz - IMG_SIZE // 2) * step)
                bid = self._surface_block(wx, wz)
                rgb = _COLORS.get(bid, _DEFAULT_COLOR)
                img.putpixel((ix, IMG_SIZE - 1 - iz), rgb + (255,))

        self._quad.texture = Texture(img)

    def update(self):
        px, pz = int(self.player.x), int(self.player.z)
        if (self._last_px is None
                or abs(px - self._last_px) >= self.UPDATE_DIST
                or abs(pz - self._last_pz) >= self.UPDATE_DIST):
            self._refresh()
