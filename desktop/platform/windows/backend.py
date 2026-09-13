"""
AutoFailover 3.0 Platform HAL - Windows Native Implementation
Author: parikesitad-pm
© 2026

Optimized for high-cadence monitoring without spawning visible PowerShell popups:
- Strict CREATE_NO_WINDOW and STARTF_USESHOWWINDOW flags on all Windows subprocesses
- In-process telemetry via psutil when available
- Cached network details and default route queries to prevent process storms
"""

import json
import time
import subprocess
import platform
from typing import List, Dict, Any, Optional, Tuple
from ..base import PlatformBackend
from ...models.interface import NetworkInterface, InterfaceState, InterfaceMediaType

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


def _run_subprocess_hidden(cmd: List[str], timeout: float = 3.0) -> Optional[str]:
    """
    Executes a Windows subprocess strictly without spawning any visible console windows.
    Applies STARTUPINFO(SW_HIDE) and CREATE_NO_WINDOW (0x08000000).
    """
    startupinfo = None
    creationflags = 0
    if platform.system() == "Windows":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0  # SW_HIDE
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)

    try:
        cp = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            startupinfo=startupinfo,
            creationflags=creationflags,
        )
        if cp.returncode == 0:
            return cp.stdout.strip()
    except Exception:
        pass
    return None


class WindowsPlatformBackend(PlatformBackend):
    """
    Native Windows networking HAL via hidden PowerShell/netsh and in-process psutil caching.
    Guarantees zero visible console popups during runtime monitoring.
    """

    def __init__(self):
        self._cache_details: Dict[str, Tuple[float, Dict[str, Any]]] = {}
        self._cache_default_route: Optional[Tuple[float, Tuple[str, str]]] = None
        self._cache_adapters: Optional[Tuple[float, List[NetworkInterface]]] = None
        self._details_ttl_sec: float = 4.0
        self._route_ttl_sec: float = 2.5
        self._adapters_ttl_sec: float = 5.0

    def _run_ps(self, cmd: str, timeout: float = 3.0) -> Optional[str]:
        full_cmd = [
            "powershell",
            "-NoProfile",
            "-NonInteractive",
            "-WindowStyle",
            "Hidden",
            "-Command",
            cmd,
        ]
        return _run_subprocess_hidden(full_cmd, timeout=timeout)

    def discover_interfaces(self) -> List[NetworkInterface]:
        now = time.monotonic()
        if self._cache_adapters and (now - self._cache_adapters[0] < self._adapters_ttl_sec):
            return [iface.model_copy() for iface in self._cache_adapters[1]]

        interfaces: List[NetworkInterface] = []
        ps_cmd = "Get-NetAdapter | Select-Object Name, InterfaceDescription, InterfaceIndex, Status, LinkSpeed, MediaType | ConvertTo-Json"
        output = self._run_ps(ps_cmd)

        adapters = []
        if output:
            try:
                data = json.loads(output)
                if isinstance(data, dict):
                    adapters = [data]
                elif isinstance(data, list):
                    adapters = data
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

        self._cache_adapters = (now, interfaces)
        return interfaces

    def query_interface_details(self, name: str) -> Dict[str, Any]:
        now = time.monotonic()
        if name in self._cache_details:
            timestamp, cached_result = self._cache_details[name]
            if now - timestamp < self._details_ttl_sec:
                # Fast in-process update of carrier if psutil is available
                if HAS_PSUTIL:
                    stats = psutil.net_if_stats().get(name)
                    if stats:
                        cached_result["carrier"] = stats.isup
                return dict(cached_result)

        result = {
            "carrier": False,
            "admin_enabled": True,
            "ip_address": None,
            "netmask": None,
            "gateway": None,
            "ssid": None,
            "link_speed": None,
        }

        # Step 1: Use in-process psutil for fast IP/carrier resolution if available
        if HAS_PSUTIL:
            try:
                stats = psutil.net_if_stats().get(name)
                if stats:
                    result["carrier"] = stats.isup
                    result["admin_enabled"] = stats.isup or True
                    if stats.speed > 0:
                        result["link_speed"] = f"{stats.speed} Mbps"

                addrs = psutil.net_if_addrs().get(name, [])
                for addr in addrs:
                    # AF_INET is family 2 across platforms
                    if getattr(addr, "family", None) == 2 or str(addr.family) == "AddressFamily.AF_INET":
                        if addr.address and not addr.address.startswith("127."):
                            result["ip_address"] = addr.address
                            result["netmask"] = addr.netmask
                            break
            except Exception:
                pass

        # Step 2: Query Gateway via hidden PowerShell only if needed
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

        # Step 3: Query SSID via hidden netsh wlan
        try:
            out_wlan = _run_subprocess_hidden(["netsh", "wlan", "show", "interfaces"], timeout=1.5)
            if out_wlan:
                for line in out_wlan.splitlines():
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

        self._cache_details[name] = (now, result)
        return result

    def set_interface_admin_state(self, name: str, enable: bool) -> bool:
        state_str = "ENABLED" if enable else "DISABLED"
        res = _run_subprocess_hidden(
            ["netsh", "interface", "set", "interface", f"name={name}", f"admin={state_str}"],
            timeout=3.0,
        )
        # Invalidate caches
        self._cache_details.pop(name, None)
        self._cache_adapters = None
        return res is not None

    def set_default_route(self, interface_name: str, gateway: str) -> bool:
        # Lower InterfaceMetric to 10 for primary takeover
        ps_cmd = f"Set-NetIPInterface -InterfaceAlias '{interface_name}' -InterfaceMetric 10 -ErrorAction Stop"
        out = self._run_ps(ps_cmd)
        self._cache_default_route = None
        return out is not None

    def get_default_route(self) -> Optional[Tuple[str, str]]:
        now = time.monotonic()
        if self._cache_default_route and (now - self._cache_default_route[0] < self._route_ttl_sec):
            return self._cache_default_route[1]

        ps_cmd = "Get-NetRoute -DestinationPrefix '0.0.0.0/0' | Sort-Object RouteMetric | Select-Object -First 1 InterfaceAlias, NextHop | ConvertTo-Json"
        out = self._run_ps(ps_cmd)
        if out:
            try:
                data = json.loads(out)
                alias = data.get("InterfaceAlias")
                nexthop = data.get("NextHop")
                if alias and nexthop:
                    self._cache_default_route = (now, (alias, nexthop))
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
