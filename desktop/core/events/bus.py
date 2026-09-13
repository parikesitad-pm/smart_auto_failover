"""
AutoFailover 3.0 Core - Event Bus
Author: parikesitad-pm
© 2026
"""

import threading
from typing import List, Callable, Dict, Any
from ...models.events import FailoverEvent, EventType


class EventBus:
    """
    Thread-safe event dispatcher and bounded historical log.
    """
    def __init__(self, max_history: int = 50):
        self.max_history = max_history
        self._history: List[FailoverEvent] = []
        self._listeners: List[Callable[[FailoverEvent], None]] = []
        self._lock = threading.Lock()

    def subscribe(self, callback: Callable[[FailoverEvent], None]) -> None:
        with self._lock:
            self._listeners.append(callback)

    def publish(
        self,
        event_type: EventType,
        message: str,
        interface_id: str = None,
        interface_name: str = None,
        details: Dict[str, Any] = None,
        severity: str = "INFO",
    ) -> FailoverEvent:
        event = FailoverEvent(
            event_type=event_type,
            message=message,
            interface_id=interface_id,
            interface_name=interface_name,
            severity=severity,
            details=details or {}
        )

        with self._lock:
            self._history.append(event)
            if len(self._history) > self.max_history:
                self._history.pop(0)
            callbacks = list(self._listeners)

        for cb in callbacks:
            try:
                cb(event)
            except Exception:
                pass

        return event

    def get_recent_events(self, limit: int = 20) -> List[FailoverEvent]:
        with self._lock:
            return list(reversed(self._history[-limit:]))

    def get_history(self, limit: int = 50) -> List[FailoverEvent]:
        """Returns chronological event history (oldest to newest) for UI initialization."""
        with self._lock:
            return list(self._history[-limit:])
