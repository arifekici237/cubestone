from ursina import Entity


class HealingSystem(Entity):
    HEAL_AMOUNT = 40

    def __init__(self, player_state, item_counts, hud=None):
        super().__init__()
        self.player_state = player_state
        self.item_counts  = item_counts
        self.hud          = hud

    def input(self, key):
        if key == 'h':
            if self.item_counts.get('health_potion', 0) > 0:
                self.item_counts['health_potion'] -= 1
                self.player_state.health = min(
                    self.player_state.max_health,
                    self.player_state.health + self.HEAL_AMOUNT,
                )
                if self.hud:
                    self.hud.set_health(
                        self.player_state.health, self.player_state.max_health
                    )
