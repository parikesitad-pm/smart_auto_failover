# Smart Auto-Failover Network Monitor v1.0
*Dibuat oleh: **parikesitad-pm***

Aplikasi Desktop modern dan ringan (Windows & macOS) berbasis Python & CustomTkinter yang dirancang khusus untuk memantau koneksi jaringan aktif secara simultan (**LAN 1**, **LAN 2**, **Wi-Fi**, dan **USB Tethering HP**), serta melakukan pengalihan rute default secara otomatis dan instan (**Zero-Drop Failover**) tanpa memutus panggilan Zoom meeting aktif.

---

## 🎯 Mengapa Manipulasi Route Metric (Bukan Disable Adapter)?

Pada aplikasi konferensi video real-time seperti **Zoom Meeting**, koneksi audio dan video dikirim melalui protokol transport **UDP** (*connectionless*):

1. **Jika adapter di-disable**: Windows akan langsung menghancurkan seluruh socket TCP/UDP yang terikat ke adapter tersebut. Zoom akan mendeteksi *socket broken*, freeze 5–15 detik, dan menampilkan status *"Reconnecting..."*.
2. **Jika menggunakan Route Metric (`InterfaceMetric`)**: Adapter fisik tetap berstatus **Connected** dan socket UDP tidak dimatikan oleh OS. Ketika nilai metric LAN 1 dinaikkan menjadi `50` dan LAN 2 diubah menjadi `10`, Windows *Routing Table* seketika mengalirkan paket data berikutnya melalui LAN 2. Server media Zoom mengenali roaming IP dalam 1-2 paket UDP tanpa menghentikan sesi panggilan (Zero-Drop).

---

## 🚀 Fitur Utama

- **Real-Time Health-Check Berbasis Source-IP (`ping -S`)**:
  - ICMP probe tidak melewati default route Windows, melainkan di-bind secara spesifik ke source IP masing-masing adapter (`ping -n 1 -w 800 -S <Source_IP> 1.1.1.1`).
  - Frekuensi probing tiap 1 detik dengan timeout pendek (800ms) untuk deteksi RTO yang cepat.
- **Logika 3-Tier Failover & Auto-Recovery**:
  - **Normal**: LAN 1 = `Metric 10` (Active Primary), LAN 2 = `Metric 20` (Standby), Wi-Fi = `Metric 30` (Standby).
  - **Failover P1**: Jika LAN 1 mengalami 2x RTO berturut-turut $\rightarrow$ LAN 2 menjadi `Metric 10`, LAN 1 diturunkan ke `Metric 50`.
  - **Failover P2**: Jika LAN 1 & LAN 2 sama-sama RTO $\rightarrow$ Wi-Fi dipromosikan ke `Metric 10`.
  - **Auto-Recovery**: Ketika LAN 1 pulih dan sukses ping 5x berturut-turut $\rightarrow$ LAN 1 kembali menjadi `Metric 10` secara mulus.
- **UI Dashboard Modern (CustomTkinter Dark Mode)**:
  - 3 Kartu Status Interface (IP, Gateway, Metric aktif, status koneksi, bar & sparkline grafik latency real-time).
  - Panel log aktivitas dengan penanda warna untuk event failover dan recovery.
  - Deteksi hak akses Windows Administrator (UAC) & tombol satu klik "Elevate to Admin".
- **Safety & Auto-Restore**:
  - Saat aplikasi ditutup (exit) atau tombol "Reset Auto-Metrics" ditekan, seluruh interface secara otomatis dikembalikan ke setelan Windows **Automatic Metric** (`Set-NetIPInterface -AutomaticMetric Enabled`).

---

## 📋 Persyaratan Sistem

- Windows 10 atau Windows 11 (64-bit)
- Python 3.10+ (Sudah terpasang di sistem)
- Hak akses Administrator (diperlukan untuk mengubah route metric Windows)

---

## 🛠️ Instalasi Dependensi

Jalankan perintah berikut di PowerShell atau Command Prompt:

```powershell
cd d:\lucca\project\auto-failover
python -m pip install -r requirements.txt
```

Dependensi:
- `customtkinter>=6.0.0` (GUI modern)
- `psutil>=5.9.0` (Informasi antarmuka jaringan)

---

## 💻 Cara Menjalankan Aplikasi

