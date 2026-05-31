from typing import Dict, Optional, Tuple
from .chunk import ChunkData


class World:
    """The voxel world — pure data, no rendering."""

    def __init__(self, chunk_size: int = 16):
        self._chunks: Dict[Tuple[int, int, int], ChunkData] = {}
        self.chunk_size = chunk_size

    def get_chunk(self, cx: int, cy: int, cz: int) -> Optional[ChunkData]:
        return self._chunks.get((cx, cy, cz))

    def get_or_create_chunk(self, cx: int, cy: int, cz: int) -> ChunkData:
        key = (cx, cy, cz)
        if key not in self._chunks:
            self._chunks[key] = ChunkData(cx, cy, cz, self.chunk_size)
        return self._chunks[key]

    def get_block(self, wx: int, wy: int, wz: int) -> int:
        s = self.chunk_size
        cx, lx = divmod(wx, s)
        cy, ly = divmod(wy, s)
        cz, lz = divmod(wz, s)
        chunk = self.get_chunk(cx, cy, cz)
        if chunk is None:
            return 0
        return chunk.get_block(lx, ly, lz)

    def set_block(self, wx: int, wy: int, wz: int, block_id: int) -> None:
        s = self.chunk_size
        cx, lx = divmod(wx, s)
        cy, ly = divmod(wy, s)
        cz, lz = divmod(wz, s)
        chunk = self.get_or_create_chunk(cx, cy, cz)
        chunk.set_block(lx, ly, lz, block_id)

    @property
    def loaded_chunks(self):
        return list(self._chunks.values())
