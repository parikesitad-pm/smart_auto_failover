# MODULA - Smart Auto Failover v2.2

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

[![Release](https://img.shields.io/badge/Release-v2.2-amber?style=for-the-badge&logo=github)](https://github.com/parikesitad-pm)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)](https://python.org)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-emerald?style=for-the-badge)](https://github.com/parikesitad-pm)
[![GUI](https://img.shields.io/badge/GUI-CustomTkinter-indigo?style=for-the-badge)](https://github.com/TomSchimansky/CustomTkinter)
[![Tests](https://img.shields.io/badge/Tests-49%2F49%20PASS-brightgreen?style=for-the-badge)](tests/)
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

MODULA melakukan ICMP Echo Probing aktif secara simultan ke target Anycast BGP Tier-1 global dengan latensi terendah:

- **🥇 Target Primer**: `1.1.1.1` (Cloudflare Global Anycast DNS) — Peering langsung ke gateway data center lokal.
- **🥈 Target Sekunder**: `8.8.8.8` (Google Public Anycast DNS) — Verifikasi sekunder untuk mencegah _false-positive_.
- **🥉 Target Tersier**: `9.9.9.9` (Quad9 Anycast) & Default Gateway lokal.
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

## ⚡ Fitur Unggulan MODULA v2.2

| Fitur                             | Deskripsi                                                                                                                                                                       |
| :-------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **🚀 Multi-Platform Releases**    | Paket bundle resmi berversi: Windows (`.zip` / `.exe`), macOS Apple Silicon M1/M2/M3 (`.dmg`), dan Linux (`.tar.gz`).                                                           |
| **🔊 Audio Alert Engine**         | Notifikasi suara sintetis real-time untuk event port terhubung (_Connect_), kabel putus (_Disconnect_), failover darurat (_Failover Alarm_), dan master toggle mute di header.  |
| **💬 Toast Bubble Notifications** | Banner notifikasi melayang beranimasi di sudut kanan bawah layar untuk setiap aksi dan event jaringan.                                                                          |
| **🎛️ Bandwidth QoS Allocator**    | Modul alokasi persentase bandwidth ke aplikasi aktif (**Zoom, OBS Studio, vMix, Spotify, Discord, Chrome**) dengan slider auto-balancing 100% dan Windows NetQoS DSCP policies. |
| **💻 Fastfetch PC Diagnostics**   | Kartu spesifikasi hardware lengkap ala Fastfetch Linux (Model Laptop, CPU, Dual GPU Iris Xe & RTX 3050 Ti, RAM, Storage NTFS).                                                  |
| **🧹 CCleaner Junk Cleaner**      | Fitur 1-klik untuk membersihkan build usang, cache PyInstaller, dan file sampah proyek, menghemat ruang disk.                                                                   |
| **📊 Smooth 40 FPS Visualizer**   | Tiga mode grafik ikonik: `⚡ Cyber Spectrum Bars` (32-band equalizer), `📡 RF Internet Wave`, dan `🌊 Smooth Curve` dengan ambient heartbeat 40 FPS anti-patah.                 |
| **⛶ Browser Fullscreen (F11)**    | Tombol toggle layar penuh borderless di header dengan shortcut keyboard `<F11>` dan `<Escape>`.                                                                                 |
| **⚡ 4-Engine Speedtest Suite**   | 1-Click benchmark ke 4 provider terkemuka sekaligus (Ookla, Fast.com Netflix, nPerf, Cloudflare) dengan speedometer gauge beranimasi sweep.                                     |
| **🌓 Dual Theme (Dark & Light)**  | Tampilan modern berpalet **Topeng Barong Bali** (_Royal Gold, Crimson, Deep Slate_) dengan segment switcher Dark/Light mode instan.                                             |

---

## 🛠️ Tech Stack & Arsitektur Sistem

```text
┌────────────────────────────────────────────────────────────────────────┐
│                      MODULA DESKTOP GUI (v2.2)                         │
│  [ CustomTkinter 6.0 ] • [ Pillow 12 ] • [ Barong Theming Engine ]     │
│  • 40 FPS Canvas Visualizer • Toast Manager • Telemetry Hub • QoS GUI  │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
┌──────────────────────────────────▼─────────────────────────────────────┐
│                      CORE ORCHESTRATION LAYER                          │
│  • FailoverEngine (State Machine & 5x Anti-Flapping Recovery)          │
│  • TrafficMonitor (RFC 3550 Jitter & Kernel NetIO Delta Sampling)      │
│  • SoundEngine (Synthesizer Chimes & Master Mute)                      │
│  • BandwidthQoSEngine (NetQoS DSCP & Windows Process Priority)         │
│  • SystemTelemetry (WMI / CIM Hardware Specs & CCleaner Scanner)       │
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
   dist_app/MODULA-v2.2-windows-x64.zip
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
   dist_app/MODULA-v2.2-macos-arm64.dmg
   ```
2. Klik ganda file `.dmg`, lalu tarik icon **MODULA** ke folder **Applications**.

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
# 1. Build Bundle Windows (Menghasilkan MODULA-v2.2-windows-x64.zip & MODULA.exe)
python build_windows_bundle.py

# 2. Build Bundle macOS (Menghasilkan MODULA-v2.2-macos-arm64.dmg di Mac)
chmod +x build_macos_dmg.sh
./build_macos_dmg.sh

# 3. Build Bundle Linux (Menghasilkan MODULA-v2.2-linux-x86_64.tar.gz di Linux)
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

MODULA dilengkapi rangkaian pengujian otomatis (_Automated Testing Suite_) yang mencakup **49 unit test** dan simulasi skenario **20 persona tester**:

```bash
python -m unittest discover tests
```

### Hasil Eksekusi:

```text
Ran 49 tests in 9.768s

OK (All 49 unit tests & 20-persona QA simulation passed 100%)
```

- `[PASS] TestSoundEngine`: Verifikasi synthesizer audio, nada connect/disconnect, dan master mute.
- `[PASS] TestBandwidthQoS`: Pemindaian proses aktif Zoom/OBS/vMix, auto-balance slider 100%, dan registrasi NetQoS.
- `[PASS] TestSystemTelemetry`: Deteksi akurat spesifikasi hardware laptop dan scanner pembersih CCleaner.
- `[PASS] TestUIComponents`: Verifikasi rendering TrafficChartWidget 40 FPS, Toast Bubble, modal popup, dan card interface.
- `[PASS] TestQA20Personas`: 20 skenario nyata pengguna (Zoom call zero-drop, docking unplugged, jitter RFC 3550, UAC elevation, anti-flapping 5x recovery).

---

## 📄 Lisensi & Kontribusi

Proyek ini dirilis di bawah lisensi **MIT License**. Terbuka penuh untuk digunakan oleh individu, streamer, perusahaan, maupun institusi penyiaran.

\*Dibuat dengan bangga oleh **[parikesitad-pm](https://github.com/parikesitad-pm)\***. Jika project ini bermanfaat untuk kelancaran meeting, streaming, atau pekerjaan Anda, berikan bintang ⭐ di GitHub!
