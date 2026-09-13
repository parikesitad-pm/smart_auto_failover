"""
AutoFailover 3.0 Platform HAL - Abstract Base Backend
Author: parikesitad-pm
© 2026
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from ..models.interface import NetworkInterface


class PlatformBackend(ABC):
    """
    Abstract Hardware Abstraction Layer for OS-specific network operations.
    """

    @abstractmethod
    def discover_interfaces(self) -> List[NetworkInterface]:
        """Enumerate all real network interfaces present on the system."""
        pass

    @abstractmethod
    def query_interface_details(self, name: str) -> Dict[str, Any]:
        """
        Query real-time dynamic properties:
        carrier (bool), admin_enabled (bool), ip_address, netmask, gateway, ssid, link_speed.
        """
        pass

    @abstractmethod
    def set_interface_admin_state(self, name: str, enable: bool) -> bool:
        """Administratively enable (UP) or disable (DOWN) an interface at OS level."""
        pass

    @abstractmethod
    def set_default_route(self, interface_name: str, gateway: str) -> bool:
        """Execute Layer-3 default route switch to specified interface."""
        pass

    @abstractmethod
    def get_default_route(self) -> Optional[Tuple[str, str]]:
        """Query authoritative active default route: returns (interface_name, gateway_ip)."""
        pass

    @abstractmethod
    def get_system_identity(self) -> Dict[str, str]:
        """Query system device name, OS, architecture, kernel."""
        pass
