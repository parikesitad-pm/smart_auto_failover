from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple

from core.models import AdapterInfo, PriorityLevel


class BaseNetworkBackend(ABC):
    """Abstract interface defining OS-level network operations for auto-failover."""

    @abstractmethod
    def is_admin(self) -> bool:
        """Check if current process has root/administrator privileges."""
        pass

    @abstractmethod
    def request_elevation(self) -> bool:
        """Trigger OS-native elevation (UAC on Windows, osascript/sudo on macOS)."""
        pass

    @abstractmethod
    def get_all_adapters(self) -> List[AdapterInfo]:
        """Discover all available network interfaces/services."""
        pass

    @abstractmethod
    def set_interface_metric(self, alias: str, metric: int) -> Tuple[bool, str]:
        """Set route/interface metric (used on Windows)."""
        pass

    @abstractmethod
    def set_network_priority_order(self, ordered_aliases: List[str]) -> Tuple[bool, str]:
        """Set network service priority order (used on macOS networksetup)."""
        pass

    @abstractmethod
    def restore_defaults(self, aliases: List[str]) -> List[Tuple[str, bool, str]]:
        """Restore all interfaces to operating system defaults (automatic metric or original order)."""
        pass

    @abstractmethod
    def set_adapter_enabled(self, alias: str, enabled: bool) -> Tuple[bool, str]:
        """Manually connect (enable) or disconnect (disable) a network interface."""
        pass
