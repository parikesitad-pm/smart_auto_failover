# AutoFailover 3.0

> by Modula • _light seamless and usefull_

AutoFailover 3.0 protects active real-time workloads (Zoom, OBS Studio, Microsoft Teams, Google Meet, vMix) by autonomously detecting network path degradation and switching seamlessly to healthy backup paths.

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

### Windows

1. Download `AutoFailover-3.0.0-Windows-x64.zip` from Releases.
2. Extract the ZIP archive.
3. Run `AutoFailover 3.0.exe`.

### Linux

1. Download `AutoFailover-3.0.0-Linux-x86_64.tar.gz` from Releases.
2. Extract: `tar -xzf AutoFailover-3.0.0-Linux-x86_64.tar.gz`
3. Enter directory and run: `./AutoFailover\ 3.0`

### macOS

1. Download `AutoFailover-3.0.0-macOS-arm64.dmg` from Releases.
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
