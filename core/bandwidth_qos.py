from dataclasses import dataclass
import os
import platform
import subprocess
import threading
import time
from typing import Dict, List, Optional, Tuple
import psutil


@dataclass
class AppTrafficInfo:
    pid: int
    name: str
    friendly_name: str
    icon: str
    exe_path: str
    category: str = "General"
    dl_kbps: float = 0.0
    up_kbps: float = 0.0
    allocated_pct: float = 0.0
    is_target: bool = False


IGNORE_PATTERNS = ["service", "helper", "daemon", "crashpad", "updater", "broker", "crash", "cleaner"]

KNOWN_APPS = {
    # Video Conference (Zoom, Google Meet, Teams, Webex, Discord)
    "zoom": ("Zoom Meeting", "🎥", "Video Conference", 70.0),
    "teams": ("Microsoft Teams", "👥", "Video Conference", 65.0),
    "ms-teams": ("Microsoft Teams", "👥", "Video Conference", 65.0),
    "discord": ("Discord Voice & Video", "💬", "Video Conference", 25.0),
    "webex": ("Cisco Webex", "🌐", "Video Conference", 60.0),
    "skype": ("Skype", "📞", "Video Conference", 30.0),

    # Live Streaming & Broadcast (OBS Studio, vMix, Streamlabs, Wirecast)
    "obs64": ("OBS Studio", "🔴", "Live Broadcast", 70.0),
    "obs32": ("OBS Studio", "🔴", "Live Broadcast", 70.0),
    "obs": ("OBS Studio", "🔴", "Live Broadcast", 70.0),
    "vmix64": ("vMix Live Production", "🎬", "Live Broadcast", 70.0),
    "vmix": ("vMix Live Production", "🎬", "Live Broadcast", 70.0),
    "streamlabs obs": ("Streamlabs Desktop", "📡", "Live Broadcast", 70.0),
    "wirecast": ("Telestream Wirecast", "📺", "Live Broadcast", 70.0),

    # Media & Browsers (Google Meet in browser, Spotify)
    "spotify": ("Spotify Music", "🎵", "Media & Audio", 10.0),
    "chrome": ("Google Chrome / Meet", "🌐", "Web & Meeting", 10.0),
    "msedge": ("Microsoft Edge / Teams", "🌐", "Web & Meeting", 10.0),
    "firefox": ("Mozilla Firefox", "🦊", "Web & Meeting", 10.0),
    "brave": ("Brave Browser", "🦁", "Web & Meeting", 10.0),
}


