from PIL import Image, ImageDraw
from ursina import Entity, camera, Texture

from systems.crafting import RECIPES, CraftingSystem
from ui._fonts import TITLE, HEAD, BODY, SMALL

_W,  _H  = 0.70, 0.92
_IW, _IH = 512, 670

_BG   = (18,  18,  32)
_ACC  = (80,  60,  180)
_SEP  = (60,  50,  120)
_ROW  = (25,  25,  42)
_TC   = (255, 220, 0)
_HDR  = (140, 140, 200)
_CAN  = (255, 255, 255)
_CANT = (200, 60,  60)
_KEY  = (255, 220, 0)
_KEYD = (130, 50,  50)
_SUB  = (160, 160, 180)
_HINT = (120, 120, 140)


def _cx(draw, text, font):
    bb = draw.textbbox((0, 0), text, font=font)
    return (_IW - (bb[2] - bb[0])) // 2


class CraftingUI(Entity):
    def __init__(self, crafting: CraftingSystem, hotbar=None, hud=None):
        super().__init__(parent=camera.ui)
        self.crafting = crafting
        self.hotbar   = hotbar
        self.hud      = hud
        self.is_open  = False

        self._panel = Entity(parent=camera.ui, model='quad', scale=(_W, _H))
        self._panel.enabled = False

    # ------------------------------------------------------------------
    def _render(self):
        img  = Image.new('RGB', (_IW, _IH), _BG)
        draw = ImageDraw.Draw(img)

        draw.rectangle([0, 0, _IW, 5],        fill=_ACC)
        draw.rectangle([0, _IH - 5, _IW, _IH], fill=_ACC)

        title = 'CRAFTING MASASI'
        draw.text((_cx(draw, title, TITLE), 14), title, font=TITLE, fill=_TC)

        hint = '[E] kapat     [1-9,0] ure'
        draw.text((_cx(draw, hint, BODY), 58), hint, font=BODY, fill=_SUB)

        draw.rectangle([8, 84, _IW - 8, 86], fill=_SEP)

        draw.text((12,  91), 'MALZEMELER', font=HEAD, fill=_HDR)
        draw.text((270, 91), 'URETIM',     font=HEAD, fill=_HDR)
        draw.text((460, 91), 'TUS',        font=HEAD, fill=_HDR)

        keys_list = list('1234567890')
        row_y = 115
        row_h = 52

        for i, recipe in enumerate(RECIPES):
            can = self.crafting.can_craft(recipe)
            if i % 2 == 0:
                draw.rectangle([8, row_y, _IW - 8, row_y + row_h - 2], fill=_ROW)

            ing = CraftingSystem.format_ingredients(recipe)
            res = f'{recipe["result_count"]}x {recipe["name"]}'
            key = f'[{keys_list[i]}]' if i < len(keys_list) else ''
            c   = _CAN  if can else _CANT
            kc  = _KEY  if can else _KEYD
            ty  = row_y + 16

            draw.text((12,  ty), ing, font=BODY, fill=c)
            draw.text((270, ty), res, font=BODY, fill=c)
            draw.text((460, ty), key, font=HEAD, fill=kc)

            row_y += row_h

        draw.rectangle([8, _IH - 28, _IW - 8, _IH - 26], fill=_SEP)
        ft = 'Kirmizi = malzeme yetersiz'
        draw.text((_cx(draw, ft, SMALL), _IH - 23), ft, font=SMALL, fill=_HINT)

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
        if key == 'e':
            self.toggle()
            return
        if not self.is_open:
            return
        if key == 'escape':
            self.toggle()
            return
        keys = list('1234567890')
        if key in keys:
            idx = keys.index(key)
            if idx < len(RECIPES):
                if self.crafting.craft(RECIPES[idx]):
                    if self.hud:
                        self.hud.update_items(self.crafting.item_counts)
                    self._render()
