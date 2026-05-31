"""
Equipment system — gear bag (List[dict]) + 4 equipped slots.
All gear is represented as full dicts created by systems.gear.make_gear().
"""
from typing import Optional, Dict, List

from systems.gear import ITEM_BASES, EQUIPMENT_ITEMS, make_gear, calc_pr  # noqa: F401


class EquipmentSystem:
    SLOTS = ('weapon', 'armor', 'boots', 'ring')

    def __init__(self, player=None, player_state=None, sword=None, on_change=None):
        self.player       = player
        self.player_state = player_state
        self.sword        = sword
        self.on_change    = on_change

        self._equipped: Dict[str, Optional[dict]] = {s: None for s in self.SLOTS}
        self.gear_bag:  List[dict]                = []

        self._class_atk  = 0
        self._class_spd  = 1.0

    # ------------------------------------------------------------------
    # Gear bag management
    # ------------------------------------------------------------------
    def add_gear(self, base_id: str, rarity: str = 'common') -> None:
        """Create a gear instance and add it to the bag."""
        self.gear_bag.append(make_gear(base_id, rarity))
        if self.on_change:
            self.on_change()

    def add_gear_dict(self, gear: dict) -> None:
        """Add an already-created gear dict to the bag (used during load)."""
        self.gear_bag.append(gear)

    # ------------------------------------------------------------------
    # Equip / unequip
    # ------------------------------------------------------------------
    def equip_from_bag(self, idx: int) -> bool:
        """Move gear_bag[idx] into its slot; displaced item returns to bag."""
        if idx < 0 or idx >= len(self.gear_bag):
            return False
        gear = self.gear_bag.pop(idx)
        slot = gear['slot']
        old  = self._equipped.get(slot)
        if old:
            self.gear_bag.append(old)
        self._equipped[slot] = gear
        self._apply_effects()
        if self.on_change:
            self.on_change()
        return True

    def unequip_to_bag(self, slot: str) -> bool:
        """Move equipped item from slot back to bag."""
        gear = self._equipped.get(slot)
        if not gear:
            return False
        self.gear_bag.append(gear)
        self._equipped[slot] = None
        self._apply_effects()
        if self.on_change:
            self.on_change()
        return True

    def equip(self, item_id: str) -> bool:
        """Backward-compat: create common gear, equip it directly. Old slot → bag."""
        if item_id not in ITEM_BASES:
            return False
        gear = make_gear(item_id, 'common')
        slot = gear['slot']
        old  = self._equipped.get(slot)
        if old:
            self.gear_bag.append(old)
        self._equipped[slot] = gear
        self._apply_effects()
        if self.on_change:
            self.on_change()
        return True

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------
    def _apply_effects(self):
        if self.player:
            spd = max(4, int(8 * self._class_spd + self.speed_bonus()))
            self.player.speed = spd
        if self.player_state:
            self.player_state.defense = self.defense()
        weapon = self._equipped.get('weapon')
        if self.sword:
            from ursina import color as uc
            if weapon and weapon.get('blade'):
                r, g, b = weapon['blade']
                self.sword.set_blade_color(uc.rgb(r, g, b))
            else:
                self.sword.set_blade_color(uc.rgb(200, 200, 200))

    # ------------------------------------------------------------------
    # Stat helpers
    # ------------------------------------------------------------------
    def get(self, slot: str) -> Optional[dict]:
        return self._equipped.get(slot)

    def damage_bonus(self) -> int:
        w = self.get('weapon')
        r = self.get('ring')
        return (w['dmg'] if w else 0) + (r['dmg'] if r else 0) + self._class_atk

    def defense(self) -> int:
        total = 0
        for slot in ('armor', 'boots', 'ring'):
            item = self.get(slot)
            if item:
                total += item['def']
        return total

    def speed_bonus(self) -> int:
        b = self.get('boots')
        r = self.get('ring')
        return (b['spd'] if b else 0) + (r['spd'] if r else 0)

    def power_rating(self) -> int:
        return calc_pr(self._equipped) + self._class_atk * 2

    def set_class_stats(self, base_atk: int, base_spd: float):
        self._class_atk = base_atk
        self._class_spd = base_spd
        self._apply_effects()

    def summary_lines(self) -> list:
        lines = []
        icons = {'weapon': '[K]', 'armor': '[Z]', 'boots': '[B]', 'ring': '[R]'}
        for slot in self.SLOTS:
            item = self.get(slot)
            if item:
                parts = []
                if item['dmg']: parts.append(f'+{item["dmg"]}ATK')
                if item['def']: parts.append(f'+{item["def"]}DEF')
                if item['spd']: parts.append(f'+{item["spd"]}HIZ')
                lines.append(f'{icons[slot]} {item["name"]}  {" ".join(parts)}')
        pr = self.power_rating()
        if pr:
            lines.append(f'>> PR: {pr}')
        return lines

    # ------------------------------------------------------------------
    # Save / load helpers
    # ------------------------------------------------------------------
    def gear_bag_save(self) -> list:
        return [{'base_id': g['base_id'], 'rarity': g['rarity']} for g in self.gear_bag]

    def equipped_save(self) -> dict:
        out = {}
        for slot in self.SLOTS:
            g = self._equipped.get(slot)
            out[slot] = {'base_id': g['base_id'], 'rarity': g['rarity']} if g else None
        return out

    def restore_gear(self, gear_bag_data: list, equipped_data: dict):
        """Restore gear state from saved dicts. Calls _apply_effects once at end."""
        self.gear_bag = [make_gear(e['base_id'], e['rarity']) for e in gear_bag_data]
        for slot in self.SLOTS:
            entry = equipped_data.get(slot)
            self._equipped[slot] = make_gear(entry['base_id'], entry['rarity']) if entry else None
        self._apply_effects()
