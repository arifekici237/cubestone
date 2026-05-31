"""Character UI — PIL rendered, right-click equip/unequip, X = sell."""
from PIL import Image, ImageDraw
from ursina import Entity, camera, Texture, mouse

from ui._fonts import TITLE, HEAD, BODY, SMALL

# ── Panel dimensions ─────────────────────────────────────────────────────────
_W,  _H  = 0.74, 0.82
_IW, _IH = 640,  560

# ── Colors ───────────────────────────────────────────────────────────────────
_BG       = (7,   9,  22)
_TITLEBAR = (14,  17, 40)
_SEP_C    = (44,  48, 76)
_SLOT_OUT = (26,  30, 56)
_SLOT_IN  = (8,   10, 24)
_INFO_BG  = (11,  13, 29)
_TC       = (200, 152, 255)
_HINT_C   = (70,  70, 105)
_EQ_HDR   = (100, 170, 255)
_BAG_HDR  = (175, 95,  245)
_LBL_C    = (105, 105, 140)
_PR_C     = (255, 215, 0)
_SEL_C    = (220, 175, 40)
_ITEM_C   = (235, 238, 248)
_STAT_C   = (200, 200, 100)
_ICON_DIM = (60,  65,  95)
_SELL_C   = (255, 100, 100)
_GOLD_C   = (255, 215, 0)

_RC = {
    'common':   (170, 170, 170),
    'uncommon': (60,  210, 60),
    'rare':     (70,  130, 255),
    'epic':     (195, 50,  255),
}
_RNAME = {
    'common':   'Siradan',
    'uncommon': 'Olagandir',
    'rare':     'Nadir',
    'epic':     'Destansi',
}
_SELL_PRICE = {'common': 2, 'uncommon': 6, 'rare': 15, 'epic': 30}
_SLOT_LBL   = {'weapon': 'Silah', 'armor': 'Zirh', 'boots': 'Bot', 'ring': 'Yuzuk'}
_EQUIP_SL   = ('weapon', 'armor', 'boots', 'ring')
_BAG_SIZE   = 8

# ── Equip slot layout ────────────────────────────────────────────────────────
_EQ_R   = 50
_EQ_PIX = {
    'weapon': (100, 190),
    'armor':  (216, 190),
    'boots':  (100, 308),
    'ring':   (216, 308),
}

# ── Bag slot layout ──────────────────────────────────────────────────────────
_BAG_S   = 68
_BAG_GAP = 7
_BAG_X0  = 333
_BAG_Y0  = 104

# ── Info panel ───────────────────────────────────────────────────────────────
_INFO_SEP = 420
_INFO_Y   = 422


def _bag_rect(i):
    col, row = i % 4, i // 4
    x = _BAG_X0 + col * (_BAG_S + _BAG_GAP)
    y = _BAG_Y0 + row * (_BAG_S + _BAG_GAP)
    return x, y, x + _BAG_S, y + _BAG_S


def _cx(draw, text, font):
    bb = draw.textbbox((0, 0), text, font=font)
    return (_IW - (bb[2] - bb[0])) // 2


def _cx2(draw, text, font, x0, x1):
    bb = draw.textbbox((0, 0), text, font=font)
    return x0 + (x1 - x0 - (bb[2] - bb[0])) // 2


def _stats(item):
    if not item:
        return ''
    parts = [f'+{item[k]}{s}' for k, s in (('dmg', 'A'), ('def', 'D'), ('spd', 'H'))
             if item.get(k)]
    return '  '.join(parts)


