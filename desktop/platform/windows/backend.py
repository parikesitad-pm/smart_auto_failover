"""
AutoFailover 3.0 Platform HAL - Windows Native Implementation
Author: parikesitad-pm
© 2026
"""

import json
import subprocess
import platform
from typing import List, Dict, Any, Optional, Tuple
from ..base import PlatformBackend
from ...models.interface import NetworkInterface, InterfaceState, InterfaceMediaType


class WindowsPlatformBackend(PlatformBackend):
    """
    Native Windows networking HAL via PowerShell NetTCPIP/NetAdapter cmdlets and netsh fallback.
    """

    def _run_ps(self, cmd: str, timeout: float = 3.0) -> Optional[str]:
        try:
            full_cmd = ["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd]
            cp = subprocess.run(full_cmd, capture_output=True, text=True, timeout=timeout)
            if cp.returncode == 0:
                return cp.stdout.strip()
        except Exception:
            pass
        return None

    def discover_interfaces(self) -> List[NetworkInterface]:
        interfaces: List[NetworkInterface] = []
        ps_cmd = "Get-NetAdapter | Select-Object Name, InterfaceDescription, InterfaceIndex, Status, LinkSpeed, MediaType | ConvertTo-Json"
        output = self._run_ps(ps_cmd)

        if not output:
            return interfaces

        try:
            data = json.loads(output)
            if isinstance(data, dict):
                adapters = [data]
            elif isinstance(data, list):
                adapters = data
            else:
                adapters = []
        except Exception:
            adapters = []

        default_route = self.get_default_route()
        active_if_name = default_route[0] if default_route else None

        for item in adapters:
            name = item.get("Name", "")
            if not name:
                continue

            desc = item.get("InterfaceDescription", "")
            status = str(item.get("Status", "")).lower()
            media = str(item.get("MediaType", "")).lower()

            if "802.3" in media or "ethernet" in desc.lower():
                media_type = InterfaceMediaType.ETHERNET
                friendly = f"Ethernet ({name})"
            elif "802.11" in media or "wi-fi" in desc.lower() or "wireless" in desc.lower():
                media_type = InterfaceMediaType.WIFI
                friendly = f"Wi-Fi ({name})"
            else:
                media_type = InterfaceMediaType.OTHER
                friendly = f"Interface ({name})"

            details = self.query_interface_details(name)
            carrier = status in ("up", "connected")
            admin_enabled = status != "disabled"

            if not admin_enabled:
                state = InterfaceState.DISABLED
            elif not carrier:
                state = InterfaceState.OFFLINE
            elif name == active_if_name:
                state = InterfaceState.ONLINE
            elif details.get("ip_address"):
                state = InterfaceState.READY
            else:
                state = InterfaceState.OFFLINE

            iface = NetworkInterface(
                id=name,
                name=name,
                friendly_name=friendly,
                media_type=media_type,
                carrier=carrier,
                admin_enabled=admin_enabled,
                state=state,
                ip_address=details.get("ip_address"),
                netmask=details.get("netmask"),
                gateway=details.get("gateway"),
                ssid=details.get("ssid"),
                link_speed=item.get("LinkSpeed") or details.get("link_speed"),
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

        # Query IP and Gateway via PowerShell
        ps_ip = f"""
        $ip = Get-NetIPAddress -InterfaceAlias '{name}' -AddressFamily IPv4 -ErrorAction SilentlyContinue | Select-Object -First 1 IPAddress, PrefixLength
        $gw = Get-NetRoute -InterfaceAlias '{name}' -DestinationPrefix '0.0.0.0/0' -ErrorAction SilentlyContinue | Select-Object -First 1 NextHop
        [PSCustomObject]@{{
            IP = $ip.IPAddress
            Prefix = $ip.PrefixLength
            Gateway = $gw.NextHop
        }} | ConvertTo-Json
        """
        output = self._run_ps(ps_ip)
        if output:
            try:
                data = json.loads(output)
                ip = data.get("IP")
                if ip:
                    result["ip_address"] = ip
                    result["carrier"] = True
                    prefix = data.get("Prefix")
                    if prefix:
                        mask = (0xFFFFFFFF >> (32 - int(prefix))) << (32 - int(prefix)) if int(prefix) > 0 else 0
                        result["netmask"] = f"{(mask >> 24) & 0xFF}.{(mask >> 16) & 0xFF}.{(mask >> 8) & 0xFF}.{mask & 0xFF}"
                if data.get("Gateway"):
                    result["gateway"] = data.get("Gateway")
            except Exception:
                pass

        # Query SSID via netsh wlan
        try:
            cp = subprocess.run(["netsh", "wlan", "show", "interfaces"], capture_output=True, text=True, timeout=1.5)
            if cp.returncode == 0:
                for line in cp.stdout.splitlines():
                    line_clean = line.strip()
                    if line_clean.startswith("SSID") and not line_clean.startswith("BSSID"):
                        parts = line_clean.split(":", 1)
                        if len(parts) > 1:
                            ssid_val = parts[1].strip()
                            if ssid_val:
                                result["ssid"] = ssid_val
                                break
        except Exception:
            pass

        return result

    def set_interface_admin_state(self, name: str, enable: bool) -> bool:
        state_str = "ENABLED" if enable else "DISABLED"
        try:
            cp = subprocess.run(
                ["netsh", "interface", "set", "interface", f"name={name}", f"admin={state_str}"],
                capture_output=True,
                timeout=3.0,
            )
            return cp.returncode == 0
        except Exception:
            return False

    def set_default_route(self, interface_name: str, gateway: str) -> bool:
        # Lower InterfaceMetric to 10 for primary takeover
        ps_cmd = f"Set-NetIPInterface -InterfaceAlias '{interface_name}' -InterfaceMetric 10 -ErrorAction Stop"
        out = self._run_ps(ps_cmd)
        return out is not None

    def get_default_route(self) -> Optional[Tuple[str, str]]:
        ps_cmd = "Get-NetRoute -DestinationPrefix '0.0.0.0/0' | Sort-Object RouteMetric | Select-Object -First 1 InterfaceAlias, NextHop | ConvertTo-Json"
        out = self._run_ps(ps_cmd)
        if out:
            try:
                data = json.loads(out)
                alias = data.get("InterfaceAlias")
                nexthop = data.get("NextHop")
                if alias and nexthop:
                    return alias, nexthop
            except Exception:
                pass
        return None

    def get_system_identity(self) -> Dict[str, str]:
        return {
            "device_name": platform.node(),
            "os_name": f"Windows {platform.release()}",
            "architecture": platform.machine(),
            "kernel": platform.version(),
        }
