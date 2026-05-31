"""
Lightweight sound-effect service.

Presentation-only feedback layer — like ``ui/particles``, gameplay systems
call into it without depending on the audio engine directly. Clips are loaded
once into a cache and replayed by name, so triggering a sound is allocation-free
at runtime (no new Entity per shot).

Clips live in ``assets/sounds/`` as procedurally-generated WAVs
(see ``tools/gen_sounds.py``). ``init()`` must be called once, after the Ursina
app exists. Every call is wrapped defensively: if audio is unavailable the game
keeps running silently.
"""
from pathlib import Path

_SOUND_DIR = Path(__file__).parent.parent.parent / 'assets' / 'sounds'

_clips: dict = {}
_music = None
_enabled = True
_ready = False


def init(volume: float = 1.0) -> None:
    """Preload every WAV in assets/sounds. Safe to call once after Ursina()."""
    global _ready
    if _ready:
        return
    _ready = True
    if not _SOUND_DIR.exists():
        print('[sfx] no sound folder, audio disabled')
        return
    try:
        from ursina import Audio
    except Exception as e:
        print(f'[sfx] Audio import failed: {e}')
        return
    for f in sorted(_SOUND_DIR.glob('*.wav')):
        if f.stem == 'music_ambient':
            continue   # streamed separately as looping music
        try:
            _clips[f.stem] = Audio(f, autoplay=False, auto_destroy=False)
        except Exception as e:
            print(f'[sfx] failed to load {f.name}: {e}')
    print(f'[sfx] loaded {len(_clips)} clips')


def play(name: str, volume: float = 1.0, pitch: float = 1.0) -> None:
    """Play a one-shot effect by name (e.g. 'jump', 'hit'). No-op if missing."""
    if not _enabled:
        return
    clip = _clips.get(name)
    if clip is None:
        return
    try:
        clip.volume = volume
        clip.pitch = pitch
        clip.play()
    except Exception:
        pass


def start_music(volume: float = 0.35) -> None:
    """Begin looping background music (optional ambient bed)."""
    global _music
    if _music is not None:
        return
    path = _SOUND_DIR / 'music_ambient.wav'
    if not path.exists():
        return
    try:
        from ursina import Audio
        _music = Audio(path, loop=True, autoplay=True,
                       auto_destroy=False, volume=volume, group='music')
    except Exception as e:
        print(f'[sfx] music failed: {e}')


def set_enabled(value: bool) -> None:
    global _enabled
    _enabled = value
