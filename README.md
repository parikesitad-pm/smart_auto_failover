# AutoFailover 3.0 by Modula

<div align="center">

```text
  ███╗   ███╗ ██████╗ ██████╗ ██╗   ██╗██╗      █████╗
  ████╗ ████║██╔═══██╗██╔══██╗██║   ██║██║     ██╔══██╗
  ██╔████╔██║██║   ██║██║  ██║██║   ██║██║     ███████║
  ██║╚██╔╝██║██║   ██║██║  ██║██║   ██║██║     ██╔══██║
  ██║ ╚═╝ ██║╚██████╔╝██████╔╝╚██████╔╝███████╗██║  ██║
  ╚═╝     ╚═╝ ╚═════╝ ╚═════╝  ╚═════╝ ╚══════╝╚═╝  ╚═╝
```

### _"light seamless and usefull"_

**Navigate Your Internet Pipeline to Keep You Online**
**Through Video Conference & Livestreaming Production**
_Windows • macOS (Apple Silicon) • Linux_

\*Dibuat oleh: **[parikesitad-pm](https://github.com/parikesitad-pm)\***

[![Vercel Deployment](https://img.shields.io/badge/Vercel-Live%20Website-000000?style=for-the-badge&logo=vercel&logoColor=white)](https://dist-jade-seven-59.vercel.app)
[![GitHub Release](https://img.shields.io/badge/Release-v3.0.0--preview-emerald?style=for-the-badge&logo=github)](https://github.com/parikesitad-pm/smart_auto_failover/releases)
[![Desktop Engine](https://img.shields.io/badge/Desktop-Python%203%20%2B%20CustomTkinter-3776AB?style=for-the-badge&logo=python&logoColor=white)](desktop/)
[![Website Hub](https://img.shields.io/badge/Website-React%20%2B%20TS%20%2B%20Vite-61DAFB?style=for-the-badge&logo=react)](website/)
[![License](https://img.shields.io/badge/License-MIT%202026-gray?style=for-the-badge)](LICENSE)

</div>

---

## 🏗️ Arsitektur Dua Permukaan (Dual-Surface Architecture)

AutoFailover 3.0 terdiri dari **DUA permukaan aplikasi mandiri** yang terisolasi secara ketat:

| Permukaan                            | Direktori  | Stack Teknologi                                       | Tanggung Jawab Utama                                                                                                                                                                                                 |
| ------------------------------------ | ---------- | ----------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **A. Desktop Application**           | `desktop/` | **Python 3**, **CustomTkinter**, Native OS Networking | **Produk Nyata**: Engine pengalihan rute Layer-3, monitoring socket RFC 3550 Jitter, scoring 5-state, anti-flap takeover margin, headless CLI ticker, dan Cockpit GUI desktop native.                                |
| **B. Public Website & Cockpit Demo** | `website/` | **React**, **TypeScript**, **Vite**, **TailwindCSS**  | **Portal Publik & Simulator**: Landing page resmi dengan logo Modula 3.0 hidup, Download Hub dengan deteksi rilis GitHub dinamis, dan simulator Cockpit interaktif dengan kontrol skenario deterministik di browser. |

---

## 🖥️ Permukaan A: Aplikasi Desktop Native (`desktop/`)

Aplikasi desktop merupakan produk inti yang berjalan di workstation untuk mengamankan koneksi jaringan.

### 1. Struktur Komponen Desktop

```text
desktop/
  ├── autofailover.spec        # PyInstaller multi-platform packaging specification
  ├── main.py                  # Entrypoint: CLI orchestrator, headless mode & GUI launcher
  ├── requirements.txt         # Minimal production dependencies (customtkinter, pillow)
  ├── VERSION                  # Single source of truth untuk versi rilis desktop
  ├── core/                    # Pure domain logic, network-engine-agnostic
  │     ├── models.py          # State types: NetworkInterface, TelemetryState, DeviceHealth
  │     ├── probe.py           # RFC 3550 Jitter & Latency measurement engine
  │     ├── health.py          # Exponential Weighted Moving Average (EWMA) scoring
  │     ├── policy.py          # Anti-flap candidate selection (takeover_margin)
  │     ├── failover.py        # Failover orchestrator & transition event emitter
  │     └── recovery.py        # Link recovery stabilization arbiter
  ├── platform/                # Native OS Network Abstraction Layer (HAL)
  │     ├── base.py            # Platform backend contract interface
  │     ├── linux.py           # Linux sysfs (/sys/class/net), /proc/net/route, iproute2
  │     ├── windows.py         # Windows netsh & route table management
  │     └── macos.py           # macOS scutil & networksetup integration
  ├── ui/                      # CustomTkinter Desktop Cockpit GUI
  │     ├── app.py             # Desktop root window & layout manager
  │     ├── splash.py          # 9-stage splash initialization gate
  │     ├── cockpit.py         # Automotive instrument cluster view
  │     └── widgets.py         # Needle tachometers, status badges & metric strips
  └── tests/                   # Python characterization & unit test suite
        ├── test_probe.py      # RFC 3550 jitter calculation verification
        ├── test_health.py     # Health scoring formula validation
        ├── test_policy.py     # Takeover margin & preemption resistance tests
        └── test_recovery.py   # Anti-flap stabilization tests
```

### 2. Menjalankan Aplikasi Desktop

#### A. Mode Headless Engine & Terminal Monitor

Dapat dijalankan langsung di server, terminal, atau workstation tanpa display server:

```bash
# Monitor background continuous (ticker 1 Hz)
python3 -m desktop.main --headless

# Menjalankan 10 siklus evaluasi lalu keluar
python3 -m desktop.main --headless --ticks 10

# Validasi antarmuka fisik dan model 5-state
python3 -m desktop.main --acceptance
```

#### B. Menjalankan Desktop Cockpit GUI (CustomTkinter)

```bash
# Instal dependensi desktop
pip install -r desktop/requirements.txt

# Luncurkan GUI desktop
python3 -m desktop.main
```

#### C. Menjalankan Rangkaian Pengujian Unit Test

```bash
python3 -m unittest discover -s desktop/tests
```

### 3. Pembuatan Paket Distribusi Mandiri (PyInstaller)

Setiap platform dikompilasi secara independen menggunakan GitHub Actions native runners:

```bash
# Linux / macOS / Windows
pyinstaller --noconfirm desktop/autofailover.spec
```

---

## 🌐 Permukaan B: Public Website & Cockpit Demo (`website/`)

Portal publik yang dideploy ke Vercel untuk mendistribusikan installer rilis dan menyediakan simulator Cockpit interaktif bagi pengguna browser.

### 1. Struktur Komponen Website

```text
website/
  ├── src/
  │    ├── components/
  │    │     ├── Landing/          # HeroSection, DownloadHub, FeaturePillars, FaqAccordion
  │    │     ├── Cockpit/          # Digital Cockpit, PerformanceGauges, InterfaceDeck
  │    │     │     ├── DemoToolbar.tsx    # 7-Action deterministic scenario controller
  │    │     │     ├── CockpitHeader/     # Title, status pill, and workload profile
  │    │     │     ├── InterfaceDeck/     # Physical interface matrix cards
  │    │     │     └── PerformanceGauges/ # 60 FPS client-side lerped SVG tachometers
  │    │     └── Splash/           # Modula 3.0 enterprise splash gate
  │    ├── hooks/
  │    │     ├── useNetworkCockpit.ts  # Deterministic browser demo engine
  │    │     └── useStartupSequence.ts # Realistic 9-stage initialization sequence
  │    ├── services/
  │    │     └── githubReleases.ts     # Dynamic GitHub release discovery & platform resolver
  │    └── types/
  │          ├── cockpit.types.ts      # Domain models
  │          └── releases.ts           # GitHub release & asset types
  ├── package.json
  ├── tailwind.config.js
  └── vite.config.ts
```

### 2. Menjalankan Pengembangan Website

```bash
# Instal dependensi website
npm --prefix website install

# Jalankan server pengembangan Vite
npm --prefix website run dev

# Validasi TypeScript
npm --prefix website run type-check

# Kompilasi bundel produksi untuk Vercel
npm --prefix website run build
```

---

## 🎮 Simulator Cockpit Interaktif (Live Browser Demo)

Cockpit pada website menyediakan simulator skenario deterministik lengkap dengan **7 Kontrol Skenario Real-Time**:

1. **Disconnect Ethernet**: Mensimulasikan terputusnya kabel LAN primer. Jalur Ethernet 1 seketika berstatus `OFFLINE`, memicu failover sub-detik yang mempromosikan Wi-Fi 6 ke `ONLINE`.
2. **Reconnect Ethernet**: Mengembalikan kabel LAN fisik. Mesin memvalidasi stabilitas tautan melalui arbiter pemulihan anti-flap sebelum mengembalikannya sebagai jalur aktif utama.
3. **Disable Wi-Fi**: Mensimulasikan penonaktifan adaptor nirkabel secara administratif (`DISABLED`).
4. **Enable Wi-Fi**: Mengaktifkan kembali adaptor nirkabel ke status siaga (`READY`).
5. **Degrade Connection**: Mensimulasikan lonjakan jitter RFC 3550 (18.2ms) dan peningkatan latensi pada tautan utama. Policy Engine mendeteksi penurunan kualitas lebih awal dan mengalihkan rute ke Wi-Fi sebelum koneksi terputus total.
6. **Recover Connection**: Mengembalikan metrik latensi dan jitter ke kondisi prima (8.2ms latensi, 1.1ms jitter).
7. **Reset Demo**: Mengembalikan topologi ke kondisi awal nominal dual-homed.

---

## 🚦 Status Verifikasi Platform Rilis

Sesuai dengan prinsip kejujuran teknis, rilis pratinjau diberi label transparan:

| Platform    | Arsitektur            | Format Paket                    | Status Verifikasi                               |
| ----------- | --------------------- | ------------------------------- | ----------------------------------------------- |
| **Linux**   | x86_64                | `.tar.gz`                       | `IMPLEMENTATION / REAL-HOST VALIDATION PENDING` |
| **Windows** | x64                   | `.zip` (`AutoFailover 3.0.exe`) | `IMPLEMENTATION / REAL-HOST VALIDATION PENDING` |
| **macOS**   | Apple Silicon (ARM64) | `.dmg`                          | `IMPLEMENTATION / REAL-HOST VALIDATION PENDING` |

> Setiap build pratinjau dilengkapi dengan file ringkasan checksum SHA-256 (`SHA256SUMS.txt`) untuk memverifikasi integritas unduhan.

---

## 🛡️ Prinsip & Kebijakan Failover

1. **Prioritas Kontinuitas Sesi**: Menjaga jalur aktif yang stabil lebih penting daripada mengejar perbedaan performa kecil.
2. **Margin Anti-Flapping**:
   $$\text{candidate\_score} \ge \text{active\_score} + \text{takeover\_margin}$$
   Pengalihan rute hanya dieksekusi jika kandidat pengganti memiliki skor yang secara signifikan melampaui jalur aktif ditambah margin toleransi.
3. **Deteksi Degradasi Awal (Early Degradation)**:
   Menggunakan pengukuran variasi kedatangan paket (IETF RFC 3550 Interarrival Jitter) untuk mengantisipasi kegagalan jalur sebelum sesi video conference atau streaming macet.
4. **Pemisahan Metrik Hardware**:
   Beban perangkat keras (CPU, RAM, GPU) dipantau secara terisolasi dan **tidak pernah** memengaruhi skor pemilihan rute jaringan.

---

## 📄 Lisensi & Hak Cipta

Proyek ini dirilis di bawah lisensi **MIT License**.

Copyright (c) 2026 **[parikesitad-pm](https://github.com/parikesitad-pm)**.
