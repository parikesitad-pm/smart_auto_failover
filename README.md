# AutoFailover 3.0
> by Modula • *light seamless and usefull*

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

## Links

- [Website](https://dist-jade-seven-59.vercel.app)
- [Releases](https://github.com/parikesitad-pm/smart_auto_failover/releases)
- [Issues](https://github.com/parikesitad-pm/smart_auto_failover/issues)
- [GitHub](https://github.com/parikesitad-pm/smart_auto_failover)

---
*A Modula Project • Crafted with ♥ by parikesitad-pm • MIT License © 2026*
