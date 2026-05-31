from typing import Optional, Callable


class EventBus:
    """Minimal event/message bus for loose coupling between systems."""

    def __init__(self):
        self._listeners = {}

    def on(self, event: str, callback: Callable) -> None:
        self._listeners.setdefault(event, []).append(callback)

    def emit(self, event: str, *args, **kwargs) -> None:
        for cb in self._listeners.get(event, []):
            cb(*args, **kwargs)


class CombatSystem:
    """Handles attack resolution. Publishes events; doesn't know about loot."""

    def __init__(self, event_bus: Optional[EventBus] = None):
        self._bus = event_bus

    def attack(self, attacker, target, damage: int) -> None:
        target.take_damage(damage)
        if not target.is_alive and self._bus:
            self._bus.emit('entity_died', target)
