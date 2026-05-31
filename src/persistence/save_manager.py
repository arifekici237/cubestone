import json
from pathlib import Path

SAVE_DIR = Path(__file__).parent.parent.parent / 'saves'


class SaveManager:
    """Persists world block modifications and player state as JSON."""

    def __init__(self, save_name: str = 'world'):
        SAVE_DIR.mkdir(exist_ok=True)
        self.path = SAVE_DIR / f'{save_name}.json'

    # ------------------------------------------------------------------
    def save(self, modifications: dict) -> None:
        """Legacy: save only block changes (called by BlockInteraction)."""
        existing = self._load_raw()
        blocks   = {f'{k[0]},{k[1]},{k[2]}': v for k, v in modifications.items()}
        existing['blocks'] = blocks
        existing.setdefault('version', 2)
        self._write(existing)
        print(f'Saved {len(blocks)} block changes → {self.path.name}')

    def save_all(self, modifications: dict, item_counts: dict,
                 equipment, player_class_name: str) -> None:
        blocks = {f'{k[0]},{k[1]},{k[2]}': v for k, v in modifications.items()}
        consumables = {k: v for k, v in item_counts.items() if v > 0}
        data = {
            'version':      2,
            'blocks':       blocks,
            'player_class': player_class_name,
            'item_counts':  consumables,
            'gear_bag':     equipment.gear_bag_save(),
            'equipped':     equipment.equipped_save(),
        }
        self._write(data)
        print(f'Saved full state → {self.path.name}')

    # ------------------------------------------------------------------
    def load(self) -> dict:
        """Legacy: return only block modifications dict."""
        raw = self._load_raw()
        blocks = raw.get('blocks', raw)  # old format: the dict IS the blocks
        return {
            tuple(int(x) for x in k.split(',')): v
            for k, v in blocks.items()
            if ',' in k
        }

    def load_all(self) -> dict:
        """Return full save dict, or empty dict if no save exists."""
        if not self.path.exists():
            return {}
        raw = self._load_raw()
        if 'version' not in raw:
            return {'blocks': raw}  # old format: just blocks
        return raw

    # ------------------------------------------------------------------
    def _load_raw(self) -> dict:
        if not self.path.exists():
            return {}
        try:
            with open(self.path) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def _write(self, data: dict) -> None:
        with open(self.path, 'w') as f:
            json.dump(data, f, indent=2)
