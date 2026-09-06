# MODULA - Smart Auto Failover v2.2

\*Dibuat oleh: **parikesitad-pm\*** • [GitHub Profile](https://github.com/parikesitad-pm)

Aplikasi Desktop modern, ultra-ringan (**Windows, macOS Apple Silicon M1/M2/M3 & Linux**) berbasis Python & CustomTkinter dengan identitas visual **Topeng Barong Bali**. Dirancang khusus untuk memantau koneksi jaringan aktif secara simultan (**LAN 1 Docking**, **LAN 2 Docking**, **Wi-Fi**, dan **USB Tethering HP**), serta melakukan pengalihan rute default secara otomatis dan instan (**Zero-Drop Failover**) tanpa memutus panggilan Zoom meeting, OBS live streaming, vMix broadcast, atau UDP stream aktif.

---

## ⚡ Fitur Unggulan di Versi 2.2

1. **Multi-Platform Release Bundles (Versioned Packages)**:
   - Skrip build otomatis untuk tiga platform utama:
     - 🪟 **Windows x64**: `MODULA-v2.2-windows-x64.zip` & `MODULA.exe` standalone.
     - 🍏 **macOS Apple Silicon (M1/M2/M3)**: `MODULA-v2.2-macos-arm64.dmg` dengan drag-and-drop ke Applications.
     - 🐧 **Linux x86_64**: `MODULA-v2.2-linux-x86_64.tar.gz`.

2. **Audio Alert Engine & Master Mute Toggle**:
   - Notifikasi suara sintetis real-time saat port Wi-Fi / Ethernet terhubung (_Connect chime_) atau terputus (_Disconnect chime_).
   - Emergency audio siren saat rute primary mengalami RTO/failover.
   - Tombol toggle suara (🔊 ON / 🔇 MUTE) langsung di header aplikasi.

3. **Toast Bubble Notification Manager**:
   - Floating toast banner modern dan non-intrusif yang muncul otomatis untuk setiap interaksi pengguna dan event jaringan.

4. **Application Bandwidth QoS Allocator**:
   - Modul kontrol alokasi bandwidth pintar antar aplikasi aktif (**Zoom, OBS Studio, vMix, Spotify, Discord, Google Chrome**).
   - Slider persentase 0–100% interaktif dengan fitur auto-balancing 100% dan preset profil instan (_Zoom VIP 75%_, _Broadcast Streamer 70%_, _Balanced QoS_).
   - Integrasi Windows NetQoS DSCP policies & process scheduling priority.

5. **Fastfetch PC Hardware Diagnostics & CCleaner Junk Cleaner**:
   - Mini CPU/RAM monitor di footer ala macOS dengan angka akurat real-time.
   - Modal Fastfetch PC Diagnostics menampilkan detail spesifikasi perangkat:
     - Model Laptop & Motherboard (contoh: ASUS TUF Dash F15 FX516PE)
     - CPU Core & Threads (Intel Core i7-11370H)
     - Dual GPU (Intel Iris Xe Integrated & NVIDIA GeForce RTX 3050 Ti Laptop GPU)
     - Live RAM & Penyimpanan Disk (NTFS drives)
   - **1-Click Cleaner ala CCleaner**: Pembersih instan untuk menghapus file build usang, cache pyinstaller, dan temporary files.

6. **Iconic Spectrum Bars Visualizer (3 Mode & Heartbeat Loop)**:
   - Tiga mode visualisasi dinamis yang ikonik:
     - `⚡ Cyber Spectrum Bars` (Equalizer audio multi-band glow)
     - `📡 RF Internet Wave` (Gelombang radio frekuensi interaktif)
     - `🌊 Smooth Curve` (Kurva halus throughput)
   - Ambient heartbeat animation loop 30 FPS sehingga grafik tetap berdenyut dinamis meskipun traffic internet sedang idle.

7. **Fullscreen Mode (F11)**:
   - Tombol toggle Fullscreen ala browser di header, dengan shortcut keyboard `<F11>` dan `<Escape>`.

8. **Speedtest Suite 4-Provider (1-Click All Test)**:
   - 1-Click Test ke seluruh 4 engine: **Ookla Speedtest**, **Fast.com (Netflix Open Connect)**, **nPerf**, dan **Cloudflare Anycast**.
   - Animasi Speedometer Circular Gauge dengan jarum sweep ala Ookla dan detail telemetri mendalam ala Cloudflare (Idle Latency, Bufferbloat, Jitter, Packet Loss).

---

## 🎯 Mengapa Manipulasi Route Metric (Bukan Disable Adapter)?

Pada aplikasi konferensi video real-time seperti **Zoom Meeting**, koneksi audio dan video dikirim melalui protokol transport **UDP** (_connectionless_):

1. **Jika adapter di-disable**: Windows akan langsung menghancurkan seluruh socket TCP/UDP yang terikat ke adapter tersebut. Zoom akan mendeteksi _socket broken_, freeze 5–15 detik, dan menampilkan status _"Reconnecting..."_.
2. **Jika menggunakan Route Metric (`InterfaceMetric`)**: Adapter fisik tetap berstatus **Connected** dan socket UDP tidak dimatikan oleh OS. Ketika nilai metric LAN 1 dinaikkan menjadi `50` dan LAN 2 diubah menjadi `10`, Windows _Routing Table_ seketika mengalirkan paket data berikutnya melalui LAN 2. Server media Zoom mengenali roaming IP dalam 1-2 paket UDP tanpa menghentikan sesi panggilan (Zero-Drop).

---

## 📦 Panduan Build & Packaging Multi-Platform

### 🪟 1. Windows (x64)

Untuk membuild standalone `.exe` dan paket release `.zip`:

```powershell
# Jalankan script packaging Windows
python build_windows_bundle.py
```

Output yang dihasilkan:

- `dist_app/MODULA-v2.2-windows-x64.zip` (Paket siap distribusi untuk tim)
- `dist_app/MODULA/MODULA.exe` (Executable standalone dengan icon & manifest Administrator)

Cara menjalankan langsung dari source code:

```cmd
run_admin.bat
```

---

### 🍏 2. macOS Apple Silicon (M1 / M2 / M3)

Untuk membuild bundle `.app` dan disk image `.dmg` di Mac:

```bash
# Pastikan script executable
chmod +x build_macos_dmg.sh

# Jalankan script build
./build_macos_dmg.sh
```

Output yang dihasilkan:

- `dist_app/MODULA-v2.2-macos-arm64.dmg` (Disk image DMG dengan drag-and-drop installer ke Applications)
- `dist_app/MODULA.app`

Cara menjalankan di macOS dari Terminal:

```bash
chmod +x run_mac.sh
./run_mac.sh
```

_(Script otomatis meminta password `sudo` sekali untuk mengatur Network Service Order)._

---

### 🐧 3. Linux (x86_64)

Untuk membuild standalone bundle di distribusi Linux (Ubuntu, Debian, Fedora, Arch):

```bash
# Pastikan dependencies sistem terpasang
sudo apt-get install python3 python3-pip python3-tk

# Jalankan script build
chmod +x build_linux.sh
./build_linux.sh
```

Output yang dihasilkan:

- `dist_app/MODULA-v2.2-linux-x86_64.tar.gz`
- `dist_app/MODULA/MODULA` (Executable Linux dengan helper `run_linux.sh`)

---

## ⚡ Multi-Interface Speedtest

Klik tombol **"⚡ Speedtest"** di action bar aplikasi:

- **Pilih Engine**: Cloudflare Anycast, Fast.com, nPerf, atau Ookla.
- **Pilih Interface**:
  - Pilih adapter tertentu (misal `Ethernet (10.207.2.115)` atau `Wi-Fi (192.168.1.39)`) untuk tes individual.
  - Atau pilih **"🔍 Bulk Test (Semua Adapter Aktif)"** untuk membandingkan performa seluruh koneksi Anda secara berdampingan.

---

## 🧪 Quality Assessment & Testing Suite

Jalankan rangkaian test otomatis:

```bash
python -m unittest discover tests
```

Semua modul v2.2 teruji:

- `SoundEngine`: Synthesizer chimes cross-platform & mute logic.
- `BandwidthQoS`: Process scanner, slider auto-balance 100%, and NetQoS rules.
- `SystemTelemetry`: Fastfetch hardware detection & CCleaner disk scanner.
- `ToastNotificationManager`: Event bubble notifications.
- `FailoverEngine`: Routing metrics preservation and zero-drop recovery.
