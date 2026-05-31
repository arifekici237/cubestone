from pathlib import Path
from PIL import ImageFont

_FONT_DIR = Path("C:/Windows/Fonts")

def _try(name: str, size: int):
    for candidate in [name, name.lower(), name.upper()]:
        try:
            return ImageFont.truetype(str(_FONT_DIR / candidate), size)
        except Exception:
            pass
    return None

def load(size: int) -> ImageFont.ImageFont:
    for name in ['arialbd.ttf', 'arial.ttf', 'consola.ttf', 'cour.ttf']:
        f = _try(name, size)
        if f:
            return f
    return ImageFont.load_default()

TITLE = load(34)
HEAD  = load(22)
BODY  = load(18)
SMALL = load(14)