### Opsi 1: Menjalankan via Batch Launcher (Rekomendasi)
Cukup **klik ganda (double-click)** pada file:
```
run_admin.bat
```
Script ini akan secara otomatis memicu dialog Windows UAC (*Run as Administrator*) dan menjalankan aplikasi dalam mode Admin penuh.

### Opsi 2: Menjalankan via Terminal / PowerShell (Admin)
Buka PowerShell sebagai Administrator (*Run as Administrator*), lalu ketik:
```powershell
cd d:\lucca\project\auto-failover
python main.py
```

*Catatan: Jika dijalankan tanpa hak Admin, aplikasi akan otomatis berjalan dalam **Simulation / Dry-Run Mode** dan menampilkan tombol "Elevate to Admin" di pojok kanan atas.*

---

## 🍏 Cara Menjalankan di macOS (MacBook / Mac Mini)

Aplikasi ini sudah **100% Cross-Platform**. Seluruh folder ini bisa Anda copy ke Mac:

1. Buka Terminal di Mac, masuk ke direktori folder ini:
   ```bash
   cd /path/to/auto-failover
   ```
2. Berikan izin eksekusi pada script launcher Mac:
   ```bash
   chmod +x run_mac.sh
   ```
3. Jalankan launcher:
   ```bash
   ./run_mac.sh
   ```
   *(Script akan meminta password `sudo` sekali untuk mengizinkan pengaturan Network Service Order macOS).*

---


## 📦 Cara Compile ke Executable Mandiri (.exe)

Aplikasi ini dilengkapi dengan script `build_exe.py` yang memanfaatkan PyInstaller dengan konfigurasi `--uac-admin` (sehingga file `.exe` yang dihasilkan memiliki icon perisai Windows UAC dan langsung meminta hak administrator saat diklik ganda):

```powershell
python build_exe.py
```

Setelah selesai, file `.exe` mandiri siap pakai akan berada di:
```
d:\lucca\project\auto-failover\dist\SmartAutoFailover\SmartAutoFailover.exe
```

---

## 📖 Panduan Penggunaan GUI

1. **Pemilihan Interface**:
   - Klik tombol **"🔍 Auto-Detect Interfaces"** untuk mendeteksi adapter yang terpasang secara otomatis, atau pilih adapter yang sesuai lewat menu dropdown di masing-masing kartu:
     - **Priority 1 (Primary)**: Pilih adapter docking Ethernet 1 (misal `Ethernet`).
     - **Priority 2 (Backup)**: Pilih adapter docking Ethernet 2 (misal `Ethernet 2`).
     - **Priority 3 (Fallback)**: Pilih adapter `Wi-Fi`.
2. **Mulai Monitoring**:
   - Klik tombol **"▶ Start Monitoring"**.
   - Aplikasi akan menerapkan metric baseline (P1: 10, P2: 20, P3: 30) dan mulai mengirim probe ICMP setiap 1 detik.
   - Banner status di atas akan menunjukkan route aktif saat ini.
3. **Pengaturan Threshold & Metric**:
   - Klik tombol **"⚙️ Settings"** untuk mengatur alamat DNS target ping (default `1.1.1.1`), timeout (default 800ms), batas RTO (default 2), dan batas recovery (default 5).
4. **Berhenti & Restorasi**:
   - Klik tombol **"■ Stop Monitoring"** atau tutup jendela aplikasi.
   - Seluruh metric interface akan dikembalikan ke setelan awal sistem (Automatic Metric).

---

## 🧪 Cara Pengujian / Verifikasi Failover

1. Buka sesi panggilan Zoom (atau lakukan streaming audio/video).
2. Jalankan aplikasi dan klik **"Start Monitoring"**.
3. Pastikan LAN 1 berstatus **ACTIVE DEFAULT ROUTE (Metric 10)**.
4. **Simulasi RTO**: Cabut kabel LAN 1 atau matikan port LAN 1 dari router/docking.
5. Perhatikan log:
   - Detik ke-1: LAN 1 RTO pertama (warning).
   - Detik ke-2: LAN 1 RTO kedua $\rightarrow$ **FAILOVER EXECUTED**!
   - LAN 2 seketika menjadi Metric 10 dan LAN 1 diturunkan ke Metric 50.
   - Panggilan Zoom tetap berjalan tanpa terputus (*Zero-Drop*).
6. **Simulasi Recovery**: Colok kembali kabel LAN 1.
   - Setelah 5 kali ping sukses berturut-turut, LAN 1 kembali menjadi Metric 10.

