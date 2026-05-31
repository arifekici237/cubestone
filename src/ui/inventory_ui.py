from PIL import Image, ImageDraw
from ursina import Entity, camera, Texture

from ui._fonts import TITLE, HEAD, BODY, SMALL

_W,  _H  = 0.74, 0.97
_IW, _IH = 512, 820

_BG    = (12,  15,  28)
_ACC   = (0,   140, 180)
_SEP   = (0,   80,  100)
_SEC   = (20,  30,  55)
_ROWD  = (18,  22,  42)
_TC    = (0,   220, 230)
_HDR_B = (100, 180, 255)
_HDR_I = (100, 220, 180)
_HDR_G = (180, 100, 240)
_SUB   = (140, 140, 160)
_WHITE = (210, 210, 220)
_DIM   = (70,  70,  80)

_RARITY_C = {
    'common':   (180, 180, 180),
    'uncommon': (80,  220, 80),
    'rare':     (80,  140, 255),
    'epic':     (200, 60,  255),
}

_BLOCK_NAMES = {
    1: 'Grass',        2: 'Dirt',
    3: 'Stone',        4: 'Wood',
    5: 'Smooth Stone', 6: 'Planks',
    7: 'Mud Block',    8: 'Gold Block',
}
_BLOCK_COLS = {
    1: (69,  153, 36),   2: (115, 72,  20),
    3: (120, 125, 140),  4: (130, 87,  38),
    5: (190, 190, 200),  6: (220, 188, 112),
    7: (100, 82,  52),   8: (245, 215, 35),
}
_ITEM_KEYS  = ['coin', 'slime_gel', 'health_potion']
_ITEM_NAMES = {'coin': 'Coin', 'slime_gel': 'Slime Jel', 'health_potion': 'Iyilestirme'}
_ITEM_COLS  = {'coin': (230, 200, 0), 'slime_gel': (80, 220, 80), 'health_potion': (230, 100, 180)}


def _cx(draw, text, font):
    bb = draw.textbbox((0, 0), text, font=font)
    return (_IW - (bb[2] - bb[0])) // 2


def _rw(draw, text, font):
    bb = draw.textbbox((0, 0), text, font=font)
    return bb[2] - bb[0]


