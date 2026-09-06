# MODULA - Smart Auto Failover v2.4

<div align="center">

```text
  ███╗   ███╗ ██████╗ ██████╗ ██╗   ██╗██╗      █████╗
  ████╗ ████║██╔═══██╗██╔══██╗██║   ██║██║     ██╔══██╗
  ██╔████╔██║██║   ██║██║  ██║██║   ██║██║     ███████║
  ██║╚██╔╝██║██║   ██║██║  ██║██║   ██║██║     ██╔══██║
  ██║ ╚═╝ ██║╚██████╔╝██████╔╝╚██████╔╝███████╗██║  ██║
  ╚═╝     ╚═╝ ╚═════╝ ╚═════╝  ╚═════╝ ╚══════╝╚═╝  ╚═╝
```

### _Ultra-Lightweight Multi-Platform Zero-Drop Network Failover & QoS Orchestrator_

**Windows • macOS Apple Silicon (M1/M2/M3) • Linux**

\*Dibuat dengan dedikasi oleh: **[parikesitad-pm](https://github.com/parikesitad-pm)\***

[![Release](https://img.shields.io/badge/Release-v2.4-amber?style=for-the-badge&logo=github)](https://github.com/parikesitad-pm)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)](https://python.org)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-emerald?style=for-the-badge)](https://github.com/parikesitad-pm)
[![GUI](https://img.shields.io/badge/GUI-CustomTkinter-indigo?style=for-the-badge)](https://github.com/TomSchimansky/CustomTkinter)
[![Tests](https://img.shields.io/badge/Tests-66%2F66%20PASS-brightgreen?style=for-the-badge)](tests/)
[![License](https://img.shields.io/badge/License-MIT-gray?style=for-the-badge)](LICENSE)

</div>

---

## 💡 Keresahan Nyata & Mengapa MODULA Diciptakan

### Skenario Lapangan:

Pernahkah Anda mengalami situasi krusial seperti ini?

- Sedang memimpin **presentasi Zoom / Microsoft Teams** penting di hadapan klien eksekutif.
- Sedang melakukan **live broadcast streaming event besar menggunakan OBS Studio / vMix**.
- Sedang mengeksekusi **transaksi trading saham/crypto bernilai tinggi**, atau pertandingan esports kompetitif.

Tiba-tiba, koneksi internet kabel fiber optic utama (Indihome / Biznet / FirstMedia) mengalami RTO (_Request Time Out_), putus sesaat, atau kabel docking station tidak sengaja tergeser.

### Masalah Terbesar pada Sistem Operasi Standar:

Ketika satu adapter internet mati:

1. **OS Membutuhkan Waktu Terlalu Lama (15–45 Detik)**: Windows, macOS, maupun Linux tidak langsung mengalihkan rute default secara instan.
2. **Socket TCP/UDP Hancur**: Jika koneksi diputus dengan men-_disable_ adapter, seluruh socket transport yang terikat ke kartu jaringan tersebut langsung dibunuh paksa oleh kernel. Hasilnya: **Zoom Meeting seketika freeze, audio terputus total, dan layar menampilkan pesan "Reconnecting..."** yang merusak jalannya acara penting.
3. **Solusi Hardware Terlalu Mahal**: Router Dual-WAN enterprise (seperti Peplink, Cisco, atau Mikrotik PCC Bonding) membutuhkan biaya jutaan hingga belasan juta rupiah, instalasi kabel rumit, serta pengetahuan jaringan yang mendalam.

### Solusi MODULA (The Software Zero-Drop Failover):

**MODULA** memecahkan masalah ini langsung di level software laptop Anda secara **100% GRATIS dan Tanpa Biaya Hardware Tambahan**:

- **Manipulasi Route Metric Layer-3**: MODULA tidak pernah men-_disable_ port fisik jaringan. Melalui manipulasi _Interface Routing Metric_ dinamis, Windows / macOS / Linux routing table dialihkan ke jalur cadangan (LAN 2 Docking, Wi-Fi, atau USB Tethering HP) dalam waktu **kurang dari 2 detik**.
- **Zero-Drop Protection**: Karena adapter tidak di-disable, socket transport UDP Zoom / Teams tidak dihancurkan oleh OS. Server media video call mengenali roaming IP dalam 1-2 paket UDP tanpa menghentikan sesi meeting sama sekali!

---

## 🎯 Transparansi Sumber Data & Probing Jaringan

Banyak pengguna bertanya: _"Ping-nya dikirim kemana saja? Dari mana asal angka Jitter dan kecepatan Download/Upload yang tampil di layar?"_ MODULA dibangun dengan transparansi teknis penuh:

### 1. Kemana Saja Ping / Probing Dikirim?

MODULA melakukan ICMP Echo Probing aktif secara simultan ke target Anycast BGP Tier-1 global dengan latensi terendah (ditampilkan jelas di status bar header utama):

- **🥇 Target Primer (P1)**: `1.1.1.1` (Cloudflare Global Anycast DNS) — Peering langsung ke gateway data center lokal.
- **🥈 Target Sekunder (P2)**: `8.8.8.8` (Google Public Anycast DNS) — Verifikasi sekunder untuk mencegah _false-positive_.
- **🥉 Target Tersier (P3)**: `9.9.9.9` (Quad9 Anycast) — Resolusi independen Swiss/Global untuk redundansi total.
- **🛰️ Target Keempat (P4 - Opsional)**: Kustom melalui tombol `+ Tambah Target ke-4` (misal OpenDNS `208.67.222.222` atau gateway router lokal `192.168.1.1`).
- **🔒 Source IP Binding**: Ping TIDAK dikirim via rute default semata, melainkan di-bind secara eksplisit ke Source IP lokal masing-masing kartu jaringan (`ping -S <source_ip>` pada Windows, atau bind socket pada macOS/Linux). Hal ini memungkinkan LAN 1, LAN 2, dan Wi-Fi dites jalurnya secara independen dan simultan!

### 2. Dari Mana Angka Jitter Dihitung?

MODULA menerapkan formula standar resmi industri telekomunikasi **IETF RFC 3550 (RTP Audio/Video Streaming Protocol)**:

$$J_i = J_{i-1} + \frac{|D(i-1, i)| - J_{i-1}}{16}$$

Di mana $D(i-1, i) = \text{Latency}_i - \text{Latency}_{i-1}$ adalah deviasi latensi absolut antar 2 paket berturut-turut. Formula ini persis sama dengan yang digunakan oleh Zoom, Cisco Webex, dan Discord VoIP untuk mengkalibrasi kestabilan audio/video buffer Anda:

- 🟢 **Jitter < 5 ms**: Sempurna (Kualitas suara jernih tanpa patah-patah).
- 🟡 **Jitter 5–15 ms**: Cukup baik (Variasi latensi wajar).
- 🔴 **Jitter > 15 ms**: Buruk (Indikasi bufferbloat / audio video mulai _stutter_).

### 3. Dari Mana Angka Download & Upload Berasal?

- **Live Throughput Dashboard**: Dibaca langsung dari _OS Kernel Network Subsystem_ (`psutil.net_io_counters(pernic=True)`) dengan menghitung selisih bytes masuk/keluar dibagi interval waktu nyata ($\Delta t$). Ini mencerminkan pemakaian bandwidth seluruh aplikasi yang sedang berjalan di PC Anda.
- **Speedtest Suite 4-Provider**: Mengalirkan chunk multi-stream paralel langsung ke server node CDN:
  - **Cloudflare Anycast**: `speed.cloudflare.com`
  - **Fast.com**: Netflix Open Connect Appliance (OCA CDN)
  - **nPerf**: Multi-CDN Anycast bandwidth nodes
  - **Ookla**: Jaringan server Ookla Speedtest Network

---

## ⚡ Fitur Unggulan MODULA v2.4

| Fitur                               | Deskripsi                                                                                                                                                                                        |
| :---------------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **🏎️ Sports Car Tachometer HUD**    | Speedometer instrumen tachometer supercar 60 FPS needle sweep analog, redline glow, HUD digital, dan bilah spectrum ganda per backbone target (6 bilah default, 8 bilah saat target ke-4 aktif). |
| **🎛️ Inline Bandwidth QoS Monitor** | Alokasi bandwidth real-time tepat di dashboard utama di bawah speedometer dengan 1-klik tombol cepat **Boost Meeting** (Zoom/Teams/Meet) dan **Boost Streaming** (OBS/vMix).                     |
| **🔌 Adaptif 1 s.d. 8 Port Card**   | Menyesuaikan otomatis dengan perangkat Anda: laptop 1 LAN tampil 1 kartu lebar; 2 LAN + 1 Wi-Fi tampil 3 kolom; PC server hingga 8 port tertata otomatis dalam 2 baris responsif.                |
| **🎯 Custom Target IP ke-4**        | Modal popup instan untuk menambah IP server ke-4 langsung dari dashboard dengan regex validator IPv4 dan preset kilat.                                                                           |
| **⚡ Zero-Delay Splash Startup**    | Eliminasi total kedipan jendela sebelum splash screen; jendela utama disembunyikan sempurna sampai transisi fadeout splash screen selesai.                                                       |
| **🔍 Dialog Riwayat Log Lengkap**   | Panel log dashboard diperamping (~95px) dan dilengkapi tombol **Buka Log Lengkap** untuk membuka dialog pencarian, filter tingkat log, dan ekspor berkas.                                        |
| **👶 Bahasa Formal & Sangat Ramah** | Panduan pengaturan dirancang ulang dalam bahasa Indonesia formal yang mudah dipahami pemula, manula, hingga teknisi jaringan profesional (tersedia Mode Praktis & Mode Lanjutan).                |
| **🚀 Multi-Platform Releases**      | Paket bundle resmi berversi: Windows (`.zip` / `.exe`), macOS Apple Silicon M1/M2/M3 (`.dmg`), dan Linux (`.tar.gz`).                                                                            |
| **⌨️ Shortcut Keyboard Manager**    | Dukungan pintasan keyboard global (F11 Fullscreen, F5 Refresh, Ctrl+M Monitoring, Ctrl+T Speedtest, Ctrl+Q QoS, Ctrl+P Settings) yang dapat dikustomisasi di jendela Settings.                   |
| **🎮 Live GPU Usage & Mini Meters** | Pemantauan utilisasi GPU real-time via daemon thread non-blocking serta visual meter mini mulus (`██░░`) pada footer untuk CPU, RAM, dan GPU.                                                    |
| **🔊 Smart Sound Alert Engine**     | Audio sintetis real-time untuk event port connect, disconnect, failover alarm, dan peringatan beban ekstrem CPU/RAM/GPU (>85%) dengan master mute switch.                                        |
| **💬 Toast Bubble Notifications**   | Banner notifikasi melayang beranimasi di sudut kanan bawah layar untuk setiap aksi, toggle adapter, dan status failover.                                                                         |
| **💻 Fastfetch Hardware Info**      | Kartu spesifikasi hardware PC lengkap ala Fastfetch Linux, grafik rolling 60 detik CPU & RAM, serta pemantauan Top 5 resource-consuming processes.                                               |
| **⚡ 60 FPS Speedtest + Detail**    | Speedometer gauge beranimasi 60 FPS super smooth ala Ookla & Cloudflare. Klik setiap hasil benchmark untuk membuka **Deep Telemetry Modal** (Grade A+ - F, Bufferbloat delta).                   |
| **🌓 Dual Theme (Dark & Light)**    | Tampilan modern berpalet **Topeng Barong Bali** (_Royal Gold, Crimson, Deep Slate_) dengan segment switcher Dark/Light mode instan.                                                              |

---

## 🛠️ Tech Stack & Arsitektur Sistem

```text
┌────────────────────────────────────────────────────────────────────────┐
│                      MODULA DESKTOP GUI (v2.4)                         │
│  [ CustomTkinter 6.0 ] • [ Pillow 12 ] • [ Barong Theming Engine ]     │
│  • Sports Car Tachometer HUD • Inline QoS • Dynamic 1-8 Port Cards     │
│  • Toast Manager • Full History Modal • 4th Target Probing Dialog      │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
┌──────────────────────────────────▼─────────────────────────────────────┐
│                      CORE ORCHESTRATION LAYER                          │
│  • FailoverEngine (Dynamic P1-P8 State Machine & 5x Anti-Flapping)     │
│  • TrafficMonitor (RFC 3550 Jitter & Kernel NetIO Delta Sampling)      │
│  • SoundEngine (Synthesizer Chimes, High-Load Alert & Master Mute)     │
│  • BandwidthQoSEngine (NetQoS DSCP & Windows Process Priority)         │
│  • SystemTelemetry (WMI / CIM Hardware Specs & Top Processes Engine)   │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
┌──────────────────────────────────▼─────────────────────────────────────┐
│                   OS PLATFORM ABSTRACTION LAYER                        │
│   [ WindowsBackend ]       [ MacOSBackend ]        [ LinuxBackend ]    │
│   netsh / route.exe        networksetup            ip route / ip link  │
│   New-NetQosPolicy         scselect                iptables / tc       │
│   WMI Win32 Provider       sysctl hardware         sysfs telemetry     │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 💻 Panduan Menjalankan & Cara Pakai

### 🪟 1. Di Windows (10 / 11)

#### Opsi A: Menggunakan Bundle Release ZIP (Paling Mudah)

1. Unduh atau buka file bundle di:
   ```
   dist_app/MODULA-v2.4-windows-x64.zip
   ```
2. Ekstrak folder `MODULA`, lalu klik kanan file `run_admin.bat` -> pilih **"Run as administrator"** (atau klik ganda `MODULA.exe`).

#### Opsi B: Menjalankan dari Source Code Python

1. Buka PowerShell / Terminal di direktori project:
   ```powershell
   python -m pip install -r requirements.txt
   ```
2. Jalankan dengan hak administrator:
   ```cmd
   run_admin.bat
   ```

---

### 🍏 2. Di macOS (Apple Silicon M1 / M2 / M3 & Intel)

#### Opsi A: Menggunakan Installer Disk Image (.dmg)

1. Build atau buka file disk image:
   ```
   dist_app/MODULA-v2.4-macos-arm64.dmg
   ```
2. Klik ganda file `.dmg`, lalu tarik icon **MODULA** (dengan icon resmi Barong `modula.icns`) ke folder **Applications**.
3. **PENTING - Mengatasi macOS Gatekeeper Quarantine**:
   Karena file didownload dari internet dan belum didaftarkan sertifikat Apple Developer berbayar ($99/thn), macOS Gatekeeper akan menampilkan pesan _"MODULA is damaged and can't be opened"_ atau memblokir aplikasi.
   Solusi sangat mudah (cukup jalankan 1 kali di Terminal Mac):
   ```bash
   xattr -cr /Applications/MODULA.app
   ```
   Atau di dalam file DMG sudah disediakan script pembuka cepat: klik ganda **`Open_MODULA.command`**.

#### Opsi B: Menjalankan dari Terminal Mac

1. Buka Terminal:
   ```bash
   chmod +x run_mac.sh
   ./run_mac.sh
   ```
   _(Script otomatis meminta password `sudo` sekali untuk mengizinkan manipulasi urutan Network Service Order)._

---

### 🐧 3. Di Linux (Ubuntu / Debian / Fedora / Arch)

1. Pasang dependensi GUI Tkinter sistem:
   ```bash
   sudo apt-get update && sudo apt-get install python3 python3-pip python3-tk
   python3 -m pip install -r requirements.txt
   ```
2. Jalankan launcher dengan privilege jaringan:
   ```bash
   chmod +x build_linux.sh
   ./dist_app/MODULA/run_linux.sh
   ```

---

## 📦 Panduan Build & Packaging untuk Tim

Jika Anda ingin membuild ulang paket rilis mandiri (_standalone distribution_) untuk tim Anda:

```bash
# 1. Build Bundle Windows (Menghasilkan MODULA-v2.4-windows-x64.zip & MODULA.exe)
python build_windows_bundle.py

# 2. Build Bundle macOS (Menghasilkan MODULA-v2.4-macos-arm64.dmg di Mac)
chmod +x build_macos_dmg.sh
./build_macos_dmg.sh

# 3. Build Bundle Linux (Menghasilkan MODULA-v2.4-linux-x86_64.tar.gz di Linux)
chmod +x build_linux.sh
./build_linux.sh
```

---

## 🔮 Roadmap Pengembangan: "Ini Bisa Jadi Apa Aja & Kemana Aja?"

Bagi para pengembang, insinyur jaringan, dan kontributor open-source, arsitektur modular **MODULA** dirancang sangat fleksibel untuk dikembangkan lebih jauh ke berbagai ranah:

### 1. 🚀 True Multi-WAN Channel Bonding (Packet Aggregation)

- **Visi**: Menggabungkan bandwidth 2 kabel LAN dan Wi-Fi secara serentak (misal: LAN 1 50Mbps + LAN 2 50Mbps = 100Mbps).
- **Implementasi**: Mengintegrasikan protokol MPTCP (_Multi-Path TCP_) atau proxy WireGuard VPN multi-tunnel seperti Speedify, namun 100% open-source dan self-hosted tanpa langganan bulanan.

### 2. 🧠 AI-Driven Predictive Network Failover

- **Visi**: Melakukan failover _sebelum_ koneksi internet benar-benar putus.
- **Implementasi**: Model Machine Learning / Neural Network ultra-ringan (menggunakan ONNX Runtime) yang mempelajari pola variansi Jitter, lonjakan Bufferbloat, dan RTT slope untuk memprediksi degradasi jaringan 1–2 detik lebih awal sebelum terjadinya drop paket.

### 3. 🐳 Headless Docker Daemon & Router Box (Raspberry Pi / Mini PC)

- **Visi**: Menjadikan MODULA sebagai sistem operasi router fisik mungil.
- **Implementasi**: Memisahkan core engine menjadi CLI daemon / REST API tanpa GUI yang dapat di-flash ke Raspberry Pi 4 / 5 atau mini PC dengan 3–4 port Ethernet untuk dijadikan gateway failover kantor atau studio broadcast.

### 4. 📱 Mobile Companion App (Android & iOS)

- **Visi**: Memantau status failover laptop dan mengontrol alokasi bandwidth dari smartphone saat sedang live broadcast.
- **Implementasi**: Local WebSocket server ringan di MODULA yang terhubung ke aplikasi mobile Flutter / React Native di jaringan Wi-Fi lokal yang sama.

### 5. 🏢 Enterprise Fleet Monitoring Dashboard

- **Visi**: Monitoring stabilitas koneksi ratusan laptop karyawan WFH dalam satu layar monitoring NOC perusahaan.
- **Implementasi**: Ekspor metrik telemetri ke Prometheus & visualisasi real-time di Grafana Dashboard.

---

## 🧪 Quality Assessment (QA) & Test Suite

MODULA dilengkapi rangkaian pengujian otomatis (_Automated Testing Suite_) yang mencakup **66 unit test** dan simulasi skenario **20 persona tester**:

```bash
python -m unittest discover tests
```

### Hasil Eksekusi:

```text
Ran 66 tests in 8.008s

OK (All 66 unit tests & 20-persona QA simulation passed 100%)
```

- `[PASS] TestV24Features`: Verifikasi Sports Car Tachometer HUD, Inline QoS Widget, Dynamic 1-8 Adapter Cards, dan target IP ke-4.
- `[PASS] TestV23Features`: Verifikasi Custom Ping Probing, Settings Modal, Keyboard Shortcuts, Telemetri GPU, QoS Presets, dan filter vMixService.
- `[PASS] TestSoundEngine`: Verifikasi synthesizer audio, nada connect/disconnect, failover, high-load (>85%), dan master mute.
- `[PASS] TestBandwidthQoS`: Pemindaian proses aktif Zoom/OBS/vMix, auto-balance slider 100%, dan registrasi NetQoS.
- `[PASS] TestSystemTelemetry`: Deteksi akurat spesifikasi hardware PC, rolling history CPU/RAM/GPU 60s, dan pemantauan top active processes.
- `[PASS] TestUIComponents`: Verifikasi TrafficChartWidget 60 FPS, Toast Bubble, modal SpeedtestDetail, Skeleton preloader, dan Interface Cards.
- `[PASS] TestQA20Personas`: 20 skenario nyata pengguna (Zoom call zero-drop, docking unplugged, jitter RFC 3550, UAC elevation, anti-flapping 5x recovery).

---

## 📄 Lisensi & Kontribusi

Proyek ini dirilis di bawah lisensi **MIT License**. Terbuka penuh untuk digunakan oleh individu, streamer, perusahaan, maupun institusi penyiaran.

\*Dibuat dengan bangga oleh **[parikesitad-pm](https://github.com/parikesitad-pm)**. Jika project ini bermanfaat untuk kelancaran meeting, streaming, atau pekerjaan Anda, berikan bintang ⭐ di GitHub!
