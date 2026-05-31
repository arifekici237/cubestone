from typing import List, Tuple, Optional, Callable, Dict
from core.chunk import ChunkData


# +X, -X, +Y, -Y, +Z, -Z
FACE_NORMALS = [
    (1, 0, 0), (-1, 0, 0),
    (0, 1, 0), (0, -1, 0),
    (0, 0, 1), (0, 0, -1),
]

_FACE_VERTS = [
    [(1,0,0),(1,1,0),(1,1,1),(1,0,1)],  # +X
    [(0,0,1),(0,1,1),(0,1,0),(0,0,0)],  # -X
    [(0,1,0),(0,1,1),(1,1,1),(1,1,0)],  # +Y
    [(0,0,1),(0,0,0),(1,0,0),(1,0,1)],  # -Y
    [(1,0,1),(1,1,1),(0,1,1),(0,0,1)],  # +Z
    [(0,0,0),(0,1,0),(1,1,0),(1,0,0)],  # -Z
]

# face_index 2 = +Y (top), 3 = -Y (bottom), rest = sides
_BLOCK_COLORS: Dict[int, Dict[str, tuple]] = {
    1: {'top': (0.24, 0.64, 0.11, 1), 'side': (0.26, 0.52, 0.09, 1), 'bot': (0.42, 0.26, 0.07, 1)},  # grass
    2: {'top': (0.46, 0.30, 0.09, 1), 'side': (0.46, 0.30, 0.09, 1), 'bot': (0.42, 0.26, 0.07, 1)},  # dirt
    3: {'top': (0.52, 0.54, 0.60, 1), 'side': (0.49, 0.51, 0.57, 1), 'bot': (0.45, 0.47, 0.53, 1)},  # stone - blue-grey
    4: {'top': (0.56, 0.38, 0.16, 1), 'side': (0.50, 0.33, 0.13, 1), 'bot': (0.44, 0.28, 0.10, 1)},  # wood
    5: {'top': (0.78, 0.78, 0.83, 1), 'side': (0.73, 0.73, 0.78, 1), 'bot': (0.68, 0.68, 0.72, 1)},  # smooth stone - light
    6: {'top': (0.90, 0.75, 0.44, 1), 'side': (0.83, 0.68, 0.38, 1), 'bot': (0.78, 0.63, 0.34, 1)},  # planks - warm oak
    7: {'top': (0.44, 0.36, 0.22, 1), 'side': (0.40, 0.32, 0.19, 1), 'bot': (0.35, 0.28, 0.15, 1)},  # mud
    8: {'top': (0.98, 0.86, 0.14, 1), 'side': (0.92, 0.78, 0.10, 1), 'bot': (0.84, 0.70, 0.07, 1)},  # gold - vibrant
    9: {'top': (0.85, 0.78, 0.46, 1), 'side': (0.80, 0.73, 0.40, 1), 'bot': (0.74, 0.66, 0.34, 1)},  # sand
   10: {'top': (0.78, 0.70, 0.38, 1), 'side': (0.72, 0.64, 0.33, 1), 'bot': (0.66, 0.58, 0.28, 1)},  # sandstone
   11: {'top': (0.94, 0.96, 1.00, 1), 'side': (0.88, 0.90, 0.96, 1), 'bot': (0.80, 0.82, 0.90, 1)},  # snow
   12: {'top': (0.15, 0.52, 0.08, 1), 'side': (0.18, 0.44, 0.07, 1), 'bot': (0.42, 0.26, 0.07, 1)},  # dark grass (forest)
   13: {'top': (0.55, 0.42, 0.33, 1), 'side': (0.51, 0.38, 0.30, 1), 'bot': (0.47, 0.35, 0.27, 1)},  # iron ore
   14: {'top': (0.28, 0.28, 0.28, 1), 'side': (0.24, 0.24, 0.24, 1), 'bot': (0.21, 0.21, 0.21, 1)},  # coal ore
   15: {'top': (0.13, 0.62, 0.08, 1), 'side': (0.12, 0.55, 0.07, 1), 'bot': (0.11, 0.50, 0.06, 1)},  # leaves
   16: {'top': (0.10, 0.48, 0.88, 1), 'side': (0.08, 0.40, 0.80, 1), 'bot': (0.06, 0.32, 0.72, 1)},  # water
   17: {'top': (0.98, 0.82, 0.12, 1), 'side': (0.92, 0.70, 0.08, 1), 'bot': (0.84, 0.58, 0.04, 1)},  # torch
}
_FALLBACK = (0.6, 0.6, 0.6, 1)

