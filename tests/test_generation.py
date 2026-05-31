import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from core.generation import TerrainGenerator
from core.chunk import ChunkData


def test_surface_height_returns_int():
    gen = TerrainGenerator(seed=0)
    assert isinstance(gen.get_surface_height(0, 0), int)


def test_generate_chunk_fills_blocks():
    gen = TerrainGenerator(seed=0)
    chunk = ChunkData(0, 0, 0)
    gen.generate_chunk(chunk)
    assert not chunk.is_empty()


def test_different_seeds_produce_different_terrain():
    gen1 = TerrainGenerator(seed=0)
    gen2 = TerrainGenerator(seed=99999)
    heights1 = [gen1.get_surface_height(x, 0) for x in range(0, 100, 5)]
    heights2 = [gen2.get_surface_height(x, 0) for x in range(0, 100, 5)]
    assert heights1 != heights2


def test_surface_height_varies_across_terrain():
    gen = TerrainGenerator(seed=42)
    heights = {gen.get_surface_height(x, 0) for x in range(0, 200, 10)}
    assert len(heights) > 1
