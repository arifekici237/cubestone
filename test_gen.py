import time
import json
from pathlib import Path
from src.core.world import World
from src.core.generation import TerrainGenerator

settings = json.load(open(Path('config/settings/game_settings.json')))
chunk_size = settings['chunk_size']
world = World(chunk_size=chunk_size)
generator = TerrainGenerator(
    seed=settings['seed'],
    base_height=settings['base_terrain_height'],
    amplitude=settings['terrain_amplitude'],
)
rd = settings['render_distance']
total_chunks = (2*rd)**2 * 6
print(f'Generating {total_chunks} chunks...')

start = time.time()
count = 0
for cx in range(-rd, rd):
    for cz in range(-rd, rd):
        for cy in range(0, 6):
            chunk = world.get_or_create_chunk(cx, cy, cz)
            generator.generate_chunk(chunk)
            count += 1
            if count % 100 == 0:
                elapsed = time.time() - start
                print(f'Generated {count}/{total_chunks} chunks in {elapsed:.1f}s')

elapsed = time.time() - start
print(f'Total time: {elapsed:.1f}s for {total_chunks} chunks ({total_chunks/elapsed:.0f} chunks/sec)')
