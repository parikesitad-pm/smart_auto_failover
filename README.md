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
_Windows • macOS (Apple Silicon & Intel) • Linux_

\*Dibuat oleh: **[parikesitad-pm](https://github.com/parikesitad-pm)\***

[![Vercel Deployment](https://img.shields.io/badge/Vercel-Live%20Demo-000000?style=for-the-badge&logo=vercel&logoColor=white)](https://dist-jade-seven-59.vercel.app)
[![Release](https://img.shields.io/badge/Release-v3.0.0--alpha-blue?style=for-the-badge&logo=github)](https://github.com/parikesitad-pm)
[![Core](https://img.shields.io/badge/Core-Rust-orange?style=for-the-badge&logo=rust)](https://www.rust-lang.org/)
[![Shell](https://img.shields.io/badge/Shell-Tauri-24C8D8?style=for-the-badge&logo=tauri)](https://tauri.app/)
[![UI](https://img.shields.io/badge/UI-React%20%2B%20TS-61DAFB?style=for-the-badge&logo=react)](https://react.dev/)
[![License](https://img.shields.io/badge/License-MIT-gray?style=for-the-badge)](LICENSE)

</div>

---

## 🧭 Ikhtisar & Posisi Produk

AutoFailover 3.0 dirancang untuk melindungi aktivitas kerja berorientasi real-time seperti panggilan video conference (**Zoom, Microsoft Teams, Google Meet**) dan live broadcast (**OBS Studio, vMix, Wirecast, Streamlabs**) dari gangguan latensi tinggi, lonjakan jitter, maupun putusnya jalur fisik internet secara tiba-tiba.

Sistem memantau kondisi seluruh antarmuka jaringan fisik (Ethernet, Wi-Fi, USB Cellular Modem), mengevaluasi kualitas koneksi menggunakan metrik objektif (IETF RFC 3550 Jitter & Latensi), dan secara otomatis mengalihkan rute default level sistem operasi tanpa memerlukan intervensi manual yang rumit.

---

## 🏎️ Panduan Penggunaan: Instrument Cluster AutoFailover 3.0

**Instrument Cluster AutoFailover 3.0** (sebelumnya dikenal sebagai _Cockpit Widget_) adalah antarmuka visual terpadu beresolusi tinggi yang terinspirasi dari kluster instrumen mobil performa tinggi (_automotive digital instrument cluster_). Kluster ini dirancang agar pengguna dapat memahami kondisi seluruh pipa jaringan dalam waktu **kurang dari 2 detik**.

```text
┌───────────────────────────────────────────────────────────────────────────┐
│ [⚡] Instrument Cluster AutoFailover 3.0 by Modula           [● ONLINE]   │
│      Navigate Your Internet Pipeline to Keep You Online                   │
│      CPU: [██░░░░] 14%  •  RAM: [████░░] 38%  •  GPU: N/A                 │
├─────────────────────────────────────┬─────────────────────────────────────┤
│   DOWNLOAD GAUGE     UPLOAD GAUGE   │ ACTIVE ROUTE PATH: Ethernet 1       │
│      187.6 Mbps        48.2 Mbps    │ Carrier: Connected • Gateway Valid  │
│      [60 FPS Arc]     [60 FPS Arc]  │ Latency: 8.2ms • RFC 3550: 1.2ms    │
├─────────────────────────────────────┴─────────────────────────────────────┤
│ Standby NICs: Wi-Fi (wlp0s20f3 · READY)                                   │
│ Pipeline Sim: [Nominal] [Jitter Spike] [Cable Unplug] [Cable Reconnect]   │
└───────────────────────────────────────────────────────────────────────────┘
```

### 4 Cara Menjalankan & Mengakses Instrument Cluster

1. **Akses Online Live Demo (Vercel)**:
   Akses instan melalui browser tanpa setup apa pun:
   - **Production Cockpit Web**: [https://dist-jade-seven-59.vercel.app](https://dist-jade-seven-59.vercel.app)
   - **Standalone Instrument Cluster**: [https://dist-jade-seven-59.vercel.app/instrument_cluster_autofailover_3_0.html](https://dist-jade-seven-59.vercel.app/instrument_cluster_autofailover_3_0.html)
2. **Akses Langsung via Browser (Dev Server Lokal)**:
   Saat aplikasi pengembangan dijalankan (`npm --prefix frontend run dev`), buka URL berikut di browser:
   ```text
   http://localhost:3000/instrument_cluster_autofailover_3_0.html
   ```
3. **Akses File HTML Mandiri (Zero Dependencies)**:
   Buka file berikut langsung dengan klik dua kali di browser (Google Chrome, Firefox, Safari, Edge) tanpa perlu menyalakan server atau menginstal Node.js:
   ```text
   frontend/public/instrument_cluster_autofailover_3_0.html
   ```
4. **Melalui Aplikasi Native Desktop (Tauri Shell)**:
   Jalankan binary desktop hasil kompilasi:
   ```bash
   ./target/debug/autofailover-app
   # atau versi rilis
   ./target/release/autofailover-app
   ```

### Anatomi & Elemen Pembacaan Kluster

- **Dual Tachometers (Download & Upload)**: Mengukur kecepatan unduh dan unggah seketika dengan animasi jarum 60 FPS client-side tanpa membebani thread engine jaringan.
- **Active Route Path Card**: Menampilkan adapter fisik yang sedang membawa trafik produksi, gateway aktif, latensi milidetik, jitter RFC 3550, dan nilai composite health score (0–100).
- **Device Health Bar**: Indikator beban hardware pasif (CPU, RAM, GPU) dengan frekuensi rendah (~1 Hz) yang **terisolasi mutlak** dari keputusan failover jaringan.
- **Standby Candidate Pool**: Memperlihatkan antarmuka cadangan yang siap siaga (`READY`), mengalami degradasi (`ALERT`), atau putus kabel (`OFFLINE`).
- **Tombol Simulasi Pipeline Real-Time**:
  - `[ Nominal ]`: Mengembalikan kondisi jaringan ke status Ethernet 1 normal dan prima (98.4 score).
  - `[ Jitter Spike ]`: Mensimulasikan lonjakan variasi transmisi paket dan membuktikan proteksi policy anti-flapping.
  - `[ Cable Unplug (OFFLINE) ]`: Mensimulasikan pelepasan kabel fisik LAN (`carrier == 0` / `operstate == down`), langsung mengalihkan rute default ke Wi-Fi (`ONLINE`), dan menandai kartu Ethernet dengan badge merah tegas `OFFLINE`.
  - `[ Cable Reconnect (READY) ]`: Mensimulasikan pemasangan kembali kabel LAN. Antarmuka masuk ke cooldown stabilisasi `RecoveryArbiter` dan berstatus `READY` (tidak membajak jalur aktif tanpa pertimbangan policy).

---

## 🚀 Panduan Penggunaan Lintas Sistem Operasi (Windows, macOS, Linux)

AutoFailover 3.0 dibangun di atas arsitektur **Rust Core** (berotoritas penuh atas manipulasi jaringan) dan **Tauri Desktop Shell** (UI ultra-ringan berbasis WebKit/WebView2).

### Kebutuhan Dasar (Prerequisites):

- **Rust Toolchain**: `rustc` dan `cargo` versi 1.77 atau lebih baru (`curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`).
- **Node.js**: Node.js versi 18+ LTS dan `npm` (atau `pnpm`).

---

### 🐧 Panduan Linux (Ubuntu, Debian, Arch, Manjaro, Fedora)

Pada Linux, backend berinteraksi langsung dengan `/sys/class/net`, `/proc/net/route`, dan utilitas `iproute2` (`ip route`, `ip link`).

#### 1. Instalasi Dependensi Sistem:

- **Debian / Ubuntu**:
  ```bash
  sudo apt-get update
  sudo apt-get install -y libwebkit2gtk-4.1-dev build-essential curl wget file \
      libxdo-dev libssl-dev libayatana-appindicator3-dev librsvg2-dev iproute2
  ```
- **Arch Linux / Manjaro**:
  ```bash
  sudo pacman -S --needed base-devel webkit2gtk-4.1 openssl iproute2
  ```
- **Fedora**:
  ```bash
  sudo dnf install webkit2gtk4.1-devel openssl-devel iproute
  ```

#### 2. Kompilasi & Menjalankan:

```bash
# Clone repositori
git clone https://github.com/parikesitad-pm/smart_auto_failover.git
cd smart_auto_failover

# Instal dependensi frontend
npm --prefix frontend install

# Jalankan dalam mode pengembangan (Desktop Shell + Vite Live Preview)
npm --prefix frontend run dev &
cargo run --bin autofailover-app
```

#### 3. Izin Manipulasi Rute Default (Root / Capabilities):

Mengubah default gateway di tabel routing Linux memerlukan hak akses jaringan:

```bash
# Opsi A (Rekomendasi - Berikan Capability tanpa root penuh):
sudo setcap cap_net_admin,cap_net_raw+ep ./target/debug/autofailover-app

# Opsi B (Jalankan via sudo):
sudo ./target/debug/autofailover-app
```

---

### 🪟 Panduan Windows (Windows 10 & 11 x64 / ARM64)

Pada Windows, backend menggunakan native Windows Network APIs (`IPHLPAPI.lib`, `SetIpForwardEntry2`, `GetIpForwardTable2`) dan socket option `IP_UNICAST_IF`.

#### 1. Kebutuhan Sistem:

- **Visual Studio Build Tools**: Paket _Desktop development with C++_ (MSVC).
- **WebView2 Runtime**: Bawaan Windows 10/11 (Evergreen Bootstrapper).

#### 2. Kompilasi & Menjalankan:

Buka terminal **PowerShell (Run as Administrator)**:

```powershell
# Clone repositori
git clone https://github.com/parikesitad-pm/smart_auto_failover.git
cd smart_auto_failover

# Instal dependensi frontend
npm --prefix frontend install

# Build binary native release
cargo build --release --bin autofailover-app

# Jalankan binary
.\target\release\autofailover-app.exe
```

> **Catatan Izin Administrator**: Penyesuaian metrik Layer-3 pada tabel routing Windows membutuhkan hak administrator. Jalankan terminal PowerShell sebagai Administrator sebelum meluncurkan aplikasi.

---

### 🍎 Panduan macOS (Apple Silicon M1/M2/M3/M4 & Intel x64)

Pada macOS, backend memanfaatkan kerangka kerja bawaan `SystemConfiguration.framework` dan perintah manipulasi kernel routing BSD (`route replace default`).

#### 1. Kebutuhan Sistem:

- **Xcode Command Line Tools**:
  ```bash
  xcode-select --install
  ```

#### 2. Kompilasi & Menjalankan:

```bash
# Clone repositori
git clone https://github.com/parikesitad-pm/smart_auto_failover.git
cd smart_auto_failover

# Instal dependensi frontend
npm --prefix frontend install

# Build binary native
cargo build --release --bin autofailover-app

# Menjalankan aplikasi
sudo ./target/release/autofailover-app
```

> **Catatan Izin macOS**: Mengubah rute gateway default pada stack BSD kernel macOS memerlukan `sudo` atau hak administrasi sistem.

---

## 🎯 Filosofi & Prinsip Desain

> **Core UX Principle:**
> _"Kelihatan kompleks di dalam. Terasa sederhana di luar."_
> _"Automation should be invisible until it matters."_

### 6 Pertanyaan Kunci Layar Utama (< 2 Detik):

1. **Jalur internet mana yang sedang dipakai?** (`ONLINE`)
2. **Apakah koneksi dalam kondisi sehat?** (Status bar & health badge)
3. **Berapa Latensi & Jitter saat ini?** (Readout standar IETF RFC 3550)
4. **Bagaimana kondisi kecepatan Download / Upload?** (Dual precision gauges)
5. **Jalur cadangan mana yang siap jika jalur aktif putus?** (`READY` / `ALERT` / `OFFLINE`)
6. **Apakah MODULA baru saja melakukan pengalihan rute?** (Notifikasi transisi instan)

---

## 🛡️ Session Continuity & Perlindungan Workload Aktif

Tujuan utama diciptakannya MODULA adalah melindungi sesi kerja real-time yang sedang berlangsung (**Zoom, Microsoft Teams, Google Meet, OBS Studio, vMix, Wirecast, Streamlabs**) dari dampak degradasi jaringan dan putusnya koneksi.

$$\text{DETECT EARLY} \longrightarrow \text{SELECT BETTER PATH} \longrightarrow \text{SWITCH FAST} \longrightarrow \text{MINIMIZE SESSION DISRUPTION}$$

### Disiplin Teknis: Batasan Kontinuitas Koneksi

- MODULA **TIDAK PERNAH mengklaim "garansi pasti zero socket drop untuk seluruh aplikasi"**. Pengalihan rute OS dapat mengubah IP sumber/antarmuka lokal, sehingga sebagian sesi TCP/UDP lama pada protokol tertentu mungkin memerlukan re-establishment.
- **Tujuan Rekayasa Resmi**: _"Meminimalkan disrupsi dan memaksimalkan probabilitas kontinuitas sesi aktif"_, didukung pengujian empiris terukur per platform dan workload.
- Pengalaman pengguna yang dihadirkan:
  **"MODULA menyelesaikan masalah jaringan saya."**
  _(Bukan: "MODULA mengubah-ubah konfigurasi jaringan saya tanpa alasan.")_

### Aturan Tanpa Perpindahan Rute yang Tak Perlu (_No Unnecessary Switching_)

Kontinuitas sesi kerja memiliki prioritas jauh lebih tinggi daripada mengejar perbedaan performa minor:

- **DILARANG berpindah jalur** hanya karena selisih latensi beberapa milidetik, derau pengukuran sesaat, lonjakan jitter tunggal yang insignifikan, atau karena jalur prioritas fisik baru pulih.
- Rumus anti-flapping margin ($\text{candidate\_score} \ge \text{active\_score} + \text{takeover\_margin}$) wajib dipenuhi sebelum promosi terjadi.

### Prioritas Penanganan Gangguan (Failure Priority):

1. Pertahankan jalur aktif yang masih sehat.
2. Deteksi degradasi lebih awal sebelum terjadi pemutusan total.
3. Hindari perpindahan jalur yang tidak perlu (_avoid flapping_).
4. Jika jalur aktif benar-benar rusak/unusable, alihkan rute seketika (<2s).
5. Pilih kandidat terbaik yang memenuhi syarat.
6. Lanjutkan pemantauan pasif terhadap jalur yang sebelumnya bermasalah.
7. Evaluasi pemulihan jalur (_recovery_) tanpa preemption agresif (`READY` terlebih dahulu).

---

## 🏛️ UI / Core Ownership & Authority Model

> **Prinsip Otoritas:**
> _The UI reports what MODULA decided._
> _The Policy Engine decides what should happen._
> _The Failover Engine makes it happen._
> _The Platform Backend talks to the operating system._

```text
React / TypeScript UI
        ↓ (Perintah Atomik: enable_interface, get_interface_state)
     Tauri IPC
        ↓ (State Streams & Events)
      Rust Core
        ↓
┌───────────────────────────────┐
│ DiscoveryEngine               │
│ ProbeEngine (RFC 3550 Jitter) │
│ Health Scoring                │
│ PolicyEngine (Route Decision) │
│ FailoverEngine (Orchestrator) │
│ RouteManager (L3 Metric)      │
│ Recovery & Anti-Flap Arbiter  │
│ WorkloadEngine (Passive App)  │
│ QoS Orchestrator              │
└───────────────┬───────────────┘
                ↓
        Native OS APIs
```

---

## 📄 Lisensi & Hak Cipta

Proyek ini dirilis di bawah lisensi **MIT License**.

Copyright (c) 2026 **[parikesitad-pm](https://github.com/parikesitad-pm)**.
