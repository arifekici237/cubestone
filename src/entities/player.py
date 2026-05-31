from dataclasses import dataclass, field
from typing import Optional, Tuple


@dataclass
class PlayerState:
    """Player state — pure data, no rendering."""

    position:     Tuple[float, float, float] = field(default_factory=lambda: (0.0, 64.0, 0.0))
    health:       int   = 100
    max_health:   int   = 100
    selected_block: int = 1
    defense:      int   = 0
    damage_mult:  float = 1.0   # ability shield multiplier (Iron Skin etc.)
    player_class: Optional[object] = field(default=None, repr=False)
    xp:           int   = 0
    level:        int   = 1
    xp_to_next:   int   = 100

    @property
    def is_alive(self) -> bool:
        return self.health > 0

    def take_damage(self, amount: int) -> None:
        reduced = max(1, amount - self.defense // 3)
        reduced = max(1, int(reduced * self.damage_mult))
        self.health = max(0, self.health - reduced)

    def heal(self, amount: int) -> None:
        self.health = min(self.max_health, self.health + amount)

    def apply_class(self, player_class) -> None:
        self.player_class = player_class
        self.max_health   = player_class.base_hp
        self.health       = player_class.base_hp

    def gain_xp(self, amount: int) -> bool:
        """Add XP; returns True if player leveled up."""
        self.xp += amount
        leveled = False
        while self.xp >= self.xp_to_next:
            self.xp       -= self.xp_to_next
            self.level    += 1
            self.xp_to_next = int(self.xp_to_next * 1.5)
            self.max_health += 15
            self.health      = self.max_health
            leveled = True
        return leveled
