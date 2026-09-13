"""
AutoFailover 3.0 Core - Recovery & Anti-Flap Arbiter
Author: parikesitad-pm
© 2026
"""

import time
from typing import Dict, Optional


class RecoveryArbiter:
    """
    Prevents flapping by enforcing a stabilization cooldown window
    before a recovered interface is considered eligible for reclaim.
    Core rule: Recovered interfaces transition to READY first!
    """

    def __init__(self, default_cooldown_sec: float = 5.0):
        self.default_cooldown_sec = default_cooldown_sec
        # Maps interface_id -> timestamp when recovered carrier was detected
        self._recovery_timestamps: Dict[str, float] = {}

    def notify_carrier_restored(self, interface_id: str) -> None:
        """Called when link carrier transitions from 0 -> 1."""
        self._recovery_timestamps[interface_id] = time.time()

    def notify_carrier_lost(self, interface_id: str) -> None:
        """Called when link carrier drops. Resets any ongoing cooldown."""
        if interface_id in self._recovery_timestamps:
            del self._recovery_timestamps[interface_id]

    def is_stabilized(self, interface_id: str, cooldown_sec: Optional[float] = None) -> bool:
        """
        Returns True if interface has been stable for at least cooldown duration.
        If interface was never in recovery, it is considered already stabilized.
        """
        if interface_id not in self._recovery_timestamps:
            return True

        elapsed = time.time() - self._recovery_timestamps[interface_id]
        required = cooldown_sec if cooldown_sec is not None else self.default_cooldown_sec
        return elapsed >= required

    def get_remaining_cooldown(self, interface_id: str, cooldown_sec: Optional[float] = None) -> float:
        """Returns remaining cooldown in seconds (0.0 if stabilized)."""
        if interface_id not in self._recovery_timestamps:
            return 0.0

        elapsed = time.time() - self._recovery_timestamps[interface_id]
        required = cooldown_sec if cooldown_sec is not None else self.default_cooldown_sec
        return max(0.0, required - elapsed)

    def mark_fully_reclaimed(self, interface_id: str) -> None:
        """Clear recovery tracking after normal operation has resumed."""
        if interface_id in self._recovery_timestamps:
            del self._recovery_timestamps[interface_id]
