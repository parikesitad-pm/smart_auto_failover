"""
AutoFailover 3.0 Platform HAL - macOS Native Implementation
Author: parikesitad-pm
© 2026
"""

import re
import subprocess
import platform
from typing import List, Dict, Any, Optional, Tuple
from ..base import PlatformBackend
from ...models.interface import NetworkInterface, InterfaceState, InterfaceMediaType


class MacOSPlatformBackend(PlatformBackend):
    """
    Native macOS networking HAL via networksetup, ifconfig, ipconfig, and route.
    """

    def discover_interfaces(self) -> List[NetworkInterface]:
        interfaces: List[NetworkInterface] = []
        
        # Read hardware ports via networksetup -listallhardwareports
        port_map: Dict[str, Dict[str, str]] = {}
        try:
            cp = subprocess.run(["networksetup", "-listallhardwareports"], capture_output=True, text=True, timeout=2.0)
            if cp.returncode == 0:
                current_port = ""
                current_dev = ""
                for line in cp.stdout.splitlines():
                    line = line.strip()
                    if line.startswith("Hardware Port:"):
                        current_port = line.split(":", 1)[1].strip()
                    elif line.startswith("Device:"):
                        current_dev = line.split(":", 1)[1].strip()
                        if current_port and current_dev:
                            port_map[current_dev] = {"port": current_port}
        except Exception:
            pass

        default_route = self.get_default_route()
        active_if_name = default_route[0] if default_route else None

        for dev, info in port_map.items():
            port_name = info["port"]
            p_lower = port_name.lower()
            if "wi-fi" in p_lower or "airport" in p_lower:
                media_type = InterfaceMediaType.WIFI
                friendly = f"Wi-Fi ({dev})"
            elif "ethernet" in p_lower or "lan" in p_lower:
                media_type = InterfaceMediaType.ETHERNET
                friendly = f"Ethernet ({dev})"
            else:
                media_type = InterfaceMediaType.OTHER
                friendly = f"{port_name} ({dev})"

            details = self.query_interface_details(dev)
            carrier = details["carrier"]
            admin_enabled = details["admin_enabled"]

            if not admin_enabled:
                state = InterfaceState.DISABLED
            elif not carrier:
                state = InterfaceState.OFFLINE
            elif dev == active_if_name:
                state = InterfaceState.ONLINE
            elif details.get("ip_address"):
                state = InterfaceState.READY
            else:
                state = InterfaceState.OFFLINE

            iface = NetworkInterface(
                id=dev,
                name=dev,
                friendly_name=friendly,
                media_type=media_type,
                carrier=carrier,
                admin_enabled=admin_enabled,
                state=state,
                ip_address=details.get("ip_address"),
                netmask=details.get("netmask"),
                gateway=details.get("gateway"),
                ssid=details.get("ssid"),
                link_speed=details.get("link_speed"),
            )

            if state in (InterfaceState.DISABLED, InterfaceState.OFFLINE):
                iface.clear_network_addressing()

            interfaces.append(iface)

        return interfaces

    def query_interface_details(self, name: str) -> Dict[str, Any]:
        result = {
            "carrier": False,
            "admin_enabled": True,
            "ip_address": None,
            "netmask": None,
            "gateway": None,
            "ssid": None,
            "link_speed": None,
        }

        try:
            cp = subprocess.run(["ifconfig", name], capture_output=True, text=True, timeout=1.5)
            if cp.returncode == 0:
                output = cp.stdout
                result["carrier"] = "status: active" in output
                result["admin_enabled"] = "<UP," in output or ",UP," in output

                # Extract IP & Netmask
                m_inet = re.search(r"inet\s+(\d+\.\d+\.\d+\.\d+)\s+netmask\s+0x([0-9a-fA-F]+)", output)
                if m_inet:
                    result["ip_address"] = m_inet.group(1)
                    hex_mask = int(m_inet.group(2), 16)
                    result["netmask"] = f"{(hex_mask >> 24) & 0xFF}.{(hex_mask >> 16) & 0xFF}.{(hex_mask >> 8) & 0xFF}.{hex_mask & 0xFF}"

                # Extract Media / Speed
                m_media = re.search(r"media:\s+autoselect\s+\((.+?)\)", output)
                if m_media:
                    result["link_speed"] = m_media.group(1)
        except Exception:
            pass

        # Query SSID if Wi-Fi
        try:
            airport_path = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"
            cp = subprocess.run([airport_path, "-I"], capture_output=True, text=True, timeout=1.0)
            if cp.returncode == 0:
                for line in cp.stdout.splitlines():
                    line = line.strip()
                    if line.startswith("SSID:"):
                        result["ssid"] = line.split(":", 1)[1].strip()
                        break
        except Exception:
            pass

        # Gateway via route get default
        try:
            cp = subprocess.run(["route", "-n", "get", "default"], capture_output=True, text=True, timeout=1.0)
            if cp.returncode == 0:
                for line in cp.stdout.splitlines():
                    line = line.strip()
                    if line.startswith("gateway:"):
                        result["gateway"] = line.split(":", 1)[1].strip()
                        break
        except Exception:
            pass

        return result

    def set_interface_admin_state(self, name: str, enable: bool) -> bool:
        cmd = ["ifconfig", name, "up" if enable else "down"]
        try:
            res = subprocess.run(cmd, capture_output=True, timeout=2.0)
            if res.returncode == 0:
                return True
            res_sudo = subprocess.run(["sudo", "-n"] + cmd, capture_output=True, timeout=2.0)
            return res_sudo.returncode == 0
        except Exception:
            return False

    def set_default_route(self, interface_name: str, gateway: str) -> bool:
        cmd = ["route", "change", "default", gateway, "-interface", interface_name]
        try:
            res = subprocess.run(cmd, capture_output=True, timeout=2.0)
            if res.returncode == 0:
                return True
            res_sudo = subprocess.run(["sudo", "-n"] + cmd, capture_output=True, timeout=2.0)
            return res_sudo.returncode == 0
        except Exception:
            return False

    def get_default_route(self) -> Optional[Tuple[str, str]]:
        try:
            cp = subprocess.run(["route", "-n", "get", "default"], capture_output=True, text=True, timeout=1.0)
            if cp.returncode == 0:
                gw = None
                iface = None
                for line in cp.stdout.splitlines():
                    line = line.strip()
                    if line.startswith("gateway:"):
                        gw = line.split(":", 1)[1].strip()
                    elif line.startswith("interface:"):
                        iface = line.split(":", 1)[1].strip()
                if iface and gw:
                    return iface, gw
        except Exception:
            pass
        return None

    def get_system_identity(self) -> Dict[str, str]:
        hw_model = "Mac"
        try:
            cp = subprocess.run(["sysctl", "-n", "hw.model"], capture_output=True, text=True, timeout=1.0)
            if cp.returncode == 0 and cp.stdout.strip():
                hw_model = cp.stdout.strip()
        except Exception:
            pass

        return {
            "device_name": hw_model,
            "os_name": f"macOS {platform.mac_ver()[0]}",
            "architecture": platform.machine(),
            "kernel": platform.release(),
        }
