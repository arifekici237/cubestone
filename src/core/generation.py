from opensimplex import OpenSimplex
from .chunk import ChunkData


class TerrainGenerator:
    """Procedural terrain generation. Pure logic, no rendering."""

    def __init__(self, seed: int = 0, scale: float = 0.04,
                 base_height: int = 32, amplitude: int = 16,
                 dungeon=None):
        self.seed        = seed
        self.scale       = scale
        self.base_height = base_height
        self.amplitude   = amplitude
        self.dungeon     = dungeon            # optional DungeonGenerator
        self._noise      = OpenSimplex(seed)
        self._cave       = OpenSimplex(seed + 1337)
        self._cave2      = OpenSimplex(seed + 7331)
        self._biome      = OpenSimplex(seed + 9999)

    def get_surface_height(self, wx: int, wz: int) -> int:
        n = self._biome.noise2(wx * 0.011, wz * 0.011)
        nx = wx * self.scale
        nz = wz * self.scale
        noise_val = (
            self._noise.noise2(nx,      nz)      * 1.00
            + self._noise.noise2(nx * 2, nz * 2) * 0.50
            + self._noise.noise2(nx * 4, nz * 4) * 0.25
        ) / 1.75

        def _sstep(x, lo, hi):
            t = max(0.0, min(1.0, (x - lo) / (hi - lo)))
            return t * t * (3.0 - 2.0 * t)

        # Smooth biome weights — blend over a transition band to avoid cliffs
        dw = _sstep(-n, 0.35, 0.55)                      # desert
        sw = _sstep( n, 0.45, 0.65)                      # snow
        fw = _sstep( n, 0.12, 0.32) * (1.0 - sw)        # forest
        pw = max(0.0, 1.0 - dw - sw - fw)                # plains

        bh = self.base_height
        dh = (bh - 3) + noise_val * self.amplitude * 0.40
        sh = (bh + 3) + noise_val * self.amplitude * 1.60
        fh =  bh      + noise_val * self.amplitude * 1.20
        plh = bh      + noise_val * self.amplitude

        h = int(dw * dh + sw * sh + fw * fh + pw * plh)
        return max(h, 4)   # clamp min terrain height — keep terrain within loaded cy>=0 chunks

    def _is_cave(self, wx: int, wy: int, wz: int) -> bool:
        s = 0.07
        n1 = self._cave.noise3(wx * s, wy * s * 1.4, wz * s)
        n2 = self._cave2.noise3(wx * s + 317, wy * s * 1.4, wz * s + 317)
        return (n1 * n1 + n2 * n2) < 0.07   # worm-like cave tubes

    def _get_biome(self, wx: int, wz: int) -> int:
        """0=Plains, 1=Desert, 2=Snow, 3=Forest."""
        n = self._biome.noise2(wx * 0.011, wz * 0.011)
        if n < -0.40:
            return 1  # Desert
        if n > 0.50:
            return 2  # Snow
        if n > 0.15:
            return 3  # Forest
        return 0  # Plains

    def get_biome(self, wx: int, wz: int) -> int:
        return self._get_biome(wx, wz)

    WATER_Y = 33   # sea level — terrain below this is flooded

    def generate_chunk(self, chunk: ChunkData) -> None:
        wx_base, wy_base, wz_base = chunk.world_position
        size = chunk.size

        for lx in range(size):
            for lz in range(size):
                wx = wx_base + lx
                wz = wz_base + lz
                surface_y = self.get_surface_height(wx, wz)
                biome = self._get_biome(wx, wz)

                # Trees only above sea level and not in water
                tree_h = (wx * 2654435761 ^ wz * 1664525 ^ self.seed) & 0xFFFF
                tree_limit = 1310 if biome == 3 else 393   # ~2% forest, ~0.6% plains
                has_tree = (biome in (0, 3)
                            and surface_y >= self.WATER_Y
                            and 1 <= lx <= size - 2 and 1 <= lz <= size - 2
                            and tree_h < tree_limit)
                ly_surf = surface_y - wy_base   # surface y in this chunk's local space

                for ly in range(size):
                    wy = wy_base + ly
                    bid = 0

                    if wy < surface_y - 4:
                        if biome == 1:
                            bid = 10   # sandstone (desert — no ores)
                        else:
                            bid = 3    # stone
                            depth = surface_y - wy
                            if depth >= 6:
                                # Cheap integer hash for ore veins — no noise needed
                                ore_h = (wx * 374761393 ^ wy * 1376312589 ^ wz * 2654435761 ^ self.seed) & 0xFFFF
                                if ore_h < 1966:             # ~3% coal ore
                                    bid = 14
                                elif depth >= 12 and ore_h < 2949:   # ~1.5% iron ore
                                    bid = 13
                    elif wy < surface_y:
                        bid = 9 if biome == 1 else 2   # sand or dirt
                    elif wy == surface_y:
                        if biome == 1:    bid = 9    # sand
                        elif biome == 2:  bid = 11   # snow
                        elif biome == 3:  bid = 12   # dark grass (forest)
                        else:             bid = 1    # grass (plains)

                    # Dungeon rooms & corridors
                    if bid != 0 and self.dungeon:
                        if self.dungeon.is_dungeon_air(wx, wy, wz):
                            bid = 0

                    chunk.set_block(lx, ly, lz, bid)

                # Fill terrain depressions with water up to sea level
                if surface_y < self.WATER_Y:
                    for wy_w in range(surface_y + 1, self.WATER_Y + 1):
                        ly_w = wy_w - wy_base
                        if 0 <= ly_w < size:
                            chunk.set_block(lx, ly_w, lz, 16)

                # Plant tree above surface when surface is within this chunk and has room
                if has_tree and 0 <= ly_surf < size - 5:
                    # Trunk: 3 wood blocks above surface
                    for ty in range(1, 4):
                        chunk.set_block(lx, ly_surf + ty, lz, 4)
                    # Canopy: 3×3 at +3 and +4, single block at +5
                    for dly, r in ((3, 1), (4, 1), (5, 0)):
                        nly = ly_surf + dly
                        if nly >= size:
                            break
                        for dlx in range(-r, r + 1):
                            for dlz in range(-r, r + 1):
                                nlx, nlz = lx + dlx, lz + dlz
                                if 0 <= nlx < size and 0 <= nlz < size:
                                    if chunk.get_block(nlx, nly, nlz) == 0:
                                        chunk.set_block(nlx, nly, nlz, 15)  # leaves
