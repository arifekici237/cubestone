import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from core.chunk import ChunkData


def test_new_chunk_is_empty():
    chunk = ChunkData(0, 0, 0)
    assert chunk.is_empty()


def test_set_block_makes_chunk_non_empty():
    chunk = ChunkData(0, 0, 0)
    chunk.set_block(0, 0, 0, 1)
    assert not chunk.is_empty()


def test_get_block_returns_set_value():
    chunk = ChunkData(0, 0, 0)
    chunk.set_block(3, 7, 12, 2)
    assert chunk.get_block(3, 7, 12) == 2


def test_world_position_matches_chunk_coords():
    chunk = ChunkData(2, 1, 3, size=16)
    assert chunk.world_position == (32, 16, 48)


def test_unset_block_is_air():
    chunk = ChunkData(0, 0, 0)
    assert chunk.get_block(5, 5, 5) == 0