# Brightness per face (+X -X +Y -Y +Z -Z) — larger spread = better depth cues
_FACE_DIM = (0.82, 0.68, 1.00, 0.44, 0.92, 0.60)


def _color_for(block_id: int, face_index: int) -> tuple:
    entry = _BLOCK_COLORS.get(block_id)
    c = _FALLBACK if entry is None else (
        entry['top'] if face_index == 2 else
        entry['bot'] if face_index == 3 else
        entry['side']
    )
    d = _FACE_DIM[face_index]
    return (c[0] * d, c[1] * d, c[2] * d, c[3])


class MeshData:
    def __init__(self):
        self.vertices: List[Tuple[float, float, float]] = []
        self.triangles: List[int] = []
        self.uvs: List[Tuple[float, float]] = []
        self.normals: List[Tuple[float, float, float]] = []
        self.colors: List[Tuple[float, float, float, float]] = []

    def add_face(self, pos: Tuple[int, int, int], face_index: int, block_id: int = 1) -> None:
        x, y, z = pos
        base = len(self.vertices)
        for vx, vy, vz in _FACE_VERTS[face_index]:
            self.vertices.append((x + vx, y + vy, z + vz))
        self.triangles += [base, base+1, base+2, base, base+2, base+3]
        self.uvs += [(0, 0), (1, 0), (1, 1), (0, 1)]
        n = FACE_NORMALS[face_index]
        self.normals += [n, n, n, n]
        c = _color_for(block_id, face_index)
        self.colors += [c, c, c, c]


def build_mesh(
    chunk: ChunkData,
    neighbor_getter: Optional[Callable[[int, int, int], int]] = None,
) -> MeshData:
    mesh = MeshData()
    size = chunk.size

    for x in range(size):
        for y in range(size):
            for z in range(size):
                block_id = chunk.get_block(x, y, z)
                if block_id == 0:
                    continue

                for face_idx, (dx, dy, dz) in enumerate(FACE_NORMALS):
                    nx, ny, nz = x + dx, y + dy, z + dz

                    if 0 <= nx < size and 0 <= ny < size and 0 <= nz < size:
                        neighbor = chunk.get_block(nx, ny, nz)
                    elif neighbor_getter:
                        wx_base, wy_base, wz_base = chunk.world_position
                        neighbor = neighbor_getter(
                            wx_base + nx, wy_base + ny, wz_base + nz
                        )
                    else:
                        neighbor = 0

                    if neighbor == 0:
                        mesh.add_face((x, y, z), face_idx, block_id)

    return mesh


def build_mesh_by_type(
    chunk: ChunkData,
    neighbor_getter: Optional[Callable[[int, int, int], int]] = None,
) -> Dict[int, MeshData]:
    """Single-pass build: returns one MeshData per block type present."""
    meshes: Dict[int, MeshData] = {}
    size = chunk.size

    for x in range(size):
        for y in range(size):
            for z in range(size):
                block_id = chunk.get_block(x, y, z)
                if block_id == 0:
                    continue
                if block_id not in meshes:
                    meshes[block_id] = MeshData()
                md = meshes[block_id]

                for face_idx, (dx, dy, dz) in enumerate(FACE_NORMALS):
                    nx, ny, nz = x + dx, y + dy, z + dz

                    if 0 <= nx < size and 0 <= ny < size and 0 <= nz < size:
                        neighbor = chunk.get_block(nx, ny, nz)
                    elif neighbor_getter:
                        wx_base, wy_base, wz_base = chunk.world_position
                        neighbor = neighbor_getter(
                            wx_base + nx, wy_base + ny, wz_base + nz
                        )
                    else:
                        neighbor = 0

                    if neighbor == 0:
                        md.add_face((x, y, z), face_idx, block_id)

    return meshes