class CharacterUI(Entity):
    def __init__(self, equipment, player_state, item_counts):
        super().__init__(parent=camera.ui)
        self.equipment    = equipment
        self.player_state = player_state
        self.item_counts  = item_counts
        self.is_open      = False
        self._selected    = None  # slot_id str or None
        self._page        = 0     # current bag page

        self._panel = Entity(parent=camera.ui, model='quad', scale=(_W, _H))
        self._panel.enabled = False

    # ── PIL render ───────────────────────────────────────────────────────
    def _render(self):
        eq       = self.equipment
        gear_bag = eq.gear_bag
        total    = len(gear_bag)
        pages    = max(1, (total + _BAG_SIZE - 1) // _BAG_SIZE)
        self._page = min(self._page, pages - 1)
        page_items = gear_bag[self._page * _BAG_SIZE: (self._page + 1) * _BAG_SIZE]

        img  = Image.new('RGB', (_IW, _IH), _BG)
        draw = ImageDraw.Draw(img)

        # Title bar
        draw.rectangle([0, 0, _IW, 48], fill=_TITLEBAR)
        title = 'KARAKTER EKIPMANI'
        draw.text((_cx(draw, title, TITLE), 7), title, font=TITLE, fill=_TC)
        hint = '[C] kapat  |  Sag tikla: giy/cikar  |  [X] sat'
        draw.text((_cx(draw, hint, SMALL), 53), hint, font=SMALL, fill=_HINT_C)

        draw.rectangle([0, 73, _IW, 75], fill=_SEP_C)

        # ── LEFT: Equipped ────────────────────────────────────────────
        eq_hdr = '== TAKILI =='
        draw.text((_cx2(draw, eq_hdr, HEAD, 0, 310), 79),
                  eq_hdr, font=HEAD, fill=_EQ_HDR)

        for stype in _EQUIP_SL:
            cx, cy = _EQ_PIX[stype]
            item   = eq._equipped.get(stype)
            sel    = (self._selected == f'equip_{stype}')
            r      = _EQ_R

            if sel:
                out_c = _SEL_C
            elif item:
                out_c = _RC.get(item.get('rarity', 'common'), (170, 170, 170))
            else:
                out_c = _SLOT_OUT
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=out_c)

            ir = int(r * 0.82)
            draw.ellipse([cx - ir, cy - ir, cx + ir, cy + ir], fill=_SLOT_IN)

            if item:
                name = item['name'][:6]
                tx = _cx2(draw, name, SMALL, cx - r, cx + r)
                draw.text((tx, cy - 8), name, font=SMALL, fill=_ITEM_C)
            else:
                icon = {'weapon': 'S', 'armor': 'Z', 'boots': 'B', 'ring': 'Y'}[stype]
                tx = _cx2(draw, icon, HEAD, cx - r, cx + r)
                draw.text((tx, cy - 11), icon, font=HEAD, fill=_ICON_DIM)

            lbl = _SLOT_LBL[stype]
            lx  = _cx2(draw, lbl, SMALL, cx - r, cx + r)
            draw.text((lx, cy + r + 5), lbl, font=SMALL, fill=_LBL_C)

        pr_txt = f'PR: {eq.power_rating()}'
        draw.text((_cx2(draw, pr_txt, HEAD, 0, 310), 382),
                  pr_txt, font=HEAD, fill=_PR_C)

        # ── Vertical divider ─────────────────────────────────────────
        draw.rectangle([311, 76, 313, _INFO_SEP], fill=_SEP_C)

        # ── RIGHT: Bag ────────────────────────────────────────────────
        # Header with page info
        bag_hdr = f'== CANTA ({total} esya) =='
        draw.text((_cx2(draw, bag_hdr, HEAD, 320, _IW), 79),
                  bag_hdr, font=HEAD, fill=_BAG_HDR)

        # Page arrows
        if pages > 1:
            page_txt = f'< Sayfa {self._page + 1}/{pages} >'
            draw.text((_cx2(draw, page_txt, SMALL, 320, _IW), 258),
                      page_txt, font=SMALL, fill=_LBL_C)
            nav_hint = '[Sol/Sag ok] sayfa degistir'
            draw.text((_cx2(draw, nav_hint, SMALL, 320, _IW), 276),
                      nav_hint, font=SMALL, fill=_ICON_DIM)

        for i in range(_BAG_SIZE):
            x0, y0, x1, y1 = _bag_rect(i)
            item = page_items[i] if i < len(page_items) else None
            # Global bag index for this slot
            global_idx = self._page * _BAG_SIZE + i
            sel  = (self._selected == f'bag_{i}')

            if sel:
                out_c = _SEL_C
            elif item:
                out_c = _RC.get(item.get('rarity', 'common'), (170, 170, 170))
            else:
                out_c = _SLOT_OUT
            draw.rectangle([x0, y0, x1, y1], fill=out_c)

            pad = int(_BAG_S * 0.09)
            draw.rectangle([x0 + pad, y0 + pad, x1 - pad, y1 - pad], fill=_SLOT_IN)

            if item:
                name = item['name'][:6]
                ty = y0 + (_BAG_S - 14) // 2 - 7
                draw.text((_cx2(draw, name, SMALL, x0, x1), ty),
                          name, font=SMALL, fill=_ITEM_C)
            else:
                num = str(global_idx + 1) if global_idx < total else ''
                if num:
                    ty = y0 + (_BAG_S - 22) // 2
                    draw.text((_cx2(draw, num, HEAD, x0, x1), ty),
                              num, font=HEAD, fill=_ICON_DIM)

        # ── Info panel ────────────────────────────────────────────────
        draw.rectangle([0, _INFO_SEP, _IW, _INFO_SEP + 2], fill=_SEP_C)
        draw.rectangle([0, _INFO_SEP + 2, _IW, _IH], fill=_INFO_BG)

        item = self._get_selected_item()
        if item:
            rc = _RC.get(item.get('rarity', 'common'), (170, 170, 170))
            rn = _RNAME.get(item.get('rarity', 'common'), '')
            name_str = f'{item["name"]}  [{rn}]'
            draw.text((_cx(draw, name_str, HEAD), _INFO_Y + 10),
                      name_str, font=HEAD, fill=rc)
            st = _stats(item)
            draw.text((_cx(draw, st or '--', BODY), _INFO_Y + 40),
                      st or '--', font=BODY, fill=_STAT_C)
            # Show sell price for bag items
            if self._selected and self._selected.startswith('bag_'):
                price = _SELL_PRICE.get(item.get('rarity', 'common'), 2)
                sell_str = f'[X] Sat  ->  +{price} coin'
                draw.text((_cx(draw, sell_str, BODY), _INFO_Y + 72),
                          sell_str, font=BODY, fill=_SELL_C)

        self._panel.texture = Texture(img)

    def _get_selected_item(self):
        if not self._selected:
            return None
        if self._selected.startswith('equip_'):
            return self.equipment._equipped.get(self._selected[6:])
        if self._selected.startswith('bag_'):
            idx = int(self._selected[4:])
            # idx is page-local; convert to global
            global_idx = self._page * _BAG_SIZE + idx
            bag = self.equipment.gear_bag
            return bag[global_idx] if global_idx < len(bag) else None
        return None

    def _get_global_bag_idx(self):
        """Return global gear_bag index of currently selected bag slot."""
        if not self._selected or not self._selected.startswith('bag_'):
            return None
        local_idx = int(self._selected[4:])
        return self._page * _BAG_SIZE + local_idx

    # ── Mouse → PIL coordinate ───────────────────────────────────────────
    def _pil_pos(self):
        mx, my = mouse.x, mouse.y
        if not (-_W / 2 <= mx <= _W / 2 and -_H / 2 <= my <= _H / 2):
            return None, None
        px = int((mx + _W / 2) / _W * _IW)
        py = int((_H / 2 - my) / _H * _IH)
        return px, py

    def _slot_at_mouse(self):
        px, py = self._pil_pos()
        if px is None:
            return None
        for stype, (cx, cy) in _EQ_PIX.items():
            if (px - cx) ** 2 + (py - cy) ** 2 <= _EQ_R ** 2:
                return f'equip_{stype}'
        for i in range(_BAG_SIZE):
            x0, y0, x1, y1 = _bag_rect(i)
            if x0 <= px <= x1 and y0 <= py <= y1:
                return f'bag_{i}'
        return None

    # ── Equip / unequip ──────────────────────────────────────────────────
    def _do_action(self, slot_id):
        eq = self.equipment
        if slot_id.startswith('equip_'):
            stype = slot_id[6:]
            if eq._equipped.get(stype):
                eq.unequip_to_bag(stype)
                if eq.on_change:
                    eq.on_change()
        else:
            global_idx = self._get_global_bag_idx()
            if global_idx is not None and global_idx < len(eq.gear_bag):
                eq.equip_from_bag(global_idx)
                if eq.on_change:
                    eq.on_change()
        self._selected = None
        self._render()

    # ── Sell ─────────────────────────────────────────────────────────────
    def _sell_selected(self):
        global_idx = self._get_global_bag_idx()
        if global_idx is None:
            return
        bag = self.equipment.gear_bag
        if global_idx >= len(bag):
            return
        item  = bag[global_idx]
        price = _SELL_PRICE.get(item.get('rarity', 'common'), 2)
        bag.pop(global_idx)
        self.item_counts['coin'] = self.item_counts.get('coin', 0) + price
        if self.equipment.on_change:
            self.equipment.on_change()
        self._selected = None
        # Stay on page but clamp if it became empty
        self._render()

    # ── Input ────────────────────────────────────────────────────────────
    def input(self, key):
        if key == 'c':
            self.toggle()
            return
        if not self.is_open:
            return
        if key == 'escape':
            self.toggle()
            return
        if key == 'right mouse down':
            slot_id = self._slot_at_mouse()
            if slot_id and slot_id.startswith('equip_'):
                # Equipped slot → unequip immediately
                self._selected = slot_id
                if self._get_selected_item():
                    self._do_action(slot_id)
                    return
                self._render()
            elif slot_id and slot_id.startswith('bag_'):
                if self._selected == slot_id:
                    # Second click on same bag slot → equip
                    if self._get_selected_item():
                        self._do_action(slot_id)
                        return
                else:
                    # First click → select and show info
                    self._selected = slot_id
                    self._render()
            else:
                self._selected = None
                self._render()
            return
        if key == 'x':
            if self._selected and self._selected.startswith('bag_'):
                self._sell_selected()
            return
        # Page navigation
        gear_bag = self.equipment.gear_bag
        pages = max(1, (len(gear_bag) + _BAG_SIZE - 1) // _BAG_SIZE)
        if key == 'right arrow' and self._page < pages - 1:
            self._page += 1
            self._selected = None
            self._render()
        elif key == 'left arrow' and self._page > 0:
            self._page -= 1
            self._selected = None
            self._render()

    # ── Open / close ─────────────────────────────────────────────────────
    def toggle(self):
        self.is_open = not self.is_open
        if self.is_open:
            mouse.locked  = False
            mouse.visible = True
            self._selected = None
            self._page     = 0
            self._render()
            self._panel.enabled = True
        else:
            mouse.locked  = True
            mouse.visible = False
            self._panel.enabled = False

    def refresh(self):
        if self.is_open:
            self._render()
