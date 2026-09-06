import ctypes
import json
import os
import re
import subprocess
import sys
from typing import Dict, List, Optional, Tuple
import psutil

from core.models import AdapterInfo
from .base_backend import BaseNetworkBackend


CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0


class WindowsBackend(BaseNetworkBackend):
    """Windows implementation using netsh and PowerShell."""

    def is_admin(self) -> bool:
        try:
            return bool(ctypes.windll.shell32.IsUserAnAdmin() != 0)
        except Exception:
            return False

    def request_elevation(self) -> bool:
        try:
            if self.is_admin():
                return True
            script = os.path.abspath(sys.argv[0])
            params = " ".join([f'"{arg}"' for arg in sys.argv[1:]])
            ret = ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, f'"{script}" {params}', None, 1
            )
            return ret > 32
        except Exception as e:
            print(f"Failed to request Windows elevation: {e}")
            return False

    def _run_cmd(self, cmd: List[str], timeout: float = 5.0) -> Tuple[int, str, str]:
        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                creationflags=CREATE_NO_WINDOW,
            )
            return res.returncode, res.stdout, res.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Command timed out"
        except Exception as e:
            return -1, "", str(e)

    def get_all_adapters(self) -> List[AdapterInfo]:
        adapters: Dict[str, AdapterInfo] = {}

        # 0. Query detailed adapter hardware info via PowerShell Get-NetAdapter
        ps_adapters_info: Dict[str, dict] = {}
        ps_cmd = [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            "Get-NetAdapter | Select-Object Name, InterfaceDescription, Status, MediaType, PhysicalMediaType | ConvertTo-Json",
        ]
        ret_ps, out_ps, _ = self._run_cmd(ps_cmd, timeout=4.0)
        if ret_ps == 0 and out_ps.strip():
            try:
                raw = json.loads(out_ps.strip())
                items = raw if isinstance(raw, list) else [raw]
                for item in items:
                    name = item.get("Name", "")
                    if name:
                        ps_adapters_info[name.strip().lower()] = item
            except Exception:
                pass

        # 0b. Query admin states via 'netsh interface show interface'
        admin_states: Dict[str, bool] = {}
        ret_admin, out_admin, _ = self._run_cmd(["netsh", "interface", "show", "interface"])
        if ret_admin == 0:
            for line in out_admin.splitlines():
                line = line.strip()
                if line.startswith("Enabled") or line.startswith("Disabled"):
                    parts = line.split(None, 3)
                    if len(parts) >= 4:
                        admin_states[parts[3].strip()] = (parts[0].lower() == "enabled")

        # 1. Parse 'netsh interface ipv4 show interfaces'
        ret, stdout, _ = self._run_cmd(["netsh", "interface", "ipv4", "show", "interfaces"])
        if ret == 0:
            lines = stdout.strip().splitlines()
            for line in lines:
                line_str = line.strip()
                if not line_str or line_str.startswith("---") or line_str.startswith("Idx"):
                    continue
                parts = line_str.split(None, 4)
                if len(parts) >= 5:
                    try:
                        idx = int(parts[0])
                        metric = int(parts[1])
                        state_str = parts[3].lower()
                        name = parts[4].strip()
                        name_lower = name.lower()

                        # Exclude virtual, loopback, Wi-Fi Direct, and Bluetooth adapters
                        if (
                            "loopback" in name_lower
                            or name_lower.startswith("local area connection*")
                            or "bluetooth" in name_lower
                            or "vethernet" in name_lower
                            or "teredo" in name_lower
                            or "isatap" in name_lower
                        ):
                            continue

                        # Check PowerShell hardware info
                        ps_info = ps_adapters_info.get(name_lower, {})
                        desc = ps_info.get("InterfaceDescription", "")
                        desc_lower = desc.lower()
                        phys_media = ps_info.get("PhysicalMediaType", "")

                        # Filter out virtual/Bluetooth via description/media
                        if (
                            "bluetooth" in desc_lower
                            or "virtual" in desc_lower
                            or "hyper-v" in desc_lower
                            or "wi-fi direct" in desc_lower
                            or "microsoft wi-fi" in desc_lower
                            or phys_media == "BlueTooth"
                        ):
                            continue

                        # Determine adapter type
                        is_wifi = (
                            phys_media == "Native 802.11"
                            or "wi-fi" in name_lower
                            or "wireless" in name_lower
                            or "wi-fi" in desc_lower
                            or "wireless" in desc_lower
                            or "802.11" in desc_lower
                        )
                        adapter_type = "Wireless" if is_wifi else "Ethernet"

                        adapters[name] = AdapterInfo(
                            alias=name,
                            index=idx,
                            metric=metric,
                            is_connected=(state_str == "connected"),
                            is_admin_enabled=admin_states.get(name, True),
                            adapter_type=adapter_type,
                            description=desc,
                            physical_media_type=phys_media,
                            is_physical=True,
                        )
                    except (ValueError, IndexError):
                        continue

        # 2. Enrich with psutil IPv4
        try:
            ps_addrs = psutil.net_if_addrs()
            for name, addrs in ps_addrs.items():
                target_adapter = adapters.get(name)
                if not target_adapter:
                    continue
                for addr in addrs:
                    if addr.family.name == "AF_INET":
                        if not target_adapter.ipv4 or not target_adapter.ipv4.startswith("169.254."):
                            if not addr.address.startswith("169.254."):
                                target_adapter.ipv4 = addr.address
                            elif not target_adapter.ipv4:
                                target_adapter.ipv4 = addr.address
        except Exception:
            pass

        # 3. Enrich gateway and metric via netsh show addresses
        for name, adapter in list(adapters.items()):
            ret, out, _ = self._run_cmd(["netsh", "interface", "ipv4", "show", "addresses", name])
            if ret == 0:
                ip_match = re.search(r"IP Address:\s+([0-9.]+)", out)
                gw_match = re.search(r"Default Gateway:\s+([0-9.]+)", out)
                met_match = re.search(r"InterfaceMetric:\s+([0-9]+)", out)

                if ip_match and not adapter.ipv4:
                    adapter.ipv4 = ip_match.group(1)
                if gw_match:
                    adapter.gateway = gw_match.group(1)
                if met_match:
                    try:
                        adapter.metric = int(met_match.group(1))
                    except ValueError:
                        pass

        return list(adapters.values())

    def set_interface_metric(self, alias: str, metric: int) -> Tuple[bool, str]:
        if not alias:
            return False, "Empty interface alias"

        cmd = ["netsh", "interface", "ipv4", "set", "interface", alias, f"metric={metric}", "store=active"]
        code, stdout, stderr = self._run_cmd(cmd)

        if code == 0:
            return True, f"Successfully set metric={metric} on '{alias}'"
        else:
            msg = stderr.strip() or stdout.strip() or f"Command failed with code {code}"
            return False, f"Failed to set metric on '{alias}': {msg}"

    def set_network_priority_order(self, ordered_aliases: List[str]) -> Tuple[bool, str]:
        # On Windows, setting priority translates to assigning ascending metrics
        base_metric = 10
        errors = []
        for i, alias in enumerate(ordered_aliases):
            if alias:
                m = base_metric + (i * 10)
                ok, msg = self.set_interface_metric(alias, m)
                if not ok:
                    errors.append(msg)
        if errors:
            return False, "; ".join(errors)
        return True, "Priority metrics updated successfully"

    def restore_defaults(self, aliases: List[str]) -> List[Tuple[str, bool, str]]:
        results = []
        for alias in aliases:
            if not alias:
                continue
            ps_script = f"Set-NetIPInterface -InterfaceAlias '{alias}' -AddressFamily IPv4 -AutomaticMetric Enabled"
            cmd = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script]
            code, stdout, stderr = self._run_cmd(cmd, timeout=8.0)
            if code == 0:
                results.append((alias, True, f"Restored Automatic Metric on '{alias}'"))
            else:
                msg = stderr.strip() or stdout.strip() or f"PowerShell failed with code {code}"
                results.append((alias, False, f"Failed to restore Automatic Metric on '{alias}': {msg}"))
        return results

    def set_adapter_enabled(self, alias: str, enabled: bool) -> Tuple[bool, str]:
        if not alias:
            return False, "Empty interface alias"

        state_str = "ENABLED" if enabled else "DISABLED"
        cmd = ["netsh", "interface", "set", "interface", f"name={alias}", f"admin={state_str}"]
        code, stdout, stderr = self._run_cmd(cmd, timeout=6.0)

        if code == 0:
            return True, f"Interface '{alias}' is now {state_str.lower()}"

        # Fallback to PowerShell Enable-NetAdapter / Disable-NetAdapter
        ps_cmd = "Enable-NetAdapter" if enabled else "Disable-NetAdapter"
        ps_script = f"{ps_cmd} -Name '{alias}' -Confirm:$false"
        p_code, p_out, p_err = self._run_cmd(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
            timeout=8.0,
        )
        if p_code == 0:
            return True, f"Interface '{alias}' is now {state_str.lower()}"

        err_msg = p_err.strip() or stderr.strip() or f"Failed with code {code}"
        return False, f"Failed to toggle interface '{alias}': {err_msg}"
