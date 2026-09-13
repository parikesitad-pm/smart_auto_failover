# AutoFailover 3.0.1

> by Modula • _light seamless and usefull_
>
> 🚀 **Current Release: [AutoFailover 3.0.1 (v3.0.1)](https://github.com/parikesitad-pm/smart_auto_failover/releases/tag/v3.0.1)** — Multi-platform desktop packages verified with 5-case failover hierarchy and live workload protection.

AutoFailover 3.0.1 protects active real-time workloads (Zoom, OBS Studio, Microsoft Teams, Google Meet, vMix) by autonomously detecting network path degradation and switching seamlessly to healthy backup paths.

## Failover Priority & Workload Protection Rules

1. **Online Priority**: Physical Ethernet (`eth`) is strictly prioritized over Wi-Fi.
2. **Case 5 (Normal State)**: When `eth0`, `eth1`, and `wifi` are connected and healthy, `eth0` is prioritized as the primary active connection.
3. **Case 2 (Single Ethernet + Wi-Fi)**: When `eth0` and `wifi` are detected, `eth0` is prioritized over Wi-Fi.
4. **Case 3 (Primary Degradation)**: When `eth0`, `eth1`, and `wifi` are connected and `eth0` degrades (ALERT/RTO/packet loss), immediately failover to `eth1`.
5. **Case 4 (All Ethernet Alert)**: When both `eth0` and `eth1` degrade (ALERT/RTO), immediately failover to `wifi`.
6. **Live Workload Continuity**: When an active Ethernet (`eth0` or `eth1`) is healthy, the engine enforces stability delay and avoids impulsive switching for small speed variations, protecting ongoing Zoom, vMix, and OBS sessions from socket disruptions.

## Tech Stack

Desktop:

- Python 3
- CustomTkinter
- psutil
- native networking
- PyInstaller

Website:

- React
- TypeScript
- Vite
- Vercel

Build:

- GitHub Actions
- GitHub Releases

## Download / How To Use

Official packages from the [AutoFailover 3.0.1 (v3.0.1)](https://github.com/parikesitad-pm/smart_auto_failover/releases/tag/v3.0.1) release:

### Windows (x64)

1. Download **[AutoFailover-3.0.1-Windows-x64.zip](https://github.com/parikesitad-pm/smart_auto_failover/releases/download/v3.0.1/AutoFailover-3.0.1-Windows-x64.zip)**.
2. Extract the ZIP archive.
3. Run `AutoFailover 3.0.exe`.

### Linux (x86_64)

1. Download **[AutoFailover-3.0.1-Linux-x86_64.tar.gz](https://github.com/parikesitad-pm/smart_auto_failover/releases/download/v3.0.1/AutoFailover-3.0.1-Linux-x86_64.tar.gz)**.
2. Extract: `tar -xzf AutoFailover-3.0.1-Linux-x86_64.tar.gz`
3. Enter directory and run: `./AutoFailover\ 3.0`

### macOS (Apple Silicon arm64)

1. Download **[AutoFailover-3.0.1-macOS-arm64.dmg](https://github.com/parikesitad-pm/smart_auto_failover/releases/download/v3.0.1/AutoFailover-3.0.1-macOS-arm64.dmg)**.
2. Open the DMG and drag or run `AutoFailover 3.0.app`.

## Run From Source

```bash
# Desktop GUI
pip install -r desktop/requirements.txt
python3 -m desktop.main

# Headless CLI / Diagnostics
python3 -m desktop.main --headless
python3 -m desktop.main --acceptance

# Website
cd website && npm install && npm run dev
```

## Changelog

Detailed version history and changes are documented in [CHANGELOG.md](CHANGELOG.md).

### Recent Highlights

- **Modular Speedtest & Bulk Queue**: Dedicated 4-provider benchmarking suite (Cloudflare, FAST.com, Ookla, nPerf) with sequential non-blocking execution, RFC 3550 jitter calculation, and audit history table.
- **Dynamic Release Discovery**: Real-time resolution of latest desktop artifacts from GitHub Releases across all website surfaces without hardcoded version tags.
- **Windows Subprocess Fix**: Eliminated PowerShell/netsh popup windows during adapter polling with Win32 hidden window flags and `psutil` in-process resolution.
- **Cockpit Dashboard Hardening**: Clean interface matrix with immediate stale data clearing on disconnect, plus interactive inspector modals for Network Health Index, Adapter Details, and Speed Benchmarks.
- **Autonomous Policy Engine**: RFC 3550 jitter calculation and multi-factor path scoring with 15-point anti-flap takeover protection.
- **Multi-Platform Distribution**: Automated CI packaging for Windows (x64), Linux (x86_64), and macOS (ARM64).

## Links

- [Website](https://dist-jade-seven-59.vercel.app)
- [Releases](https://github.com/parikesitad-pm/smart_auto_failover/releases)
- [Changelog](CHANGELOG.md)
- [Issues](https://github.com/parikesitad-pm/smart_auto_failover/issues)
- [GitHub](https://github.com/parikesitad-pm/smart_auto_failover)

---

_A Modula Project • Crafted with ♥ by parikesitad-pm • MIT License © 2026_
