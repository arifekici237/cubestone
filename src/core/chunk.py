import numpy as np
from typing import Tuple


class ChunkData:
    """Pure data container for a voxel chunk. No rendering logic."""

    def __init__(self, cx: int, cy: int, cz: int, size: int = 16):
        self.cx = cx
        self.cy = cy
        self.cz = cz
        self.size = size
        self.blocks = np.zeros((size, size, size), dtype=np.uint16)

    def get_block(self, x: int, y: int, z: int) -> int:
        return int(self.blocks[x, y, z])

    def set_block(self, x: int, y: int, z: int, block_id: int) -> None:
        self.blocks[x, y, z] = block_id

    def is_empty(self) -> bool:
        return not np.any(self.blocks)

    @property
    def world_position(self) -> Tuple[int, int, int]:
        return (self.cx * self.size, self.cy * self.size, self.cz * self.size)
