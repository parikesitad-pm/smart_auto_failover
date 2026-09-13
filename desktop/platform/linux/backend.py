"""
AutoFailover 3.0 Platform HAL - Linux Native Implementation
Author: parikesitad-pm
© 2026
"""

import os
import json
import subprocess
import platform
from typing import List, Dict, Any, Optional, Tuple
from ..base import PlatformBackend
from ...models.interface import NetworkInterface, InterfaceState, InterfaceMediaType


def cidr_to_netmask(prefixlen: int) -> str:
    """Convert CIDR prefix length (e.g. 24) to dotted decimal netmask (e.g. 255.255.255.0)."""
    mask = (0xFFFFFFFF >> (32 - prefixlen)) << (32 - prefixlen) if prefixlen > 0 else 0
    return f"{(mask >> 24) & 0xFF}.{(mask >> 16) & 0xFF}.{(mask >> 8) & 0xFF}.{mask & 0xFF}"


class LinuxPlatformBackend(PlatformBackend):
    """
    Authoritative native Linux networking HAL via sysfs, iproute2 JSON, and iw.
    """

    def discover_interfaces(self) -> List[NetworkInterface]:
        interfaces: List[NetworkInterface] = []
        sysfs_net = "/sys/class/net"

        if not os.path.exists(sysfs_net):
            return interfaces

        for iface_name in sorted(os.listdir(sysfs_net)):
            # Skip loopback and virtual virtualization interfaces
            if iface_name == "lo" or iface_name.startswith(("docker", "br-", "veth")):
                continue

            iface_path = os.path.join(sysfs_net, iface_name)

            # Determine media type
            if os.path.exists(os.path.join(iface_path, "wireless")) or os.path.exists(os.path.join(iface_path, "phy80211")):
                media_type = InterfaceMediaType.WIFI
                friendly = f"Wi-Fi ({iface_name})"
            elif os.path.exists(os.path.join(iface_path, "device")):
                media_type = InterfaceMediaType.ETHERNET
                friendly = f"Ethernet ({iface_name})"
            else:
                media_type = InterfaceMediaType.OTHER
                friendly = f"Interface ({iface_name})"

            # Query dynamic details immediately
            details = self.query_interface_details(iface_name)

            # Determine initial state
            if not details["admin_enabled"]:
                state = InterfaceState.DISABLED
            elif not details["carrier"]:
                state = InterfaceState.OFFLINE
            elif details["ip_address"] is not None:
                state = InterfaceState.READY
            else:
                state = InterfaceState.OFFLINE

            iface = NetworkInterface(
                id=iface_name,
                name=iface_name,
                friendly_name=friendly,
                media_type=media_type,
                carrier=details["carrier"],
                admin_enabled=details["admin_enabled"],
                state=state,
                ip_address=details["ip_address"],
                netmask=details["netmask"],
                gateway=details["gateway"],
                ssid=details["ssid"],
                link_speed=details["link_speed"],
            )

            # Enforce invariant: if DISABLED or OFFLINE, clear addressing
            if state in (InterfaceState.DISABLED, InterfaceState.OFFLINE):
                iface.clear_network_addressing()

            interfaces.append(iface)

        # Mark active default route as ONLINE if applicable
        default_route = self.get_default_route()
        if default_route:
            active_dev, _ = default_route
            for iface in interfaces:
                if iface.name == active_dev and iface.state == InterfaceState.READY:
                    iface.state = InterfaceState.ONLINE

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

        sysfs_path = f"/sys/class/net/{name}"
        if not os.path.exists(sysfs_path):
            return result

        # 1. Carrier Check
        carrier_file = os.path.join(sysfs_path, "carrier")
        operstate_file = os.path.join(sysfs_path, "operstate")
        try:
            carrier_val = 0
            if os.path.exists(carrier_file):
                with open(carrier_file, "r") as f:
                    carrier_val = int(f.read().strip())
            operstate = "down"
            if os.path.exists(operstate_file):
                with open(operstate_file, "r") as f:
                    operstate = f.read().strip().lower()
            result["carrier"] = (carrier_val == 1) and (operstate in ("up", "unknown"))
        except Exception:
            result["carrier"] = False

        # 2. Administrative State Check (flags bit 0x1 IFF_UP)
        flags_file = os.path.join(sysfs_path, "flags")
        try:
            with open(flags_file, "r") as f:
                flags_val = int(f.read().strip(), 16)
                result["admin_enabled"] = bool(flags_val & 0x1)
        except Exception:
            result["admin_enabled"] = True

        # Invariant: If admin disabled, do not query or return stale IP/Gateway/SSID
        if not result["admin_enabled"] or not result["carrier"]:
            return result

        # 3. IP Address & Netmask via `ip -j addr show <name>`
        try:
            cp = subprocess.run(
                ["ip", "-j", "addr", "show", name],
                capture_output=True,
                text=True,
                timeout=1.0,
            )
            if cp.returncode == 0 and cp.stdout.strip():
                data = json.loads(cp.stdout)
                if data and len(data) > 0:
                    for addr in data[0].get("addr_info", []):
                        if addr.get("family") == "inet":
                            result["ip_address"] = addr.get("local")
                            prefix = addr.get("prefixlen", 24)
                            result["netmask"] = cidr_to_netmask(prefix)
                            break
        except Exception:
            pass

        # 4. Gateway query via `ip -j route show default dev <name>`
        try:
            cp = subprocess.run(
                ["ip", "-j", "route", "show", "default", "dev", name],
                capture_output=True,
                text=True,
                timeout=1.0,
            )
            if cp.returncode == 0 and cp.stdout.strip():
                routes = json.loads(cp.stdout)
                if routes and len(routes) > 0:
                    result["gateway"] = routes[0].get("gateway")
        except Exception:
            pass

        # 5. Wi-Fi SSID via `iw dev <name> link`
        if os.path.exists(os.path.join(sysfs_path, "wireless")) or os.path.exists(os.path.join(sysfs_path, "phy80211")):
            try:
                cp = subprocess.run(
                    ["iw", "dev", name, "link"],
                    capture_output=True,
                    text=True,
                    timeout=1.0,
                )
                if cp.returncode == 0:
                    for line in cp.stdout.splitlines():
                        line_str = line.strip()
                        if line_str.startswith("SSID:"):
                            result["ssid"] = line_str.split("SSID:", 1)[1].strip()
                            break
            except Exception:
                pass

        # 6. Link Speed via sysfs `speed`
        speed_file = os.path.join(sysfs_path, "speed")
        try:
            if os.path.exists(speed_file):
                with open(speed_file, "r") as f:
                    speed_mbps = int(f.read().strip())
                    if speed_mbps >= 1000:
                        result["link_speed"] = f"{speed_mbps // 1000} Gbps"
                    elif speed_mbps > 0:
                        result["link_speed"] = f"{speed_mbps} Mbps"
        except Exception:
            pass

        return result

    def set_interface_admin_state(self, name: str, enable: bool) -> bool:
        cmd = ["ip", "link", "set", name, "up" if enable else "down"]
        try:
            # Check if running as root or via sudo
            res = subprocess.run(cmd, capture_output=True, timeout=2.0)
            if res.returncode == 0:
                return True
            # Attempt sudo if standard invocation failed with permission denied
            res_sudo = subprocess.run(["sudo", "-n"] + cmd, capture_output=True, timeout=2.0)
            return res_sudo.returncode == 0
        except Exception:
            return False

    def set_default_route(self, interface_name: str, gateway: str) -> bool:
        """
        Atomically switches Layer-3 default route using metric priority.
        Lowest metric (100) = active primary.
        """
        # Set primary low metric on target interface
        cmd = ["ip", "route", "replace", "default", "via", gateway, "dev", interface_name, "metric", "100"]
        try:
            res = subprocess.run(cmd, capture_output=True, timeout=2.0)
            if res.returncode == 0:
                return True
            res_sudo = subprocess.run(["sudo", "-n"] + cmd, capture_output=True, timeout=2.0)
            return res_sudo.returncode == 0
        except Exception:
            return False

    def get_default_route(self) -> Optional[Tuple[str, str]]:
        """Finds default route with lowest metric."""
        try:
            cp = subprocess.run(
                ["ip", "-j", "route", "show", "default"],
                capture_output=True,
                text=True,
                timeout=1.0,
            )
            if cp.returncode == 0 and cp.stdout.strip():
                routes = json.loads(cp.stdout)
                if routes:
                    # Sort by metric ascending
                    routes.sort(key=lambda r: r.get("metric", 1024))
                    best = routes[0]
                    return best.get("dev"), best.get("gateway")
        except Exception:
            pass
        return None

    def get_system_identity(self) -> Dict[str, str]:
        device_name = "Workstation"
        for dmi_path in ("/sys/class/dmi/id/product_name", "/sys/class/dmi/id/board_name"):
            try:
                if os.path.exists(dmi_path):
                    with open(dmi_path, "r") as f:
                        name = f.read().strip()
                        if name and name != "None":
                            device_name = name
                            break
            except Exception:
                pass

        os_name = "Linux"
        try:
            if os.path.exists("/etc/os-release"):
                with open("/etc/os-release", "r") as f:
                    for line in f:
                        if line.startswith("PRETTY_NAME="):
                            os_name = line.split("=", 1)[1].strip().strip('"')
                            break
        except Exception:
            pass

        u = os.uname()
        return {
            "device_name": device_name,
            "os_name": os_name,
            "architecture": u.machine,
            "kernel": u.release,
        }
