"""Hotbar — 9 slots (blocks 1-8 + torch 17). All colors use 0-1 float range."""
from ursina import Entity, Text, color, camera, destroy

_BLOCK_NAMES = {
    1: 'Cim', 2: 'Toprak', 3: 'Tas', 4: 'Tahta',
    5: 'Cilali Tas', 6: 'Tahta Plaka', 7: 'Camur', 8: 'Altin',
    17: 'Mesale',
}

# 0-1 block icon colors
_BLOCK_COLORS = {
    1:  color.rgba(0.271, 0.600, 0.141, 1),   # grass
    2:  color.rgba(0.451, 0.282, 0.078, 1),   # dirt
    3:  color.rgba(0.502, 0.502, 0.502, 1),   # stone
    4:  color.rgba(0.400, 0.251, 0.102, 1),   # wood
    5:  color.rgba(0.722, 0.722, 0.761, 1),   # smooth stone
    6:  color.rgba(0.851, 0.722, 0.451, 1),   # planks
    7:  color.rgba(0.349, 0.278, 0.180, 1),   # mud
    8:  color.rgba(0.949, 0.820, 0.098, 1),   # gold
    17: color.rgba(0.949, 0.784, 0.196, 1),   # torch
}

SLOTS     = list(range(1, 9)) + [17]
_SLOT_IDX = {bid: i for i, bid in enumerate(SLOTS)}

SLOT_W = 0.063
SLOT_H = 0.063
GAP    = 0.007
TOTAL  = len(SLOTS) * (SLOT_W + GAP) - GAP
SX     = -TOTAL / 2 + SLOT_W / 2
BOT_Y  = -0.415

_C_BORDER = color.rgba(0.24, 0.26, 0.35, 0.95)
_C_EMPTY  = color.rgba(0.08, 0.09, 0.14, 0.92)
_C_FULL   = color.rgba(0.16, 0.20, 0.31, 0.92)
_C_SEL    = color.rgba(0.82, 0.76, 0.12, 0.96)
_C_ICON_DIM = color.rgba(0.18, 0.18, 0.20, 0.60)
_C_CNT_FULL = color.rgba(1.00, 0.95, 0.28, 0.97)
_C_CNT_ZERO = color.rgba(0.50, 0.50, 0.50, 0.42)
_C_NUM      = color.rgba(0.75, 0.75, 0.80, 0.55)


class Hotbar(Entity):
    def __init__(self, block_counts: dict):
        super().__init__(parent=camera.ui)
        self.block_counts = block_counts
        self.selected     = 1
        self._bgs   = {}
        self._icons = {}
        self._cnts  = {}

        # Block name label centered above hotbar
        self._name_lbl = Text(
            parent=self, text='',
            origin=(0, -0.5),
            position=(0, BOT_Y + SLOT_H * 0.76),
            scale=1.05,
            color=color.rgba(1.0, 0.96, 0.55, 0.96))

        for i, bid in enumerate(SLOTS):
            x = SX + i * (SLOT_W + GAP)

            # Layer 1: border (slightly larger, rendered first → behind)
            Entity(parent=self, model='quad', color=_C_BORDER,
                   scale=(SLOT_W + 0.006, SLOT_H + 0.006),
                   position=(x, BOT_Y))

            # Layer 2: slot background
            bg = Entity(parent=self, model='quad', color=_C_EMPTY,
                        scale=(SLOT_W, SLOT_H), position=(x, BOT_Y))
            self._bgs[bid] = bg

            # Layer 3: block color icon
            icon = Entity(parent=self, model='quad',
                          color=_BLOCK_COLORS.get(bid, color.gray),
                          scale=(SLOT_W * 0.58, SLOT_H * 0.58),
                          position=(x, BOT_Y + SLOT_H * 0.04))
            self._icons[bid] = icon

            # Layer 4a: key number (top-left)
            key_lbl = '9' if bid == 17 else str(bid)
            Text(parent=self, text=key_lbl, origin=(-0.5, 0.5),
                 scale=0.62,
                 position=(x - SLOT_W * 0.44, BOT_Y + SLOT_H * 0.42),
                 color=_C_NUM)

            # Layer 4b: count number (bottom-right) — created LAST → renders on top
            cnt = Text(parent=self, text='0', origin=(0.5, -0.5),
                       scale=1.40,
                       position=(x + SLOT_W * 0.42, BOT_Y - SLOT_H * 0.35),
                       color=_C_CNT_ZERO)
            self._cnts[bid] = cnt

        self.select(self.selected)

    # ──────────────────────────────────────────────────────────────────
    def _slot_x(self, bid: int) -> float:
        return SX + _SLOT_IDX[bid] * (SLOT_W + GAP)

    def _refresh_slot(self, bid: int):
        count = self.block_counts.get(bid, 0)

        # Update count text in-place (no destroy/recreate → avoids every-frame flicker)
        cnt = self._cnts[bid]
        cnt.text  = str(count)
        cnt.color = _C_CNT_FULL if count > 0 else _C_CNT_ZERO

        # Update icon brightness
        self._icons[bid].color = (_BLOCK_COLORS.get(bid, color.gray)
                                  if count > 0 else _C_ICON_DIM)

        # Update background (don't overwrite the selected slot's golden color)
        if bid != self.selected:
            self._bgs[bid].color = _C_FULL if count > 0 else _C_EMPTY

    def update(self):
        for bid in SLOTS:
            self._refresh_slot(bid)
        # Keep tooltip count up-to-date
        if self.selected in _BLOCK_NAMES:
            cnt = self.block_counts.get(self.selected, 0)
            name = _BLOCK_NAMES.get(self.selected, '')
            self._name_lbl.text = f'{name}   x{cnt}'

    # ──────────────────────────────────────────────────────────────────
    def select(self, block_id: int):
        if block_id not in self._bgs:
            return
        for bid, bg in self._bgs.items():
            count = self.block_counts.get(bid, 0)
            bg.color = (_C_SEL if bid == block_id
                        else (_C_FULL if count > 0 else _C_EMPTY))
        self.selected = block_id

        # Update tooltip: "Cim  x10" above the selected slot
        count = self.block_counts.get(block_id, 0)
        name  = _BLOCK_NAMES.get(block_id, f'Blok {block_id}')
        self._name_lbl.text = f'{name}   x{count}'
        self._name_lbl.x    = self._slot_x(block_id)

    def update_count(self, block_id: int):
        if block_id in _SLOT_IDX:
            self._refresh_slot(block_id)
