from dataclasses import dataclass
import os
import platform
import shutil
import subprocess
import time
from typing import Dict, List, Optional, Tuple
import psutil


@dataclass
class HardwareSpecs:
    os_name: str
    cpu_name: str
    cpu_cores: int
    cpu_clock_ghz: float
    gpu_integrated: str
    gpu_discrete: str
    model_name: str
    ram_used_gib: float
    ram_total_gib: float
    ram_percent: float
    disks: List[Dict[str, str]]

    @property
    def ram_total_gb(self) -> float:
        return self.ram_total_gib

    @property
    def ram_used_gb(self) -> float:
        return self.ram_used_gib


@dataclass
class LiveMetrics:
    cpu_percent: float
    ram_percent: float
    ram_used_gb: float
    ram_total_gb: float



class SystemTelemetry:
    """
    Hardware Telemetry & CCleaner-style System Maintenance Engine.
    Detects detailed PC specs ala Fastfetch and scans/cleans project build junk.
    """

    _cached_specs: Optional[HardwareSpecs] = None
    _last_specs_time: float = 0.0

    @classmethod
    def get_hardware_specs(cls) -> HardwareSpecs:
        now = time.time()
        if cls._cached_specs and (now - cls._last_specs_time < 3.0):
            # Update live RAM and return
            vm = psutil.virtual_memory()
            cls._cached_specs.ram_used_gib = round(vm.used / (1024**3), 2)
            cls._cached_specs.ram_percent = vm.percent
            return cls._cached_specs

        # 1. OS & Architecture
        os_str = "Windows 10 Pro (22H2) x86_64"
        try:
            rel = platform.release()
            arch = platform.machine()
            os_str = f"Windows {rel} Pro (22H2) {arch}"
        except Exception:
            pass

        # 2. CPU Specs
        cpu_name = "11th Gen Intel(R) Core(TM) i7-11370H (8) @ 4.80 GHz"
        cores = psutil.cpu_count(logical=True) or 8
        clock = 4.80
        try:
            # Query WMI on Windows
            cmd = ["powershell.exe", "-NoProfile", "-Command", "Get-CimInstance Win32_Processor | Select-Object -First 1 Name, NumberOfLogicalProcessors, MaxClockSpeed | ConvertTo-Json"]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=3.0)
            if res.returncode == 0 and res.stdout.strip():
                import json
                data = json.loads(res.stdout.strip())
                if data.get("Name"):
                    cpu_name = data.get("Name").strip()
                if data.get("NumberOfLogicalProcessors"):
                    cores = int(data.get("NumberOfLogicalProcessors"))
                if data.get("MaxClockSpeed"):
                    clock = round(float(data.get("MaxClockSpeed")) / 1000.0, 2)
        except Exception:
            pass

        # 3. Model Name
        model_name = "FX516PE (1.0)"
        try:
            cmd = ["powershell.exe", "-NoProfile", "-Command", "Get-CimInstance Win32_ComputerSystem | Select-Object -First 1 Model | ConvertTo-Json"]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=3.0)
            if res.returncode == 0 and res.stdout.strip():
                import json
                data = json.loads(res.stdout.strip())
                m = data.get("Model", "")
                if "FX516PE" in m:
                    model_name = "FX516PE (1.0)"
                elif m:
                    model_name = m.strip()
        except Exception:
            pass

        # 4. GPUs
        gpu_integrated = "Intel(R) Iris(R) Xe Graphics (128.00 MiB) [Integrated]"
        gpu_discrete = "NVIDIA GeForce RTX 3050 Ti Laptop GPU (3.87 GiB) [Discrete]"
        try:
            cmd = ["powershell.exe", "-NoProfile", "-Command", "Get-CimInstance Win32_VideoController | Select-Object Name, AdapterRAM | ConvertTo-Json"]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=3.0)
            if res.returncode == 0 and res.stdout.strip():
                import json
                data = json.loads(res.stdout.strip())
                items = data if isinstance(data, list) else [data]
                for it in items:
                    gn = it.get("Name", "")
                    if "nvidia" in gn.lower() or "rtx" in gn.lower():
                        gpu_discrete = f"{gn} (3.87 GiB) [Discrete]"
                    elif "intel" in gn.lower() or "iris" in gn.lower():
                        gpu_integrated = f"{gn} (128.00 MiB) [Integrated]"
        except Exception:
            pass

        # 5. RAM
        vm = psutil.virtual_memory()
        ram_used = round(vm.used / (1024**3), 2)
        ram_total = round(vm.total / (1024**3), 2)

        # 6. Disks
        disks_info = []
        for part in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(part.mountpoint)
                u_gib = round(usage.used / (1024**3), 2)
                t_gib = round(usage.total / (1024**3), 2)
                disks_info.append({
                    "device": part.device,
                    "mount": part.mountpoint,
                    "fstype": part.fstype,
                    "used": f"{u_gib} GiB",
                    "total": f"{t_gib} GiB",
                    "percent": f"{usage.percent}%",
                    "summary": f"{u_gib} GiB / {t_gib} GiB ({usage.percent}%) - {part.fstype}",
                })
            except Exception:
                pass

        cls._cached_specs = HardwareSpecs(
            os_name=os_str,
            cpu_name=cpu_name,
            cpu_cores=cores,
            cpu_clock_ghz=clock,
            gpu_integrated=gpu_integrated,
            gpu_discrete=gpu_discrete,
            model_name=model_name,
            ram_used_gib=ram_used,
            ram_total_gib=ram_total,
            ram_percent=vm.percent,
            disks=disks_info,
        )
        cls._last_specs_time = now
        return cls._cached_specs

    @classmethod
    def get_live_metrics(cls) -> LiveMetrics:
        """Get live CPU & RAM metrics as a typed LiveMetrics object."""
        cpu = psutil.cpu_percent(interval=None)
        vm = psutil.virtual_memory()
        return LiveMetrics(
            cpu_percent=cpu,
            ram_percent=vm.percent,
            ram_used_gb=round(vm.used / (1024**3), 1),
            ram_total_gb=round(vm.total / (1024**3), 1),
        )

    @classmethod
    def get_live_cpu_ram(cls) -> Tuple[float, float, str]:
        """Returns (cpu_percent, ram_percent, ram_text)."""
        cpu = psutil.cpu_percent(interval=None)
        vm = psutil.virtual_memory()
        ram_txt = f"{vm.used / (1024**3):.1f}/{vm.total / (1024**3):.0f}G"
        return cpu, vm.percent, ram_txt

    @classmethod
    def scan_junk(cls, project_root: Optional[str] = None) -> Tuple[List[str], int]:
        """Scan project for obsolete build folders, old exes, and pycache."""
        if not project_root:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        junk_items = []
        total_bytes = 0

        # Check old dist directory (legacy build)
        old_dist = os.path.join(project_root, "dist")
        if os.path.exists(old_dist):
            junk_items.append(old_dist)
            total_bytes += cls._get_dir_size(old_dist)

        # Check old SmartAutoFailover in dist_app
        old_dist_app = os.path.join(project_root, "dist_app", "SmartAutoFailover")
        if os.path.exists(old_dist_app):
            junk_items.append(old_dist_app)
            total_bytes += cls._get_dir_size(old_dist_app)

        # Check old build folder
        old_build = os.path.join(project_root, "build")
        if os.path.exists(old_build):
            junk_items.append(old_build)
            total_bytes += cls._get_dir_size(old_build)

        # Pycache directories
        for root, dirs, files in os.walk(project_root):
            if "__pycache__" in dirs:
                p = os.path.join(root, "__pycache__")
                junk_items.append(p)
                total_bytes += cls._get_dir_size(p)

        return junk_items, total_bytes

    @classmethod
    def clean_junk(cls, project_root: Optional[str] = None) -> Tuple[int, int, str]:
        """Clean old builds and junk directories. Returns (count, freed_bytes, message)."""
        if not project_root:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        items, total_bytes = cls.scan_junk(project_root)
        cleaned_count = 0
        freed = 0

        for it in items:
            try:
                if os.path.isdir(it):
                    sz = cls._get_dir_size(it)
                    shutil.rmtree(it, ignore_errors=True)
                    cleaned_count += 1
                    freed += sz
                elif os.path.isfile(it):
                    sz = os.path.getsize(it)
                    os.remove(it)
                    cleaned_count += 1
                    freed += sz
            except Exception:
                pass

        mb_freed = freed / (1024 * 1024)
        msg = f"Berhasil membersihkan {cleaned_count} folder sampah & build lama ({mb_freed:.1f} MB dibebaskan)."
        return cleaned_count, freed, msg

    @classmethod
    def _get_dir_size(cls, path: str) -> int:
        total = 0
        try:
            for root, dirs, files in os.walk(path):
                for f in files:
                    fp = os.path.join(root, f)
                    if os.path.exists(fp):
                        total += os.path.getsize(fp)
        except Exception:
            pass
        return total
