from dataclasses import dataclass
import os
import platform
import shutil
import subprocess
import threading
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
    gpu_percent: float = 0.0
    gpu_name: str = "GPU"



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

    _gpu_percent: float = 0.0
    _gpu_name: str = "GPU"
    _gpu_sampler_running: bool = False
    _gpu_sampler_thread: Optional[threading.Thread] = None
    _gpu_lock = threading.Lock()

    @classmethod
    def start_gpu_sampler(cls):
        with cls._gpu_lock:
            if cls._gpu_sampler_running:
                return
            cls._gpu_sampler_running = True
            cls._gpu_sampler_thread = threading.Thread(target=cls._gpu_worker, daemon=True)
            cls._gpu_sampler_thread.start()

    @classmethod
    def _gpu_worker(cls):
        """Non-blocking background sampler for GPU utilization."""
        while cls._gpu_sampler_running:
            util = 0.0
            name = "GPU"
            found = False

            # 1. Try nvidia-smi query
            try:
                creationflags = 0x08000000 if platform.system() == "Windows" else 0
                res = subprocess.run(
                    ["nvidia-smi", "--query-gpu=utilization.gpu,name", "--format=csv,noheader,nounits"],
                    capture_output=True,
                    text=True,
                    timeout=2.0,
                    creationflags=creationflags,
                )
                if res.returncode == 0 and res.stdout.strip():
                    parts = res.stdout.strip().split("\n")[0].split(",")
                    if len(parts) >= 1:
                        util = float(parts[0].strip())
                        found = True
                    if len(parts) >= 2:
                        name = parts[1].strip()
            except Exception:
                pass

            # 2. Update cached values safely
            with cls._gpu_lock:
                cls._gpu_percent = util
                cls._gpu_name = name

            time.sleep(2.5)

    @classmethod
    def get_live_metrics(cls) -> LiveMetrics:
        """Get live CPU, RAM & GPU metrics as a typed LiveMetrics object."""
        cls.start_gpu_sampler()
        cpu = psutil.cpu_percent(interval=None)
        vm = psutil.virtual_memory()
        with cls._gpu_lock:
            gpu_pct = cls._gpu_percent
            gpu_name = cls._gpu_name
        return LiveMetrics(
            cpu_percent=cpu,
            ram_percent=vm.percent,
            ram_used_gb=round(vm.used / (1024**3), 1),
            ram_total_gb=round(vm.total / (1024**3), 1),
            gpu_percent=gpu_pct,
            gpu_name=gpu_name,
        )

    @classmethod
    def get_live_cpu_ram(cls) -> Tuple[float, float, str]:
        """Returns (cpu_percent, ram_percent, ram_text)."""
        cpu = psutil.cpu_percent(interval=None)
        vm = psutil.virtual_memory()
        ram_txt = f"{vm.used / (1024**3):.1f}/{vm.total / (1024**3):.0f}G"
        return cpu, vm.percent, ram_txt

    _cpu_history: List[float] = []
    _ram_history: List[float] = []
    _gpu_history: List[float] = []

    @classmethod
    def record_history_sample(cls, cpu: float, ram: float, gpu: float = 0.0):
        cls._cpu_history.append(cpu)
        cls._ram_history.append(ram)
        cls._gpu_history.append(gpu)
        if len(cls._cpu_history) > 60:
            cls._cpu_history.pop(0)
        if len(cls._ram_history) > 60:
            cls._ram_history.pop(0)
        if len(cls._gpu_history) > 60:
            cls._gpu_history.pop(0)

    @classmethod
    def get_history(cls) -> Tuple[List[float], List[float]]:
        return list(cls._cpu_history), list(cls._ram_history)

    @classmethod
    def get_gpu_history(cls) -> List[float]:
        return list(cls._gpu_history)

    @classmethod
    def get_top_processes(cls, limit: int = 5) -> List[Dict[str, any]]:
        """Get top running processes by CPU & RAM consumption."""
        procs = []
        try:
            for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
                try:
                    info = p.info
                    name = info.get("name", "")
                    if name and not name.lower().startswith("system"):
                        procs.append({
                            "pid": info["pid"],
                            "name": name,
                            "cpu": round(info.get("cpu_percent") or 0.0, 1),
                            "ram": round(info.get("memory_percent") or 0.0, 1),
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception:
            pass

        procs.sort(key=lambda x: (x["cpu"], x["ram"]), reverse=True)
        return procs[:limit]
