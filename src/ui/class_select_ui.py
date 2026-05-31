"""Class selection screen shown at game start."""
from PIL import Image, ImageDraw
from ursina import Entity, camera, Texture, destroy, color, Text, invoke

from systems.player_class import CLASSES, CLASS_ORDER
from ui._fonts import TITLE, HEAD, BODY, SMALL

_W,  _H  = 1.0,  0.88
_IW, _IH = 900, 580

_BG   = (12, 8,  22)
_ACC  = (120, 40, 180)
_SEP  = (70,  20, 110)
_TC   = (220, 80, 255)
_HDR  = (160, 120, 200)
_KEY  = (255, 220, 60)
_DESC = (170, 150, 210)
_DIM  = (100, 80,  140)


def _cx_in(draw, text, font, x0, x1):
    bb = draw.textbbox((0, 0), text, font=font)
    w  = bb[2] - bb[0]
    return x0 + (x1 - x0 - w) // 2


def _draw_card(draw, x0, y0, w, h, cls_obj, key_label: str, selected: bool):
    border = cls_obj.color if selected else (60, 40, 80)
    bg     = (28, 14, 48) if selected else (20, 10, 35)
    draw.rectangle([x0, y0, x0 + w, y0 + h], fill=bg)
    draw.rectangle([x0, y0, x0 + w, y0 + 3], fill=border)
    draw.rectangle([x0, y0 + h - 3, x0 + w, y0 + h], fill=border)

    # Key badge
    kx = _cx_in(draw, key_label, HEAD, x0, x0 + w)
    draw.text((kx, y0 + 8), key_label, font=HEAD, fill=_KEY)

    # Class icon (colored circle)
    cx_ = x0 + w // 2
    cy_ = y0 + 80
    r   = 34
    draw.ellipse([cx_ - r, cy_ - r, cx_ + r, cy_ + r], fill=cls_obj.icon_color)
    # Inner highlight
    draw.ellipse([cx_ - r + 4, cy_ - r + 4, cx_ + r - 8, cy_ + r - 8],
                 fill=tuple(min(255, c + 50) for c in cls_obj.icon_color))

    # Class name
    name_x = _cx_in(draw, cls_obj.label, TITLE, x0, x0 + w)
    draw.text((name_x, y0 + 124), cls_obj.label, font=TITLE, fill=cls_obj.color)

    # Stats
    stats = [
        f'HP:   {cls_obj.base_hp}',
        f'ATK:  +{cls_obj.base_atk}',
        f'HIZ:  x{cls_obj.base_spd}',
    ]
    sy = y0 + 172
    for s in stats:
        sx = _cx_in(draw, s, BODY, x0, x0 + w)
        draw.text((sx, sy), s, font=BODY, fill=_DESC)
        sy += 24

    # Separator
    draw.rectangle([x0 + 10, sy + 4, x0 + w - 10, sy + 6], fill=_SEP)
    sy += 12

    # Ability
    draw.text((_cx_in(draw, cls_obj.ability_name, HEAD, x0, x0 + w), sy),
              cls_obj.ability_name, font=HEAD, fill=_KEY)
    sy += 26
    # Wrap desc to two lines if needed
    draw.text((_cx_in(draw, cls_obj.ability_desc, SMALL, x0, x0 + w), sy),
              cls_obj.ability_desc, font=SMALL, fill=_DIM)


class ClassSelectUI(Entity):
    def __init__(self, on_select):
        """on_select(class_name: str) called when player picks a class."""
        super().__init__(parent=camera.ui)
        self.on_select = on_select
        self.is_open   = True

        self._panel = Entity(parent=camera.ui, model='quad', scale=(_W, _H))
        self._render()
        self._panel.enabled = True

        # Dim overlay behind cards
        self._overlay = Entity(
            parent=camera.ui, model='quad',
            scale=(2, 2), color=color.rgba(0, 0, 0, 180),
            z=0.01,
        )

    def _render(self):
        img  = Image.new('RGB', (_IW, _IH), _BG)
        draw = ImageDraw.Draw(img)

        # Top bar
        draw.rectangle([0, 0, _IW, 5], fill=_ACC)

        # Title
        t  = 'SINIF SEC'
        bb = draw.textbbox((0, 0), t, font=TITLE)
        tx = (_IW - (bb[2] - bb[0])) // 2
        draw.text((tx, 14), t, font=TITLE, fill=_TC)
        draw.rectangle([8, 56, _IW - 8, 58], fill=_SEP)

        # Sub-title
        sub = 'Karakterin icin bir sinif sec — [1] [2] [3]'
        bb  = draw.textbbox((0, 0), sub, font=BODY)
        draw.text((_IW // 2 - (bb[2] - bb[0]) // 2, 64), sub, font=BODY, fill=_DESC)

        # Three class cards
        card_w  = 250
        card_h  = 440
        gap     = 25
        total_w = 3 * card_w + 2 * gap
        start_x = (_IW - total_w) // 2
        card_y  = 92

        for i, name in enumerate(CLASS_ORDER):
            cls = CLASSES[name]
            cx  = start_x + i * (card_w + gap)
            _draw_card(draw, cx, card_y, card_w, card_h, cls, f'[{i+1}]', False)

        # Bottom hint
        draw.rectangle([8, _IH - 36, _IW - 8, _IH - 34], fill=_SEP)
        hint = 'Escape = varsayilan Savasci ile devam et'
        bb   = draw.textbbox((0, 0), hint, font=SMALL)
        draw.text((_IW // 2 - (bb[2] - bb[0]) // 2, _IH - 28),
                  hint, font=SMALL, fill=_DIM)

        self._panel.texture = Texture(img)

    def _select(self, class_name: str):
        self.is_open = False
        self._panel.enabled  = False
        self._overlay.enabled = False
        destroy(self._panel)
        destroy(self._overlay)
        if self.on_select:
            self.on_select(class_name)
        destroy(self)

    def input(self, key):
        if not self.is_open:
            return
        mapping = {'1': 'knight', '2': 'ranger', '3': 'mage'}
        if key in mapping:
            self._select(mapping[key])
        elif key == 'escape':
            self._select('knight')
