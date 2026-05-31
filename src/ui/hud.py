"""HUD — all colors use 0-1 float range (Ursina 8.3.0 compatibility)."""
from ursina import Entity, Text, color, camera, destroy


class HUD(Entity):
    def __init__(self):
        super().__init__(parent=camera.ui)

        # ── Crosshair ────────────────────────────────────────────────
        Text(parent=self, text='+', origin=(0, 0), scale=2, color=color.white)

        # ── HP bar ───────────────────────────────────────────────────
        # Label
        Text(parent=self, text='HP', origin=(0.5, 0),
             position=(-0.178, -0.340), scale=1.0,
             color=color.rgba(1.0, 0.85, 0.85, 0.90))

        # Background
        Entity(parent=self, model='quad', scale=(0.30, 0.026),
               position=(0.025, -0.340),
               color=color.rgba(0.06, 0.06, 0.08, 0.88))

        # Fill (scale_x driven by set_health)
        self._hp_fill = Entity(
            parent=self, model='quad', scale=(0.30, 0.026),
            position=(-0.125, -0.340), origin=(-0.5, 0),
            color=color.lime)

        # HP numbers (e.g. "100/100")
        self._hp_text = Text(
            parent=self, text='100/100', origin=(0, 0),
            position=(0.025, -0.340), scale=0.80,
            color=color.rgba(1.0, 1.0, 1.0, 0.90))

        # ── Q ability bar ─────────────────────────────────────────────
        Entity(parent=self, model='quad', scale=(0.28, 0.015),
               position=(0, -0.376),
               color=color.rgba(0.07, 0.07, 0.22, 0.85))
        self._ab_fill = Entity(
            parent=self, model='quad', scale=(0, 0.015),
            position=(-0.14, -0.376), origin=(-0.5, 0),
            color=color.rgba(0.39, 0.55, 1.00, 0.85))
        self._ab_label = Text(
            parent=self, text='', origin=(0.5, 0),
            position=(0.14, -0.376), scale=0.80,
            color=color.rgba(0.65, 0.80, 1.0, 0.90))

        # ── R ability bar ─────────────────────────────────────────────
        Entity(parent=self, model='quad', scale=(0.28, 0.015),
               position=(0, -0.400),
               color=color.rgba(0.22, 0.08, 0.04, 0.85))
        self._ab2_fill = Entity(
            parent=self, model='quad', scale=(0, 0.015),
            position=(-0.14, -0.400), origin=(-0.5, 0),
            color=color.rgba(1.00, 0.59, 0.12, 0.85))
        self._ab2_label = Text(
            parent=self, text='', origin=(0.5, 0),
            position=(0.14, -0.400), scale=0.80,
            color=color.rgba(1.0, 0.80, 0.40, 0.90))

        # ── XP bar ───────────────────────────────────────────────────
        Entity(parent=self, model='quad', scale=(0.28, 0.009),
               position=(0, -0.420),
               color=color.rgba(0.06, 0.06, 0.08, 0.80))
        self._xp_fill = Entity(
            parent=self, model='quad', scale=(0, 0.009),
            position=(-0.14, -0.420), origin=(-0.5, 0),
            color=color.rgba(0.20, 0.71, 1.00, 0.85))

        # ── Class + Level labels (top center) ─────────────────────────
        self._class_label = Text(
            parent=self, text='', origin=(0, 0.5),
            position=(0, 0.462), scale=1.20,
            color=color.rgba(0.86, 0.71, 1.00, 0.82))
        self._lv_label = Text(
            parent=self, text='Lv. 1', origin=(-0.5, 0.5),
            position=(0.175, 0.462), scale=1.00,
            color=color.rgba(0.31, 0.86, 1.00, 0.88))

        # ── Item / equipment text (top-left) ──────────────────────────
        self._item_text  = None
        self._equip_text = None

        # ── Hints (bottom-right) ──────────────────────────────────────
        # camera.ui x-range is ±0.5*aspect (~±0.8 at 16:10) — keep inside it
        Text(parent=self,
             text='[I] Envanter  [C] Karakter  [T] Tuccar\n'
                  '[H] Iksir  [F] Saldiri  [Q] Yetenek1  [R] Yetenek2\n'
                  '[Shift] Kosma  [9] Mesale  [G] Portal  [F5] Kaydet',
             origin=(0.5, 0), position=(0.77, -0.44),
             scale=0.70, color=color.rgba(0.78, 0.78, 0.78, 0.85))

    # ──────────────────────────────────────────────────────────────────
    def set_health(self, hp: float, max_hp: float = 100) -> None:
        ratio = max(0.0, min(1.0, hp / max_hp if max_hp > 0 else 0))
        self._hp_fill.scale_x = 0.30 * ratio
        self._hp_fill.color = (
            color.rgba(0.20, 0.90, 0.25, 1) if ratio > 0.55 else
            color.rgba(0.95, 0.85, 0.10, 1) if ratio > 0.28 else
            color.rgba(0.95, 0.18, 0.14, 1)
        )
        self._hp_text.text = f'{int(hp)}/{int(max_hp)}'

    def set_xp(self, ratio: float, level: int) -> None:
        self._xp_fill.scale_x = 0.28 * max(0.0, min(1.0, ratio))
        self._lv_label.text = f'Lv. {level}'

    def update_ability(self, ability_name: str, cd_ratio: float) -> None:
        self._ab_fill.scale_x = 0.28 * max(0.0, min(1.0, cd_ratio))
        if cd_ratio > 0:
            self._ab_label.text = f'[Q] {ability_name} ({cd_ratio*100:.0f}%)'
        else:
            self._ab_label.text = f'[Q] {ability_name}  HAZIR'

    def update_ability2(self, ability_name: str, cd_ratio: float) -> None:
        self._ab2_fill.scale_x = 0.28 * max(0.0, min(1.0, cd_ratio))
        if cd_ratio > 0:
            self._ab2_label.text = f'[R] {ability_name} ({cd_ratio*100:.0f}%)'
        else:
            self._ab2_label.text = f'[R] {ability_name}  HAZIR'

    def set_class_label(self, label: str, rgb: tuple) -> None:
        self._class_label.text  = label
        self._class_label.color = color.rgba(rgb[0]/255, rgb[1]/255, rgb[2]/255, 0.85)

    def update_items(self, item_counts: dict) -> None:
        _ICONS = {'coin': 'o', 'slime_gel': '*', 'health_potion': '+'}
        _NAMES = {'coin': 'Coin', 'slime_gel': 'Jel', 'health_potion': 'Iksir'}
        SHOW   = {'coin', 'slime_gel', 'health_potion'}
        lines  = [f'{_ICONS.get(k,"?")} {_NAMES.get(k,k)}: {v}'
                  for k, v in item_counts.items() if v > 0 and k in SHOW]
        if self._item_text:
            destroy(self._item_text)
        self._item_text = Text(
            parent=self, text='\n'.join(lines),
            origin=(-0.5, 0.5), position=(-0.78, 0.46),
            scale=1.05, color=color.rgba(1.0, 0.95, 0.20, 0.95),
        ) if lines else None

    def update_equipment(self, equipment) -> None:
        if self._equip_text:
            destroy(self._equip_text)
        lines = equipment.summary_lines()
        self._equip_text = Text(
            parent=self, text='\n'.join(lines),
            origin=(-0.5, 0.5), position=(-0.78, 0.36),
            scale=0.88, color=color.rgba(0.80, 0.85, 1.00, 0.95),
        ) if lines else None
