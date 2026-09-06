import os
import re
import subprocess
import sys
from typing import Dict, List, Optional, Tuple
import psutil

from core.models import AdapterInfo
from .base_backend import BaseNetworkBackend


class MacOSBackend(BaseNetworkBackend):
    """
    macOS implementation using networksetup, scutil, and BSD routing commands.
    """

    def __init__(self):
        self._initial_service_order: List[str] = []
        self._device_map: Dict[str, str] = {}  # service_name -> en0/en1
        self._refresh_device_map()

    def is_admin(self) -> bool:
        try:
            return os.geteuid() == 0
        except AttributeError:
            # On non-unix or mocked env
            return False

    def request_elevation(self) -> bool:
        if self.is_admin():
            return True
        try:
            script = os.path.abspath(sys.argv[0])
            params = " ".join([f"'{arg}'" for arg in sys.argv[1:]])
            apple_script = f'do shell script "python3 \'{script}\' {params}" with administrator privileges'
            cmd = ["osascript", "-e", apple_script]
            ret = subprocess.call(cmd)
            return ret == 0
        except Exception as e:
            print(f"Failed to request macOS elevation: {e}")
            return False

    def _run_cmd(self, cmd: List[str], timeout: float = 5.0) -> Tuple[int, str, str]:
        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return res.returncode, res.stdout, res.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Command timed out"
        except Exception as e:
            return -1, "", str(e)

    def _refresh_device_map(self):
        """Parse networksetup -listnetworkserviceorder to map service names to enX devices."""
        ret, stdout, _ = self._run_cmd(["networksetup", "-listnetworkserviceorder"])
        if ret != 0:
            return

        # Output format:
        # (1) Wi-Fi
        # (Hardware Port: Wi-Fi, Device: en0)
        # (2) Thunderbolt Ethernet
        # (Hardware Port: Thunderbolt Ethernet, Device: en1)
        current_service = None
        self._initial_service_order = []
        self._device_map = {}

        for line in stdout.splitlines():
            line = line.strip()
            svc_match = re.match(r"^\([0-9]+\)\s+(.*)$", line)
            if svc_match:
                current_service = svc_match.group(1).strip()
                if not current_service.startswith("*"):  # Asterisk denotes disabled
                    self._initial_service_order.append(current_service)
                continue

            dev_match = re.search(r"Device:\s*([a-zA-Z0-9]+)", line)
            if dev_match and current_service:
                self._device_map[current_service] = dev_match.group(1)

    def get_all_adapters(self) -> List[AdapterInfo]:
        self._refresh_device_map()
        adapters: Dict[str, AdapterInfo] = {}

        # Query all active services
        ret, stdout, _ = self._run_cmd(["networksetup", "-listallnetworkservices"])
        services = []
        if ret == 0:
            for line in stdout.splitlines():
                line = line.strip()
                if not line or "asterisk" in line.lower() or line.startswith("*"):
                    continue
                services.append(line)

        # Query psutil for device IPs and stats
        ps_addrs = psutil.net_if_addrs()
        ps_stats = psutil.net_if_stats()

        # Query default gateway via route -n get default
        default_gw = ""
        gw_ret, gw_out, _ = self._run_cmd(["route", "-n", "get", "default"])
        if gw_ret == 0:
            gw_match = re.search(r"gateway:\s+([0-9.]+)", gw_out)
            if gw_match:
                default_gw = gw_match.group(1)

        for svc in services:
            dev = self._device_map.get(svc, "")
            ipv4 = ""
            is_connected = False

            if dev and dev in ps_addrs:
                for addr in ps_addrs[dev]:
                    if addr.family.name == "AF_INET":
                        if not addr.address.startswith("169.254."):
                            ipv4 = addr.address
                            break
                        elif not ipv4:
                            ipv4 = addr.address

            if dev and dev in ps_stats:
                is_connected = ps_stats[dev].isup and bool(ipv4)

            # Query router IP for service if available
            svc_gw = default_gw
            r_ret, r_out, _ = self._run_cmd(["networksetup", "-getinfo", svc])
            if r_ret == 0:
                r_match = re.search(r"Router:\s+([0-9.]+)", r_out)
                if r_match:
                    svc_gw = r_match.group(1)
                ip_match = re.search(r"IP address:\s+([0-9.]+)", r_out)
                if ip_match and not ipv4:
                    ipv4 = ip_match.group(1)

            is_wifi = "wi-fi" in svc.lower() or "airport" in svc.lower()
            adapters[svc] = AdapterInfo(
                alias=svc,
                index=int(dev.replace("en", "")) if dev.startswith("en") and dev[2:].isdigit() else 0,
                ipv4=ipv4,
                gateway=svc_gw,
                is_connected=is_connected,
                metric=10 if svc == self._initial_service_order[0:1] else 20,
                adapter_type="Wireless" if is_wifi else "Ethernet",
            )

        return list(adapters.values())

    def set_network_priority_order(self, ordered_aliases: List[str]) -> Tuple[bool, str]:
        """
        Reorder network services in macOS.
        The top service becomes the primary default route for all traffic including Zoom.
        """
        if not ordered_aliases:
            return False, "No services to order"

        # networksetup -ordernetworkservices requires all services to be present in order
        all_services = list(self._initial_service_order)
        new_order = [s for s in ordered_aliases if s in all_services]
        for s in all_services:
            if s not in new_order:
                new_order.append(s)

        cmd = ["networksetup", "-ordernetworkservices"] + new_order
        code, stdout, stderr = self._run_cmd(cmd)

        if code == 0:
            # Also update kernel default route immediately to primary device
            primary_svc = new_order[0]
            primary_dev = self._device_map.get(primary_svc)
            if primary_dev:
                self._run_cmd(["route", "change", "default", "-interface", primary_dev])
            return True, f"macOS Network Service Order updated: {', '.join(new_order[:3])}"
        else:
            msg = stderr.strip() or stdout.strip() or f"Code {code}"
            return False, f"Failed to order network services: {msg}"

    def set_interface_metric(self, alias: str, metric: int) -> Tuple[bool, str]:
        # On macOS, metric is simulated via priority order
        return True, f"Metric {metric} mapped to service '{alias}'"

    def restore_defaults(self, aliases: List[str]) -> List[Tuple[str, bool, str]]:
        if self._initial_service_order:
            cmd = ["networksetup", "-ordernetworkservices"] + self._initial_service_order
            code, stdout, stderr = self._run_cmd(cmd)
            if code == 0:
                return [(s, True, "Restored original service order") for s in aliases]
            else:
                return [(s, False, stderr.strip() or stdout.strip()) for s in aliases]
        return [(s, True, "Default state maintained") for s in aliases]

    def set_adapter_enabled(self, alias: str, enabled: bool) -> Tuple[bool, str]:
        if not alias:
            return False, "Empty service alias"

        state_str = "on" if enabled else "off"
        cmd = ["networksetup", "-setnetworkserviceenabled", alias, state_str]
        code, stdout, stderr = self._run_cmd(cmd)

        if code == 0:
            dev = self._device_map.get(alias)
            if dev:
                self._run_cmd(["ifconfig", dev, "up" if enabled else "down"])
            return True, f"macOS service '{alias}' is now {state_str}"

        err_msg = stderr.strip() or stdout.strip() or f"Code {code}"
        return False, f"Failed to toggle macOS service '{alias}': {err_msg}"
