import random
from typing import List, Dict, Any, Set, Tuple


class DungeonGenerator:
    """
    Three-floor underground dungeon.

    Floor 0 (shallow)  Y ~ 22  – sparse large rooms, boss chambers
    Floor 1 (mid)      Y ~ 14  – medium rooms, balanced density
    Floor 2 (deep)     Y ~  6  – dense small rooms, hardest mobs

    Rooms on the same floor are connected with L-shaped horizontal
    corridors.  Adjacent floors are linked by gently-sloped tunnels
    (max slope 1:2) so the player can always walk between levels.
    """

    FLOOR_Y = [22, 14, 6, -4, -14]

    def __init__(self, seed: int):
        rng = random.Random(seed ^ 0xDEAD)
        self._rooms:     List[Dict[str, Any]] = []
        self._corridors: List[Dict[str, Any]] = []

        # Generate rooms per floor, then build connections
        floor_rooms: List[List[Dict]] = []
        for fi, fy in enumerate(self.FLOOR_Y):
            rooms = self._gen_floor(rng, fi, fy)
            floor_rooms.append(rooms)
            self._rooms.extend(rooms)
            self._connect_horizontal(rooms)

        for fi in range(len(self.FLOOR_Y) - 1):
            self._connect_vertical(rng, floor_rooms[fi], floor_rooms[fi + 1])

        # Precompute air positions — O(1) lookup at runtime
        self._air_set: Set[Tuple[int, int, int]] = set()
        self._carve_all()

    # ──────────────────────────────────────────────────────────────────
    # Room generation
    # ──────────────────────────────────────────────────────────────────
    def _gen_floor(self, rng: random.Random, fi: int, fy: int) -> List[Dict]:
        rooms: List[Dict] = []
        spacing = 30 - fi * 3          # deeper floors pack tighter
        prob    = 0.28 + fi * 0.09     # deeper floors denser
        grid    = range(-4, 5)

        for gi in grid:
            for gj in grid:
                if rng.random() > prob:
                    continue
                rx = gi * spacing + rng.randint(-7, 7)
                rz = gj * spacing + rng.randint(-7, 7)

                roll = rng.random()
                if roll < 0.10:
                    # Boss / large room
                    w, h, d = rng.randint(12, 20), rng.randint(4, 7), rng.randint(12, 20)
                    rt = 'large'
                elif roll < 0.22:
                    # Tall tower room
                    w, h, d = rng.randint(5, 8), rng.randint(8, 12), rng.randint(5, 8)
                    rt = 'tall'
                else:
                    # Standard room
                    w, h, d = rng.randint(5, 10), rng.randint(3, 5), rng.randint(5, 10)
                    rt = 'standard'

                rooms.append({'x': rx, 'y': fy, 'z': rz,
                              'w': w,  'h': h,  'd': d,
                              'type': rt, 'floor': fi})
        return rooms

    # ──────────────────────────────────────────────────────────────────
    # Corridor planning
    # ──────────────────────────────────────────────────────────────────
    def _connect_horizontal(self, rooms: List[Dict]) -> None:
        """Connect every room to its nearest same-floor neighbour."""
        for i, a in enumerate(rooms):
            best_d2, nearest = float('inf'), None
            for j, b in enumerate(rooms):
                if i == j:
                    continue
                d2 = (a['x'] - b['x'])**2 + (a['z'] - b['z'])**2
                if d2 < best_d2 and d2 < 70**2:
                    best_d2, nearest = d2, b
            if nearest:
                self._corridors.append({'a': a, 'b': nearest, 'kind': 'h'})

    def _connect_vertical(self, rng: random.Random,
                          upper: List[Dict], lower: List[Dict]) -> None:
        """Pair each upper room with the closest lower room; keep ~1/3 of pairs."""
        if not upper or not lower:
            return
        pairs: List[Tuple[Dict, Dict]] = []
        for u in upper:
            cx_u = u['x'] + u['w'] // 2
            cz_u = u['z'] + u['d'] // 2
            best_d2, best_l = float('inf'), None
            for l in lower:
                cx_l = l['x'] + l['w'] // 2
                cz_l = l['z'] + l['d'] // 2
                d2 = (cx_u - cx_l)**2 + (cz_u - cz_l)**2
                if d2 < best_d2 and d2 < 60**2:
                    best_d2, best_l = d2, l
            if best_l:
                pairs.append((u, best_l))

        rng.shuffle(pairs)
        keep = max(2, len(pairs) // 3)
        for u, l in pairs[:keep]:
            self._corridors.append({'a': u, 'b': l, 'kind': 'slope'})

    # ──────────────────────────────────────────────────────────────────
    # Carving
    # ──────────────────────────────────────────────────────────────────
    def _carve_all(self) -> None:
        for r in self._rooms:
            for wx in range(r['x'], r['x'] + r['w']):
                for wy in range(r['y'], r['y'] + r['h']):
                    for wz in range(r['z'], r['z'] + r['d']):
                        self._air_set.add((wx, wy, wz))

        for c in self._corridors:
            a, b = c['a'], c['b']
            ax = a['x'] + a['w'] // 2
            az = a['z'] + a['d'] // 2
            ay = a['y']
            bx = b['x'] + b['w'] // 2
            bz = b['z'] + b['d'] // 2
            by = b['y']

            if c['kind'] == 'h':
                self._carve_h(ax, az, ay, bx, bz)
            else:
                self._carve_slope(ax, ay, az, bx, by, bz)

    def _carve_h(self, ax: int, az: int, ay: int, bx: int, bz: int) -> None:
        """L-shaped horizontal corridor: 3 wide × 3 tall."""
        # X segment
        for wx in range(min(ax, bx), max(ax, bx) + 1):
            for wy in range(ay, ay + 3):
                for wz in range(az - 1, az + 2):
                    self._air_set.add((wx, wy, wz))
        # Z segment
        for wz in range(min(az, bz), max(az, bz) + 1):
            for wy in range(ay, ay + 3):
                for wx in range(bx - 1, bx + 2):
                    self._air_set.add((wx, wy, wz))

    def _carve_slope(self, ax: int, ay: int, az: int,
                     bx: int, by: int, bz: int) -> None:
        """Sloped tunnel between two Y levels.

        Steps are chosen so the gradient never exceeds 1:2 — gentle
        enough for the player to walk without needing to jump.
        """
        dx = bx - ax
        dz = bz - az
        dy = by - ay
        # Guarantee gentle slope: at least 2 horizontal steps per Y unit
        steps = max(abs(dx), abs(dz), abs(dy) * 2, 1)

        for i in range(steps + 1):
            t  = i / steps
            wx = int(ax + t * dx)
            wy = int(ay + t * dy)
            wz = int(az + t * dz)
            # 3 × 3 × 3 opening so the player can always pass through
            for ddx in range(-1, 2):
                for ddy in range(0, 3):
                    for ddz in range(-1, 2):
                        self._air_set.add((wx + ddx, wy + ddy, wz + ddz))

    # ──────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────
    def is_dungeon_air(self, wx: int, wy: int, wz: int) -> bool:
        return (wx, wy, wz) in self._air_set

    def get_room_centers(self) -> List[Tuple[float, float, float]]:
        return [
            (r['x'] + r['w'] / 2, r['y'] + 0.5, r['z'] + r['d'] / 2)
            for r in self._rooms
        ]

    def get_chest_rooms(self) -> List[Tuple[float, float, float, int]]:
        """Centers of large rooms: (cx, cy, cz, floor_index)."""
        return [
            (r['x'] + r['w'] / 2, r['y'] + 0.5, r['z'] + r['d'] / 2, r['floor'])
            for r in self._rooms if r['type'] == 'large'
        ]
