"""
AutoFailover 3.0 Platform HAL - Windows Native Implementation
Author: parikesitad-pm
© 2026

Optimized for ultra-responsive monitoring without UI thread freezes or visible console popups:
- Strict CREATE_NO_WINDOW and STARTF_USESHOWWINDOW flags on all Windows subprocesses
- In-process telemetry and interface resolution via psutil (zero subprocesses for carrier & addressing)
- Static adapter metadata caching (query once, reuse indefinitely)
- Fast default route discovery via route.exe / Win32 table (10ms vs 1500ms PowerShell)
- Wi-Fi SSID queries isolated to active Wi-Fi adapters with 10s TTL
- Active subprocess rate tracking and latency instrumentation
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

# Subprocess call rate instrumentation
_SUBPROCESS_CALLS: List[float] = []


def _record_subprocess_call():
    now = time.monotonic()
    _SUBPROCESS_CALLS.append(now)
    cutoff = now - 60.0
    while _SUBPROCESS_CALLS and _SUBPROCESS_CALLS[0] < cutoff:
        _SUBPROCESS_CALLS.pop(0)


def get_subprocess_rate_per_min() -> int:
    now = time.monotonic()
    cutoff = now - 60.0
    while _SUBPROCESS_CALLS and _SUBPROCESS_CALLS[0] < cutoff:
        _SUBPROCESS_CALLS.pop(0)
    return len(_SUBPROCESS_CALLS)


def _run_subprocess_hidden(cmd: List[str], timeout: float = 2.0) -> Optional[str]:
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

    _record_subprocess_call()

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
    High-performance Windows networking HAL.
    Eliminates UI stutter by caching static hardware details and utilizing
    in-process psutil tables wherever possible.
    """

    def __init__(self):
        self._cache_details: Dict[str, Tuple[float, Dict[str, Any]]] = {}
        self._cache_default_route: Optional[Tuple[float, Tuple[str, str]]] = None
        self._cache_adapters: Optional[Tuple[float, List[NetworkInterface]]] = None
        self._static_adapter_cache: Dict[str, Dict[str, Any]] = {}
        self._cached_ssid: Tuple[float, Optional[str]] = (0.0, None)

        self._details_ttl_sec: float = 4.0
        self._route_ttl_sec: float = 3.0
        self._adapters_ttl_sec: float = 5.0
        self._ssid_ttl_sec: float = 10.0

        self._last_discovery_duration_ms: float = 0.0

    def _run_ps(self, cmd: str, timeout: float = 2.5) -> Optional[str]:
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

    def _populate_static_adapter_metadata(self):
        """Queries Get-NetAdapter once to store hardware descriptions and media types."""
        ps_cmd = "Get-NetAdapter | Select-Object Name, InterfaceDescription, InterfaceIndex, Status, LinkSpeed, MediaType | ConvertTo-Json"
        output = self._run_ps(ps_cmd, timeout=3.0)
        if not output:
            return
        try:
            data = json.loads(output)
            adapters = [data] if isinstance(data, dict) else (data if isinstance(data, list) else [])
            for item in adapters:
                name = item.get("Name", "")
                if not name:
                    continue
                desc = item.get("InterfaceDescription", "")
                media = str(item.get("MediaType", "")).lower()

                if "802.3" in media or "ethernet" in desc.lower():
                    m_type = InterfaceMediaType.ETHERNET
                    f_name = f"Ethernet ({name})"
                elif "802.11" in media or "wi-fi" in desc.lower() or "wireless" in desc.lower():
                    m_type = InterfaceMediaType.WIFI
                    f_name = f"Wi-Fi ({name})"
                else:
                    m_type = InterfaceMediaType.OTHER
                    f_name = f"Interface ({name})"

                self._static_adapter_cache[name] = {
                    "friendly_name": f_name,
                    "media_type": m_type,
                    "description": desc,
                    "link_speed": item.get("LinkSpeed"),
                }
        except Exception:
            pass

    def discover_interfaces(self) -> List[NetworkInterface]:
        t0 = time.monotonic()
        now = t0
        if self._cache_adapters and (now - self._cache_adapters[0] < self._adapters_ttl_sec):
            return [iface.model_copy() for iface in self._cache_adapters[1]]

        interfaces: List[NetworkInterface] = []

        # 1. Inspect in-process psutil interface names
        psutil_names = set()
        if HAS_PSUTIL:
            try:
                psutil_names = set(psutil.net_if_addrs().keys())
            except Exception:
                pass

        # Check if we have static metadata for all discovered interfaces
        missing_names = [n for n in psutil_names if n not in self._static_adapter_cache and not n.startswith("Loopback")]
        if missing_names or not self._static_adapter_cache:
            self._populate_static_adapter_metadata()

        default_route = self.get_default_route()
        active_if_name = default_route[0] if default_route else None

        # Build interfaces from static cache + psutil real-time status
        names_to_evaluate = list(self._static_adapter_cache.keys())
        # If psutil detected other non-cached adapters, add them
        for n in psutil_names:
            if n not in names_to_evaluate and not n.startswith("Loopback"):
                names_to_evaluate.append(n)

        for name in names_to_evaluate:
            meta = self._static_adapter_cache.get(name, {})
            friendly = meta.get("friendly_name")
            media_type = meta.get("media_type")

            if not friendly:
                n_lower = name.lower()
                if "wi-fi" in n_lower or "wireless" in n_lower or "wlan" in n_lower:
                    media_type = InterfaceMediaType.WIFI
                    friendly = f"Wi-Fi ({name})"
                elif "eth" in n_lower:
                    media_type = InterfaceMediaType.ETHERNET
                    friendly = f"Ethernet ({name})"
                else:
                    media_type = InterfaceMediaType.OTHER
                    friendly = f"Interface ({name})"

            details = self.query_interface_details(name)
            carrier = details.get("carrier", False)
            admin_enabled = details.get("admin_enabled", True)

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
                link_speed=details.get("link_speed") or meta.get("link_speed"),
            )

            if state in (InterfaceState.DISABLED, InterfaceState.OFFLINE):
                iface.clear_network_addressing()

            interfaces.append(iface)

        self._last_discovery_duration_ms = (time.monotonic() - t0) * 1000.0
        self._cache_adapters = (now, interfaces)
        return interfaces

    def query_interface_details(self, name: str) -> Dict[str, Any]:
        now = time.monotonic()
        if name in self._cache_details:
            timestamp, cached_result = self._cache_details[name]
            if now - timestamp < self._details_ttl_sec:
                if HAS_PSUTIL:
                    try:
                        stats = psutil.net_if_stats().get(name)
                        if stats:
                            cached_result["carrier"] = stats.isup
                    except Exception:
                        pass
                return dict(cached_result)

        result: Dict[str, Any] = {
            "carrier": False,
            "admin_enabled": True,
            "ip_address": None,
            "netmask": None,
            "gateway": None,
            "ssid": None,
            "link_speed": None,
        }

        # Step 1: In-process psutil for fast IP/carrier resolution (Zero Subprocesses)
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
                    if getattr(addr, "family", None) == 2 or str(addr.family) == "AddressFamily.AF_INET":
                        if addr.address and not addr.address.startswith("127."):
                            result["ip_address"] = addr.address
                            result["netmask"] = addr.netmask
                            break
            except Exception:
                pass

        # Step 2: Gateway resolution (From default route cache or route.exe)
        def_route = self.get_default_route()
        if def_route and def_route[0] == name:
            result["gateway"] = def_route[1]

        # Step 3: Wi-Fi SSID (Only if adapter is Wi-Fi and currently has carrier)
        meta = self._static_adapter_cache.get(name, {})
        is_wifi = (meta.get("media_type") == InterfaceMediaType.WIFI) or ("wi-fi" in name.lower())
        if is_wifi and result["carrier"]:
            if now - self._cached_ssid[0] < self._ssid_ttl_sec and self._cached_ssid[1]:
                result["ssid"] = self._cached_ssid[1]
            else:
                try:
                    out_wlan = _run_subprocess_hidden(["netsh", "wlan", "show", "interfaces"], timeout=1.0)
                    if out_wlan:
                        for line in out_wlan.splitlines():
                            line_clean = line.strip()
                            if line_clean.startswith("SSID") and not line_clean.startswith("BSSID"):
                                parts = line_clean.split(":", 1)
                                if len(parts) > 1:
                                    ssid_val = parts[1].strip()
                                    if ssid_val:
                                        result["ssid"] = ssid_val
                                        self._cached_ssid = (now, ssid_val)
                                        break
                except Exception:
                    pass

        self._cache_details[name] = (now, result)
        return result

    def set_interface_admin_state(self, name: str, enable: bool) -> bool:
        state_str = "ENABLED" if enable else "DISABLED"
        res = _run_subprocess_hidden(
            ["netsh", "interface", "set", "interface", f"name={name}", f"admin={state_str}"],
            timeout=2.5,
        )
        self._cache_details.pop(name, None)
        self._cache_adapters = None
        return res is not None

    def set_default_route(self, interface_name: str, gateway: str) -> bool:
        ps_cmd = f"Set-NetIPInterface -InterfaceAlias '{interface_name}' -InterfaceMetric 10 -ErrorAction Stop"
        out = self._run_ps(ps_cmd, timeout=2.5)
        self._cache_default_route = None
        return out is not None

    def get_default_route(self) -> Optional[Tuple[str, str]]:
        now = time.monotonic()
        if self._cache_default_route and (now - self._cache_default_route[0] < self._route_ttl_sec):
            return self._cache_default_route[1]

        # Attempt 1: Fast route.exe print 0.0.0.0 (Native C utility, ~10ms execution)
        route_out = _run_subprocess_hidden(["route", "print", "0.0.0.0"], timeout=1.0)
        if route_out:
            try:
                for line in route_out.splitlines():
                    parts = line.strip().split()
                    if len(parts) >= 4 and parts[0] == "0.0.0.0" and parts[1] == "0.0.0.0":
                        gw_ip = parts[2]
                        iface_ip = parts[3]
                        # Map iface_ip to adapter name via in-process psutil
                        if HAS_PSUTIL:
                            for if_name, addrs in psutil.net_if_addrs().items():
                                for a in addrs:
                                    if a.address == iface_ip:
                                        self._cache_default_route = (now, (if_name, gw_ip))
                                        return if_name, gw_ip
            except Exception:
                pass

        # Attempt 2: Fallback to PowerShell Get-NetRoute
        ps_cmd = "Get-NetRoute -DestinationPrefix '0.0.0.0/0' | Sort-Object RouteMetric | Select-Object -First 1 InterfaceAlias, NextHop | ConvertTo-Json"
        out = self._run_ps(ps_cmd, timeout=2.5)
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

    def get_instrumentation(self) -> Dict[str, Any]:
        """Provides real-time runtime monitoring metrics for debug & acceptance."""
        return {
            "subprocess_count_per_min": get_subprocess_rate_per_min(),
            "cached_adapters_count": len(self._static_adapter_cache),
            "last_discovery_duration_ms": round(self._last_discovery_duration_ms, 2),
        }
