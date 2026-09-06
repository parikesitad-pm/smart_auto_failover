# MODULA - Smart Auto Failover v2.1

\*Dibuat oleh: **parikesitad-pm\*** • [GitHub Profile](https://github.com/parikesitad-pm)

Aplikasi Desktop modern, ultra-ringan (**Windows & macOS**) berbasis Python & CustomTkinter dengan identitas visual **Topeng Barong Bali**, dirancang khusus untuk memantau koneksi jaringan aktif secara simultan (**LAN 1 Docking**, **LAN 2 Docking**, **Wi-Fi**, dan **USB Tethering HP**), serta melakukan pengalihan rute default secara otomatis dan instan (**Zero-Drop Failover**) tanpa memutus panggilan Zoom meeting atau UDP stream aktif.

---

## 🐲 Fitur Unggulan di Versi 2.1 (MODULA Overhaul)

1. **Rebranding & Identitas Visual Barong**:
   - Desain terintegrasi dengan logo artistik **Topeng Barong Bali** dan palet warna harmoni: _Royal Gold_ (`#F59E0B`), _Crimson_ (`#DC2626`), dan _Deep Slate_ (`#12141C`).
   - Icon aplikasi `.ico` dan badge resmi di taskbar serta window header.

2. **Startup Preloader & GitHub-Style Skeleton Loader**:
   - Tampilan pembuka beranimasi dengan efek shimmer skeleton cards saat aplikasi memindai adapter dan mengkalibrasi rute metrik awal.

3. **Speedtest Suite 4-Provider (1-Click All Test)**:
   - Pengujian kecepatan 4 engine terkemuka sekaligus dengan 1 klik: **Ookla Speedtest**, **Fast.com (Netflix Open Connect CDN)**, **nPerf / Multi-CDN**, dan **Cloudflare Anycast**.
   - Animasi **Speedometer Circular Gauge ala Ookla** dengan jarum putar sweep dan angka digital real-time.
   - Detail telemetri mendalam ala Cloudflare: _Idle Latency_, _Loaded Latency (Bufferbloat)_, _Jitter (RFC 3550)_, dan _Server Location / ISP_.

4. **Equalizer Spectrum Bars Visualizer**:
   - Pilihan visualisasi live throughput & jitter: Mode Kurva Halus (_Smooth Curve_) atau Mode Bar Spektrum Equalizer (_Aesthetic Audio Spectrum Bars_) dengan warna glow dinamis sesuai beban bandwidth.

5. **Smart Hardware Auto-Detection (Anti-Phantom USB)**:
   - Filter ketat untuk menyingkirkan virtual adapter (Wi-Fi Direct \*Local Area Connection\*\*, Bluetooth Personal Area Network, Loopback, dan vEthernet).
   - Prioritas mutlak port fisik Ethernet (docking / PCIe GbE) pada **Priority 1** dan **Priority 2**, sehingga USB tethering HP tidak akan merebut status koneksi utama jika port docking terpasang.

6. **Dual Mode (Dark & Light)**:
   - Dukungan tema Gelap (_Dark_) dan Terang (_Light_) yang elegan dan responsif.

---

## 🎯 Mengapa Manipulasi Route Metric (Bukan Disable Adapter)?

Pada aplikasi konferensi video real-time seperti **Zoom Meeting**, koneksi audio dan video dikirim melalui protokol transport **UDP** (_connectionless_):

1. **Jika adapter di-disable**: Windows akan langsung menghancurkan seluruh socket TCP/UDP yang terikat ke adapter tersebut. Zoom akan mendeteksi _socket broken_, freeze 5–15 detik, dan menampilkan status _"Reconnecting..."_.
2. **Jika menggunakan Route Metric (`InterfaceMetric`)**: Adapter fisik tetap berstatus **Connected** dan socket UDP tidak dimatikan oleh OS. Ketika nilai metric LAN 1 dinaikkan menjadi `50` dan LAN 2 diubah menjadi `10`, Windows _Routing Table_ seketika mengalirkan paket data berikutnya melalui LAN 2. Server media Zoom mengenali roaming IP dalam 1-2 paket UDP tanpa menghentikan sesi panggilan (Zero-Drop).

---

## 💻 Cara Menjalankan Aplikasi

### Di Windows:

1. Cukup klik ganda file:
   ```
   run_admin.bat
   ```
   _(Script otomatis meminta izin Administrator / UAC)._
2. Atau jalankan file `.exe` mandiri yang sudah jadi di:
   ```
   dist_app\SmartAutoFailover\SmartAutoFailover.exe
   ```

### Di macOS (MacBook / Mac Mini):

1. Buka Terminal di Mac:
   ```bash
   cd /path/to/auto-failover
   chmod +x run_mac.sh
   ./run_mac.sh
   ```
   _(Script otomatis meminta password `sudo` sekali untuk mengatur Network Service Order)._

---

## ⚡ Multi-Interface Speedtest

Klik tombol **"⚡ Speedtest Suite"** di action bar aplikasi:

- **Pilih Engine**: Cloudflare Anycast, nPerf, atau Ookla.
- **Pilih Interface**:
  - Pilih adapter tertentu (misal `Ethernet (10.207.2.115)` atau `Wi-Fi (192.168.1.39)`) untuk tes individual.
  - Atau pilih **"🔍 Bulk Test (Semua Adapter Aktif)"** untuk membandingkan performa seluruh koneksi Anda secara berdampingan.

---

## 🧪 Hasil Quality Assessment (20 Tester Personas)

Seluruh 31 unit test dan 20 simulasi persona pengguna lulus 100% (`Ran 31 tests in 1.086s: OK`):

1. `[PASS] Persona 1`: Budi (Executive on Zoom Call) - Zero-drop UDP failover ke LAN 2 dalam 2 detik.
2. `[PASS] Persona 2`: Siti (Backend Engineer) - Jitter real-time dan packet loss terdeteksi akurat.
3. `[PASS] Persona 3`: Alex (DevOps on Mac M2) - macOS Service Order switching berjalan lancar.
4. `[PASS] Persona 4`: Rian (Competitive Gamer) - Probing interval 1.0s dengan timeout 800ms.
5. `[PASS] Persona 5`: Dimas (Field Tech 4G Tethering) - Deteksi adapter USB tethering HP otomatis.
6. `[PASS] Persona 6`: Dewi (Corporate VPN) - Hirarki metric normal (10/20/30) terjaga.
7. `[PASS] Persona 7`: Fajar (Docking Unplugged) - Failover instan tanpa crash saat kabel dicabut tiba-tiba.
8. `[PASS] Persona 8`: Lina (Outdoor Light Mode) - Pergantian ke Light Mode kontras tinggi.
9. `[PASS] Persona 9`: Hendra (Night Dark Mode) - Mode Gelap obsidian rendah kelelahan mata.
10. `[PASS] Persona 10`: Kevin (Cloudflare Speedtest) - Pengujian download/upload terikat ke source IP.
11. `[PASS] Persona 11`: Anita (nPerf Speedtest) - Multi-CDN Anycast latency test berhasil.
12. `[PASS] Persona 12`: Bambang (Ookla Speedtest) - Integrasi Ookla CLI & fallback Anycast.
13. `[PASS] Persona 13`: Doni (Bulk Multi-WAN) - Skor perbandingan multi-interface berurutan.
14. `[PASS] Persona 14`: Rini (Network Admin) - Perintah connect/disconnect manual port terverifikasi.
15. `[PASS] Persona 15`: Maya (Standard User) - Mode simulasi dry-run aman tanpa hak admin.
16. `[PASS] Persona 16`: Rudi (Windows 11 UAC) - Generator elevasi Administrator teruji.
17. `[PASS] Persona 17`: Tono (Anti-Flapping) - Recovery membutuhkan tepat 5x sukses berturut-turut.
18. `[PASS] Persona 18`: Sarah (Newbie) - Teks modal Bantuan & FAQ interaktif lengkap.
19. `[PASS] Persona 19`: Gilang (Release Auditor) - Riwayat Changelog v1.0 dan v2.0 utuh.
20. `[PASS] Persona 20`: Eko (DevOps Teardown) - Restorasi Automatic Metric otomatis saat aplikasi ditutup.
