"""
AutoFailover 3.0 Models - Interface & State Definitions
Author: parikesitad-pm
© 2026
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from .metrics import PathMetrics


class InterfaceState(str, Enum):
    """
    Authoritative 5-state model for AutoFailover 3.0.
    """
    ONLINE = "ONLINE"        # Currently selected active default route
    READY = "READY"          # Healthy eligible standby candidate
    ALERT = "ALERT"          # Usable but degraded / high jitter or loss
    OFFLINE = "OFFLINE"      # Present/enabled but no carrier or disconnected
    DISABLED = "DISABLED"    # Administratively disabled at OS level

    def is_eligible_candidate(self) -> bool:
        """Only READY and ALERT can be considered for failover."""
        return self in (InterfaceState.READY, InterfaceState.ALERT)

    def is_usable(self) -> bool:
        """Paths that carry or can carry data."""
        return self in (InterfaceState.ONLINE, InterfaceState.READY, InterfaceState.ALERT)


class InterfaceMediaType(str, Enum):
    ETHERNET = "ethernet"
    WIFI = "wifi"
    CELLULAR = "cellular"
    OTHER = "other"


class NetworkInterface(BaseModel):
    """
    Represents a real, detected physical or virtual network interface.
    """
    id: str
    name: str                           # System device name (e.g. enp44s0, eth0, wlp0s20f3)
    friendly_name: str                  # Human-readable name (e.g. Ethernet 1, Wi-Fi)
    media_type: InterfaceMediaType = InterfaceMediaType.OTHER
    carrier: bool = False               # Physical link detected (sysfs carrier == 1)
    admin_enabled: bool = True          # OS administrative state (IFF_UP / Enabled)
    state: InterfaceState = InterfaceState.OFFLINE
    ip_address: Optional[str] = None
    netmask: Optional[str] = None
    gateway: Optional[str] = None
    ssid: Optional[str] = None          # Wi-Fi only
    link_speed: Optional[str] = None    # e.g. "1 Gbps", "100 Mbps"
    metrics: PathMetrics = Field(default_factory=PathMetrics)

    def clear_network_addressing(self) -> None:
        """Clear dynamic addressing upon disconnect or disable to prevent stale leaks."""
        self.ip_address = None
        self.gateway = None
        self.netmask = None
        self.ssid = None
        self.metrics.reset()
