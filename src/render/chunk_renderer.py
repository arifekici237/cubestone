from ursina import Entity, Mesh, color
from core.chunk import ChunkData
from render.mesher import build_mesh


class ChunkRenderer(Entity):
    """Single entity per chunk — vertex colors encode block type."""

    def __init__(self, chunk_data: ChunkData, neighbor_getter=None,
                 with_collider: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.chunk_data = chunk_data
        self.neighbor_getter = neighbor_getter
        self._with_collider = with_collider
        self.rebuild()

    def rebuild(self) -> None:
        mesh_data = build_mesh(self.chunk_data, self.neighbor_getter)

        if not mesh_data.vertices:
            self.model = None
            return

        self.model = Mesh(
            vertices=mesh_data.vertices,
            triangles=mesh_data.triangles,
            uvs=mesh_data.uvs,
            normals=mesh_data.normals,
            colors=mesh_data.colors,
            mode='triangle',
        )
        wx, wy, wz = self.chunk_data.world_position
        self.position = (wx, wy, wz)
        self.color = color.white
        self.double_sided = True
        self.collider = 'mesh' if self._with_collider else None

    def set_collider(self, enabled: bool) -> None:
        self._with_collider = enabled
        if self.model:
            self.collider = 'mesh' if enabled else None
