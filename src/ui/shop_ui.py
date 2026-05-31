from PIL import Image, ImageDraw
from ursina import Entity, Text, color as uc, camera, Texture, destroy

from systems.shop import BUY_ITEMS, SELL_ITEMS, ShopSystem
from ui._fonts import TITLE, HEAD, BODY, SMALL

_W,        _H   = 0.74, 0.88
_IW,       _IH  = 512, 608
_PROXIMITY       = 5.0
_SELL_KEYS       = 'abcde'

_BG    = (10,  22,  14)
_ACC   = (20,  160, 60)
_SEP   = (20,  100, 40)
_BUY_S = (15,  35,  20)
_SEL_S = (35,  15,  15)
_ROWD  = (14,  28,  18)
_ROWDS = (28,  14,  14)
_TC    = (80,  230, 100)
_HDR_B = (100, 220, 130)
_HDR_S = (220, 120, 100)
_SUB   = (140, 160, 140)
_WHITE = (240, 240, 240)
_DIM   = (100, 100, 100)
_GOLD  = (230, 200, 60)
_GOLDM = (90,  90,  50)


def _cx(draw, text, font):
    bb = draw.textbbox((0, 0), text, font=font)
    return (_IW - (bb[2] - bb[0])) // 2


def _rw(draw, text, font):
    bb = draw.textbbox((0, 0), text, font=font)
    return bb[2] - bb[0]


class ShopUI(Entity):
    def __init__(self, player, merchant, shop: ShopSystem):
        super().__init__(parent=camera.ui)
        self.player     = player
        self.merchant   = merchant
        self.shop       = shop
        self.is_open    = False
        self._near_prev = False
        self._hint      = None

        self._panel = Entity(parent=camera.ui, model='quad', scale=(_W, _H))
        self._panel.enabled = False

    # ------------------------------------------------------------------
    def _dist(self) -> float:
        d = self.player.position - self.merchant.position
        return (d.x * d.x + d.y * d.y + d.z * d.z) ** 0.5

    def _render(self):
        coins = self.shop.coins()
        img   = Image.new('RGB', (_IW, _IH), _BG)
        draw  = ImageDraw.Draw(img)

        draw.rectangle([0, 0, _IW, 5],          fill=_ACC)
        draw.rectangle([0, _IH - 5, _IW, _IH],  fill=_ACC)

        title = 'MAGAZA'
        draw.text((_cx(draw, title, TITLE), 12), title, font=TITLE, fill=_TC)

        hint = '[T / Esc] kapat'
        draw.text((12, 56), hint, font=SMALL, fill=_SUB)
        coin_str = f'Sikke: {coins}'
        draw.text((_IW - _rw(draw, coin_str, HEAD) - 12, 53), coin_str, font=HEAD, fill=_GOLD)

        draw.rectangle([8, 76, _IW - 8, 78], fill=_SEP)

        # ── AL section ──
        draw.rectangle([8, 82, _IW - 8, 102], fill=_BUY_S)
        draw.text((12, 83), 'A L   [1-9]', font=HEAD, fill=_HDR_B)

        row_h  = 32
        buy_y0 = 106

        for i, item in enumerate(BUY_ITEMS):
            can = self.shop.can_buy(item)
            y   = buy_y0 + i * row_h
            if i % 2 == 0:
                draw.rectangle([8, y, _IW - 8, y + row_h - 2], fill=_ROWD)
            nc = _WHITE if can else _DIM
            pc = _GOLD  if can else _GOLDM
            draw.text((12, y + 7), f'[{i + 1}]  {item["name"]}', font=BODY, fill=nc)
            ps = f'{item["price"]} coin'
            draw.text((_IW - _rw(draw, ps, BODY) - 12, y + 7), ps, font=BODY, fill=pc)

        sep_y = buy_y0 + len(BUY_ITEMS) * row_h + 2
        draw.rectangle([8, sep_y, _IW - 8, sep_y + 2], fill=_SEP)

        # ── SAT section ──
        sell_hdr_y = sep_y + 6
        draw.rectangle([8, sell_hdr_y, _IW - 8, sell_hdr_y + 20], fill=_SEL_S)
        draw.text((12, sell_hdr_y + 1), 'S A T   [A-E]', font=HEAD, fill=_HDR_S)

        sell_y0 = sell_hdr_y + 26
        sell_items = SELL_ITEMS[:5]

        for j, item in enumerate(sell_items):
            can = self.shop.can_sell(item)
            y   = sell_y0 + j * row_h
            if j % 2 == 0:
                draw.rectangle([8, y, _IW - 8, y + row_h - 2], fill=_ROWDS)
            nc = _WHITE if can else _DIM
            rc = _GOLD  if can else _GOLDM
            draw.text((12, y + 7), f'[{_SELL_KEYS[j].upper()}]  {item["name"]}', font=BODY, fill=nc)
            rs = f'+{item["reward"]} coin'
            draw.text((_IW - _rw(draw, rs, BODY) - 12, y + 7), rs, font=BODY, fill=rc)

        draw.rectangle([8, _IH - 5, _IW, _IH], fill=_ACC)

        self._panel.texture = Texture(img)

    # ------------------------------------------------------------------
    def update(self):
        near = self._dist() < _PROXIMITY
        if near and not self._near_prev:
            self._hint = Text(
                parent=camera.ui, text='[T] Tuccar ile konus',
                origin=(0, 0), position=(0, -0.20),
                scale=1.2, color=uc.yellow,
            )
        elif not near and self._near_prev:
            if self._hint:
                destroy(self._hint)
                self._hint = None
            if self.is_open:
                self._do_close()
        self._near_prev = near

    def toggle(self):
        if self.is_open:
            self._do_close()
        else:
            self._do_open()

    def _do_open(self):
        self.is_open = True
        if self._hint:
            destroy(self._hint)
            self._hint = None
        self._render()
        self._panel.enabled = True

    def _do_close(self):
        self.is_open = False
        self._panel.enabled = False

    # ------------------------------------------------------------------
    def input(self, key):
        if key == 't':
            if self._dist() < _PROXIMITY or self.is_open:
                self.toggle()
            return
        if not self.is_open:
            return
        if key == 'escape':
            self._do_close()
            return
        if key in '123456789':
            idx = int(key) - 1
            if idx < len(BUY_ITEMS):
                self.shop.buy(BUY_ITEMS[idx])
                self._render()
            return
        if key in _SELL_KEYS:
            idx = _SELL_KEYS.index(key)
            if idx < len(SELL_ITEMS):
                self.shop.sell(SELL_ITEMS[idx])
                self._render()
