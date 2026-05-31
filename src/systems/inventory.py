from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class ItemStack:
    item_id: str
    count: int = 1


class Inventory:
    def __init__(self, size: int = 36):
        self.size = size
        self.slots: Dict[int, Optional[ItemStack]] = {i: None for i in range(size)}

    def add_item(self, item_id: str, count: int = 1) -> int:
        """Returns leftover count when inventory is full."""
        for i in range(self.size):
            if self.slots[i] is None:
                self.slots[i] = ItemStack(item_id, count)
                return 0
        return count

    def remove_item(self, slot: int) -> Optional[ItemStack]:
        item = self.slots[slot]
        self.slots[slot] = None
        return item

    def get_item(self, slot: int) -> Optional[ItemStack]:
        return self.slots[slot]
