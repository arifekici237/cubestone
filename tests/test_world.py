import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from core.world import World


def test_set_and_get_block():
    world = World()
    world.set_block(0, 0, 0, 1)
    assert world.get_block(0, 0, 0) == 1


def test_unset_block_returns_air():
    world = World()
    assert world.get_block(100, 100, 100) == 0


def test_chunk_created_on_set_block():
    world = World()
    world.set_block(5, 5, 5, 2)
    assert world.get_chunk(0, 0, 0) is not None


def test_set_block_cross_chunk_boundary():
    world = World()
    world.set_block(0, 0, 0, 1)
    world.set_block(16, 0, 0, 2)
    assert world.get_block(0, 0, 0) == 1
    assert world.get_block(16, 0, 0) == 2


def test_loaded_chunks_count():
    world = World()
    world.set_block(0, 0, 0, 1)
    world.set_block(16, 0, 0, 2)
    assert len(world.loaded_chunks) == 2