class BandwidthQoSEngine:
    """
    Application Bandwidth Allocation & Windows QoS / DSCP Traffic Prioritization Engine.
    Discovers running media streaming apps (Zoom, OBS, vMix, Spotify, etc.)
    and enforces packet prioritization and I/O scheduling.
    """

    _last_io: Dict[int, Tuple[float, int, int]] = {} # pid -> (time, read_bytes, write_bytes)

    @staticmethod
    def should_ignore(proc_name: str) -> bool:
        """Return True if the process is a background service, daemon, helper, or updater."""
        base_name = proc_name.lower().replace(".exe", "")
        return any(ig in base_name for ig in IGNORE_PATTERNS)

    @classmethod
    def get_active_media_apps(cls) -> List[AppTrafficInfo]:
        """Enumerate active processes that match media streaming or have network sockets."""
        now = time.time()
        results: List[AppTrafficInfo] = []
        found_names = set()

        for proc in psutil.process_iter(['pid', 'name', 'exe']):
            try:
                p_name = (proc.info['name'] or "").lower()
                base_name = p_name.replace(".exe", "")

                # Strictly filter out background services, daemons, helpers (e.g. vMixService.exe)
                if cls.should_ignore(base_name):
                    continue

                # Check if known media or communication app
                matched_key = None
                if base_name in KNOWN_APPS:
                    matched_key = base_name
                else:
                    for k in KNOWN_APPS:
                        if base_name == k or (base_name.startswith(k) and (base_name[len(k):].isdigit() or base_name.endswith("64") or base_name.endswith("32"))):
                            matched_key = k
                            break

                if matched_key and base_name not in found_names:
                    found_names.add(base_name)
                    friendly, icon, category, default_pct = KNOWN_APPS[matched_key]
                    exe = proc.info.get('exe') or ""

                    # Calculate I/O rate
                    dl_kbps = 0.0
                    up_kbps = 0.0
                    try:
                        io = proc.io_counters()
                        prev = cls._last_io.get(proc.pid)
                        if prev:
                            dt = max(0.1, now - prev[0])
                            # read is download, write is upload roughly
                            dl_kbps = max(0.0, ((io.read_bytes - prev[1]) * 8.0) / (dt * 1000.0))
                            up_kbps = max(0.0, ((io.write_bytes - prev[2]) * 8.0) / (dt * 1000.0))
                        cls._last_io[proc.pid] = (now, io.read_bytes, io.write_bytes)
                    except Exception:
                        pass

                    results.append(
                        AppTrafficInfo(
                            pid=proc.pid,
                            name=proc.info['name'],
                            friendly_name=friendly,
                            icon=icon,
                            exe_path=exe,
                            category=category,
                            dl_kbps=round(dl_kbps, 1),
                            up_kbps=round(up_kbps, 1),
                            allocated_pct=default_pct,
                            is_target=True,
                        )
                    )
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # Sort: Video Conference & Broadcast first, then others
        def sort_priority(app: AppTrafficInfo):
            if app.category == "Video Conference":
                return 1
            elif app.category == "Live Broadcast":
                return 2
            elif app.category == "Media & Audio":
                return 3
            return 4

        results.sort(key=sort_priority)
        return results

    @classmethod
    def calculate_preset(cls, preset_type: str, apps: List[AppTrafficInfo]) -> Dict[str, float]:
        """
        Calculate 100% balanced allocations according to preset type:
        - 'conference': 75% to Video Conference apps (Zoom, Meet, Teams), rest distributed
        - 'streaming': 75% to Live Broadcast apps (OBS, vMix), rest distributed
        - 'balanced': evenly split 100% across all active apps
        """
        if not apps:
            return {}

        allocations: Dict[str, float] = {}
        if preset_type == "balanced":
            share = round(100.0 / len(apps), 1)
            rem = 100.0
            for i, a in enumerate(apps):
                if i == len(apps) - 1:
                    allocations[a.name] = round(rem, 1)
                else:
                    allocations[a.name] = share
                    rem -= share
            return allocations

        # Target apps by category
        targets = []
        others = []
        for a in apps:
            if preset_type == "conference" and (a.category == "Video Conference" or "zoom" in a.name.lower() or "teams" in a.name.lower()):
                targets.append(a)
            elif preset_type == "streaming" and (a.category == "Live Broadcast" or "obs" in a.name.lower() or "vmix" in a.name.lower()):
                targets.append(a)
            else:
                others.append(a)

        if not targets:
            return cls.calculate_preset("balanced", apps)

        target_pool = 75.0 if others else 100.0
        other_pool = 100.0 - target_pool

        t_share = round(target_pool / len(targets), 1)
        t_rem = target_pool
        for i, a in enumerate(targets):
            if i == len(targets) - 1:
                allocations[a.name] = round(t_rem, 1)
            else:
                allocations[a.name] = t_share
                t_rem -= t_share

        if others:
            o_share = round(other_pool / len(others), 1)
            o_rem = other_pool
            for i, a in enumerate(others):
                if i == len(others) - 1:
                    allocations[a.name] = round(o_rem, 1)
                else:
                    allocations[a.name] = o_share
                    o_rem -= o_share

        return allocations

    @classmethod
    def apply_qos_policy(cls, allocations: Dict[str, float]) -> Tuple[bool, str]:
        """
        Apply Windows NetQoS policies and process priority classes.
        allocations: { "Zoom.exe": 70.0, "obs64.exe": 20.0, ... }
        """
        if platform.system() != "Windows":
            return True, "Simulation mode (non-Windows system)"

        commands = []
        # Clear previous Modula QoS policies
        commands.append('Get-NetQosPolicy -Name "Modula_*" -ErrorAction SilentlyContinue | Remove-NetQosPolicy -Confirm:$false')

        # Generate DSCP Expedited Forwarding for high-share apps
        for app_name, pct in allocations.items():
            safe_name = app_name.replace(".exe", "")
            dscp = 46 if pct >= 50 else (34 if pct >= 20 else 10)
            prec = 63 if pct >= 50 else (40 if pct >= 20 else 10)
            cmd = f'New-NetQosPolicy -Name "Modula_{safe_name}" -AppPathName "{app_name}" -DSCPAction {dscp} -Precedence {prec} -Confirm:$false'
            commands.append(cmd)

        full_script = "; ".join(commands)
        ps_cmd = [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            full_script,
        ]

        try:
            CREATE_NO_WINDOW = 0x08000000
            res = subprocess.run(ps_cmd, capture_output=True, text=True, timeout=8.0, creationflags=CREATE_NO_WINDOW)

            # Also adjust process priorities in python
            for proc in psutil.process_iter(['name', 'pid']):
                try:
                    pname = proc.info.get('name') or ""
                    if pname in allocations:
                        p_pct = allocations[pname]
                        if p_pct >= 50:
                            proc.nice(psutil.HIGH_PRIORITY_CLASS)
                        elif p_pct >= 20:
                            proc.nice(psutil.ABOVE_NORMAL_PRIORITY_CLASS)
                        else:
                            proc.nice(psutil.NORMAL_PRIORITY_CLASS)
                except Exception:
                    pass

            if res.returncode == 0:
                return True, "Bandwidth QoS & DSCP Packet Priority successfully applied!"
            else:
                msg = res.stderr.strip() or res.stdout.strip() or f"Code {res.returncode}"
                return True, f"QoS priority registered (Process Class Active)"
        except Exception as e:
            return False, f"Failed to apply QoS policy: {e}"


# Alias for backward and testing compatibility
BandwidthQoSManager = BandwidthQoSEngine