class InventoryUI(Entity):
    def __init__(self, block_counts: dict, item_counts: dict, equipment=None):
        super().__init__(parent=camera.ui)
        self.block_counts = block_counts
        self.item_counts  = item_counts
        self.equipment    = equipment
        self.is_open      = False

        self._panel = Entity(parent=camera.ui, model='quad', scale=(_W, _H))
        self._panel.enabled = False

    # ------------------------------------------------------------------
    def _render(self):
        img  = Image.new('RGB', (_IW, _IH), _BG)
        draw = ImageDraw.Draw(img)

        draw.rectangle([0, 0, _IW, 5],          fill=_ACC)
        draw.rectangle([0, _IH - 5, _IW, _IH],  fill=_ACC)

        title = 'ENVANTER'
        draw.text((_cx(draw, title, TITLE), 14), title, font=TITLE, fill=_TC)

        hint = '[I] kapat     [H] iksir kullan     [C] ekipman yonet'
        draw.text((_cx(draw, hint, SMALL), 58), hint, font=SMALL, fill=_SUB)
        draw.rectangle([8, 76, _IW - 8, 78], fill=_SEP)

        # ── BLOKLAR ──────────────────────────────────────────────────
        draw.rectangle([8, 82, _IW - 8, 104], fill=_SEC)
        draw.text((12, 84), 'B L O K L A R', font=HEAD, fill=_HDR_B)

        row_h  = 52
        col_w  = (_IW - 24) // 2
        blk_y0 = 108

        for i in range(8):
            bid = i + 1
            col = i // 4
            row = i % 4
            x0  = 8 + col * (col_w + 8)
            y   = blk_y0 + row * row_h
            x1  = x0 + col_w

            if row % 2 == 0:
                draw.rectangle([x0, y, x1, y + row_h - 2], fill=_ROWD)

            bclr  = _BLOCK_COLS.get(bid, (128, 128, 128))
            bname = _BLOCK_NAMES.get(bid, f'Blok {bid}')
            count = self.block_counts.get(bid, 0)
            clr   = _WHITE if count > 0 else _DIM

            draw.rectangle([x0 + 8, y + 16, x0 + 30, y + 38], fill=bclr)
            draw.text((x0 + 36, y + 16), bname, font=BODY, fill=clr)
            ctext = str(count)
            draw.text((x1 - _rw(draw, ctext, HEAD) - 8, y + 15), ctext, font=HEAD, fill=clr)

        blocks_end = blk_y0 + 4 * row_h  # ~316

        draw.rectangle([8, blocks_end + 2, _IW - 8, blocks_end + 4], fill=_SEP)

        # ── ESYALAR ───────────────────────────────────────────────────
        item_hdr_y = blocks_end + 8
        draw.rectangle([8, item_hdr_y, _IW - 8, item_hdr_y + 22], fill=_SEC)
        draw.text((12, item_hdr_y + 2), 'E S Y A L A R', font=HEAD, fill=_HDR_I)

        item_y0 = item_hdr_y + 28
        item_h  = 48

        for j, key in enumerate(_ITEM_KEYS):
            y     = item_y0 + j * item_h
            iclr  = _ITEM_COLS.get(key, _WHITE)
            name  = _ITEM_NAMES.get(key, key)
            count = self.item_counts.get(key, 0)
            clr   = iclr if count > 0 else _DIM
            draw.ellipse([12, y + 14, 32, y + 34], fill=iclr)
            draw.text((40, y + 14), name, font=BODY, fill=clr)
            ctext = str(count)
            draw.text((310 - _rw(draw, ctext, HEAD), y + 14), ctext, font=HEAD, fill=clr)

        items_end = item_y0 + len(_ITEM_KEYS) * item_h  # ~460

        # ── CANTA (Gear Bag) ──────────────────────────────────────────
        draw.rectangle([8, items_end + 2, _IW - 8, items_end + 4], fill=_SEP)

        gear_hdr_y = items_end + 8
        draw.rectangle([8, gear_hdr_y, _IW - 8, gear_hdr_y + 22], fill=_SEC)
        draw.text((12, gear_hdr_y + 2), 'E K I P M A N  C A N T A S I', font=HEAD, fill=_HDR_G)

        gear_y0 = gear_hdr_y + 28
        gear_h  = 38

        gear_bag = self.equipment.gear_bag if self.equipment else []

        if gear_bag:
            for idx, item in enumerate(gear_bag[:8]):
                y   = gear_y0 + idx * gear_h
                bg  = _SEC if idx % 2 == 0 else _BG
                draw.rectangle([8, y, _IW - 8, y + gear_h - 2], fill=bg)
                rc  = _RARITY_C.get(item.get('rarity', 'common'), _WHITE)
                draw.text((14, y + 8), item['name'], font=BODY, fill=rc)
                # Stats on right
                parts = []
                if item['dmg']: parts.append(f'+{item["dmg"]}A')
                if item['def']: parts.append(f'+{item["def"]}D')
                if item['spd']: parts.append(f'+{item["spd"]}H')
                stat_str = '  '.join(parts)
                sw = _rw(draw, stat_str, SMALL)
                draw.text((_IW - sw - 14, y + 12), stat_str, font=SMALL,
                          fill=(200, 200, 100))
            if len(gear_bag) > 8:
                extra_y = gear_y0 + 8 * gear_h + 4
                msg = f'+{len(gear_bag) - 8} daha  —  [C] ile yonet'
                draw.text((_cx(draw, msg, SMALL), extra_y), msg,
                          font=SMALL, fill=_DIM)
        else:
            draw.text((_cx(draw, '— Cantada ekipman yok —', BODY), gear_y0 + 8),
                      '— Cantada ekipman yok —', font=BODY, fill=_DIM)

        # ── Footer ────────────────────────────────────────────────────
        draw.rectangle([8, _IH - 28, _IW - 8, _IH - 26], fill=_SEP)
        ft = '[C] Karakter ekrani  |  [E] Crafting'
        draw.text((_cx(draw, ft, SMALL), _IH - 22), ft, font=SMALL, fill=_DIM)

        self._panel.texture = Texture(img)

    # ------------------------------------------------------------------
    def toggle(self):
        self.is_open = not self.is_open
        if self.is_open:
            self._render()
            self._panel.enabled = True
        else:
            self._panel.enabled = False

    def refresh(self):
        if self.is_open:
            self._render()

    # ------------------------------------------------------------------
    def input(self, key):
        if key == 'i':
            self.toggle()
        elif self.is_open and key == 'escape':
            self.toggle()
