"""
Procedural sound-effect generator.

The project ships no binary audio assets; instead every SFX is *synthesised*
from code so the repository stays small, deterministic and license-free.
Run once to (re)generate the WAV files under ``assets/sounds/``:

    python tools/gen_sounds.py

16-bit PCM mono, 44.1 kHz. Each clip is short and envelope-shaped to avoid
click artefacts at the edges.
"""
import struct
import wave
from pathlib import Path

import numpy as np

SR = 44100  # sample rate
OUT_DIR = Path(__file__).parent.parent / 'assets' / 'sounds'


# ── Synthesis primitives ────────────────────────────────────────────────
def _t(duration: float) -> np.ndarray:
    return np.linspace(0.0, duration, int(SR * duration), endpoint=False)


def sine(freq, duration, t=None):
    tt = _t(duration) if t is None else t
    f = freq(tt) if callable(freq) else freq
    return np.sin(2 * np.pi * f * tt)


def square(freq, duration):
    return np.sign(sine(freq, duration))


def noise(duration):
    return np.random.uniform(-1.0, 1.0, int(SR * duration))


def env_ad(sig, attack=0.005, decay=None):
    """Attack/decay amplitude envelope (linear attack, exponential-ish decay)."""
    n = len(sig)
    e = np.ones(n)
    a = max(1, int(SR * attack))
    e[:a] = np.linspace(0.0, 1.0, a)
    d = n - a if decay is None else int(SR * decay)
    d = min(d, n - a)
    if d > 0:
        e[a:a + d] *= np.linspace(1.0, 0.0, d) ** 1.8
    return sig * e


def normalize(sig, peak=0.9):
    m = np.max(np.abs(sig)) or 1.0
    return sig / m * peak


def save(name: str, sig: np.ndarray):
    sig = normalize(sig)
    data = (sig * 32767).astype('<i2')
    path = OUT_DIR / f'{name}.wav'
    with wave.open(str(path), 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())
    print(f'  wrote {path.name}  ({len(sig)/SR:.2f}s)')


# ── Individual effects ──────────────────────────────────────────────────
def make_jump():
    t = _t(0.18)
    f = 320 + 320 * (t / 0.18)            # rising blip 320→640 Hz
    return env_ad(np.sin(2 * np.pi * f * t), attack=0.004, decay=0.16)


def make_hit():
    # Combat thwack: short noise burst + low thump
    body = env_ad(noise(0.10), attack=0.001, decay=0.09) * 0.7
    thump = env_ad(sine(150, 0.10), attack=0.001, decay=0.09) * 0.8
    return body + thump


def make_hurt():
    # Player damage: dark descending tone with a little grit
    t = _t(0.26)
    f = 300 - 150 * (t / 0.26)            # 300→150 Hz
    tone = np.sin(2 * np.pi * f * t)
    grit = noise(0.26) * 0.25
    return env_ad(tone + grit, attack=0.003, decay=0.24)


def make_block_break():
    return env_ad(noise(0.14), attack=0.001, decay=0.13)


def make_block_place():
    return env_ad(sine(190, 0.10), attack=0.002, decay=0.09)


def make_pickup():
    # Pleasant two-step ding up
    a = env_ad(sine(660, 0.09), attack=0.003, decay=0.08)
    b = env_ad(sine(990, 0.12), attack=0.003, decay=0.11)
    return np.concatenate([a, b])


def make_levelup():
    # Ascending arpeggio C5 E5 G5 C6
    notes = [523, 659, 784, 1046]
    parts = [env_ad(sine(f, 0.14), attack=0.005, decay=0.13) for f in notes]
    return np.concatenate(parts)


def make_enemy_death():
    # Descending squarish growl 440→110
    t = _t(0.30)
    f = 440 - 330 * (t / 0.30)
    sig = np.sign(np.sin(2 * np.pi * f * t)) * 0.6 + np.sin(2 * np.pi * f * t) * 0.4
    return env_ad(sig, attack=0.003, decay=0.28)


def make_ability():
    # Whoosh: noise + rising sine sweep
    t = _t(0.34)
    sweep = np.sin(2 * np.pi * (200 + 700 * (t / 0.34)) * t)
    air = noise(0.34) * 0.4
    return env_ad(sweep * 0.7 + air, attack=0.02, decay=0.30)


def make_click():
    return env_ad(sine(1200, 0.04), attack=0.001, decay=0.035)


def make_death():
    # Player death sting: low descending tone, longer
    t = _t(0.7)
    f = 220 - 150 * (t / 0.7)
    tone = np.sin(2 * np.pi * f * t)
    sub = np.sin(2 * np.pi * (f / 2) * t) * 0.5
    return env_ad(tone + sub, attack=0.01, decay=0.68)


def make_music_ambient():
    # Soft 8s looping pad: root + fifth + octave with slow tremolo.
    dur = 8.0
    t = _t(dur)
    root = 110.0   # A2
    chord = (np.sin(2 * np.pi * root * t)
             + 0.6 * np.sin(2 * np.pi * root * 1.5 * t)     # fifth
             + 0.4 * np.sin(2 * np.pi * root * 2.0 * t))    # octave
    tremolo = 0.75 + 0.25 * np.sin(2 * np.pi * 0.12 * t)    # slow swell
    sig = chord * tremolo
    # Cross-fade the seam so the loop is click-free
    fade = int(SR * 0.4)
    sig[:fade] *= np.linspace(0.0, 1.0, fade)
    sig[-fade:] *= np.linspace(1.0, 0.0, fade)
    return sig * 0.5


GENERATORS = {
    'jump':          make_jump,
    'hit':           make_hit,
    'hurt':          make_hurt,
    'block_break':   make_block_break,
    'block_place':   make_block_place,
    'pickup':        make_pickup,
    'levelup':       make_levelup,
    'enemy_death':   make_enemy_death,
    'ability':       make_ability,
    'click':         make_click,
    'death':         make_death,
    'music_ambient': make_music_ambient,
}


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    np.random.seed(42)   # deterministic noise → reproducible files
    print(f'Generating {len(GENERATORS)} sounds → {OUT_DIR}')
    for name, fn in GENERATORS.items():
        save(name, fn())
    print('Done.')


if __name__ == '__main__':
    main()
