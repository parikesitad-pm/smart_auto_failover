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

**Digital Network Cockpit • Multi-Path Failover & Active Session Protector**  
**Windows • macOS Apple Silicon • Linux**

*Dibuat oleh: **[parikesitad-pm](https://github.com/parikesitad-pm)\***

[![Release](https://img.shields.io/badge/Release-v3.0.0--alpha-blue?style=for-the-badge&logo=github)](https://github.com/parikesitad-pm)
[![Core](https://img.shields.io/badge/Core-Rust-orange?style=for-the-badge&logo=rust)](https://www.rust-lang.org/)
[![Shell](https://img.shields.io/badge/Shell-Tauri-24C8D8?style=for-the-badge&logo=tauri)](https://tauri.app/)
[![UI](https://img.shields.io/badge/UI-React%20%2B%20TS-61DAFB?style=for-the-badge&logo=react)](https://react.dev/)
[![License](https://img.shields.io/badge/License-MIT-gray?style=for-the-badge)](LICENSE)

</div>

---

## 🎯 Filosofi & Prinsip Desain

> **Core UX Principle:**  
> *"Kelihatan kompleks di dalam. Terasa sederhana di luar."*  
> *"Automation should be invisible until it matters."*

AutoFailover 3.0 dirancang sebagai sebuah **Digital Network Cockpit** yang terinspirasi dari visual instrumen kluster otomotif berpresisi tinggi—bukan panel administrasi router yang padat dan membingungkan.

### 6 Pertanyaan Kunci Layar Utama (< 2 Detik):
1. **Jalur internet mana yang sedang dipakai?** (`ONLINE`)
2. **Apakah koneksi dalam kondisi sehat?** (Status bar & health badge)
3. **Berapa Latensi & Jitter saat ini?** (Readout standar IETF RFC 3550)
4. **Bagaimana kondisi kecepatan Download / Upload?** (Dual precision gauges)
5. **Jalur cadangan mana yang siap jika jalur aktif putus?** (`READY` / `ALERT` / `OFFLINE`)
6. **Apakah MODULA baru saja melakukan pengalihan rute?** (Notifikasi transisi instan)

*Fitur sekunder (analisis beban hardware CPU/RAM/GPU, konfigurasi lanjutan, log diagnostik mendalam) ditempatkan rapi di secondary views agar dashboard utama tetap tenang dan fokus.*

---

## 🛡️ Session Continuity & Perlindungan Workload Aktif

Tujuan utama diciptakannya MODULA adalah melindungi sesi kerja real-time yang sedang berlangsung (**Zoom, Microsoft Teams, Google Meet, OBS Studio, vMix, Wirecast, Streamlabs**) dari dampak degradasi jaringan dan putusnya koneksi.

$$\text{DETECT EARLY} \longrightarrow \text{SELECT BETTER PATH} \longrightarrow \text{SWITCH FAST} \longrightarrow \text{MINIMIZE SESSION DISRUPTION}$$

### Disiplin Teknis: Batasan Kontinuitas Koneksi
- MODULA **TIDAK PERNAH mengklaim "garansi pasti zero socket drop untuk seluruh aplikasi"**. Pengalihan rute OS dapat mengubah IP sumber/antarmuka lokal, sehingga sebagian sesi TCP/UDP lama pada protokol tertentu mungkin memerlukan re-establishment.
- **Tujuan Rekayasa Resmi**: *"Meminimalkan disrupsi dan memaksimalkan probabilitas kontinuitas sesi aktif"*, didukung pengujian empiris terukur per platform dan workload.
- Pengalaman pengguna yang dihadirkan:  
  **"MODULA menyelesaikan masalah jaringan saya."**  
  *(Bukan: "MODULA mengubah-ubah konfigurasi jaringan saya tanpa alasan.")*

### Aturan Tanpa Perpindahan Rute yang Tak Perlu (*No Unnecessary Switching*)
Kontinuitas sesi kerja memiliki prioritas jauh lebih tinggi daripada mengejar perbedaan performa minor:
- **DILARANG berpindah jalur** hanya karena selisih latensi beberapa milidetik, derau pengukuran sesaat, lonjakan jitter tunggal yang insignifikan, atau karena jalur prioritas fisik baru pulih.
- Rumus anti-flapping margin ($\text{candidate\_score} \ge \text{active\_score} + \text{takeover\_margin}$) wajib dipenuhi sebelum promosi terjadi.

### Prioritas Penanganan Gangguan (Failure Priority):
1. Pertahankan jalur aktif yang masih sehat.
2. Deteksi degradasi lebih awal sebelum terjadi pemutusan total.
3. Hindari perpindahan jalur yang tidak perlu (*avoid flapping*).
4. Jika jalur aktif benar-benar rusak/unusable, alihkan rute seketika (<2s).
5. Pilih kandidat terbaik yang memenuhi syarat.
6. Lanjutkan pemantauan pasif terhadap jalur yang sebelumnya bermasalah.
7. Evaluasi pemulihan jalur (*recovery*) tanpa preemption agresif.

---

## 🏎️ Visual & AutoFailover 3.0 Vertical Accent

- **Dark Cockpit Aesthetic**: Latar gelap high-contrast (`#080b10`) dengan tipografi presisi teknis.
- **Custom SVG Gauges**: Jarum instrumen analog responsif dengan interpolasi 60 FPS client-side tanpa membebani engine jaringan.
- **AutoFailover 3.0 Vertical Accent**: Garis aksen vertikal tipis (*light blue → blue → red*) pada tepi bezel sebagai ciri khas visual dekoratif AutoFailover 3.0 by Modula (bukan indikator status).
- **Dynamic Interface Cards**: Hanya menampilkan kartu jaringan fisik/logis yang benar-benar aktif terdeteksi (Ethernet 1, Ethernet 2, Wi-Fi, USB Modem) tanpa placeholder palsu.

---

## 🏛️ UI / Core Ownership & Authority Model

> **Prinsip Dasar:**  
> *The UI reports what MODULA decided.*  
> *The Policy Engine decides what should happen.*  
> *The Failover Engine makes it happen.*  
> *The Platform Backend talks to the operating system.*

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

### Pemisahan Tanggung Jawab:
- **UI (React + TypeScript)**: Bertanggung jawab merender status dashboard, interaksi pengguna, permintaan konfigurasi policy, konfirmasi administratif, dan menampilkan event engine. **UI TIDAK PERNAH memiliki wewenang jaringan** (tidak melakukan probing, scoring, atau switching rute sendiri).
- **Rust Core**: Memiliki otoritas penuh atas pemantauan jaringan, evaluasi kesehatan, keputusan rute, manipulasi routing metric, dan penegakan QoS.
- **Process Independence**: Siklus hidup engine jaringan independen dari UI. Engine tetap berjalan optimal saat UI diminimalkan, disembunyikan, atau tertutup.

---

## 🛡️ Administrative Actions vs Policy Decisions

Aksi administratif berbeda secara mendasar dari keputusan policy rute:

1. **Passive Carrier Probing**: Adapter fisik yang di-disable secara administratif tetap dipantau status carrier & latensinya melalui background socket probe (`SO_BINDTODEVICE` / `IP_UNICAST_IF`).
2. **Smart Prompt ("Please Enable")**: Jika adapter yang di-disable terbukti memiliki kualitas prima, UI memunculkan notifikasi persetujuan:
   > *"Ethernet 1 is disabled but appears healthy. Enable it for automatic failover?"*  
   > `[ Enable ]` `[ Keep Disabled ]`
3. **Aturan Otoritas**:
   - Jika pengguna memilih **Enable**: UI mengirim perintah atomik `enable_interface(id)` ke Rust Core. Platform backend mengaktifkan adapter → memvalidasi operational state → Policy Engine mengevaluasi skor → Failover Engine memutuskan apakah promosi layak. **"Enable" BUKAN berarti langsung "Force ONLINE"**.
   - Jika pengguna memilih **Keep Disabled**: Adapter tetap dinonaktifkan dan dikeluarkan dari kandidat failover. **MODULA tidak akan pernah mengaktifkan adapter secara diam-diam (*never silently re-enable*) tanpa izin eksplisit pengguna.**

---

## ⚡ Workload Awareness Profiles

Workload Engine memberikan konteks spesifik ke Policy Engine tanpa memotong alur kendali:
- **General**: Penyeimbangan metrik umum (latensi & bandwidth seimbang).
- **Video Conference**: Memprioritaskan latensi rendah, variasi jitter (RFC 3550) serendah mungkin, toleransi kehilangan paket minimal, dan kestabilan buffer audio/video.
- **Live Production**: Memprioritaskan throughput unggah (*upload stability*), packet loss 0%, dan kestabilan bit-rate video upstream (OBS/vMix).

---

## 📜 Riwayat Milestone Ringkas

Detail riwayat lengkap setiap rilis tersedia di **[CHANGELOG.md](CHANGELOG.md)**.

| Versi | Milestone Utama |
| :--- | :--- |
| **v3.0** | Arsitektur Rust + Tauri + React & TS, pemisahan UI/Core ownership mutlak, Digital Network Cockpit minimalis, Session Continuity & Active Session Protection, anti-flap margin, dynamic interface discovery, dan administrative approval protocol. |
| **v2.6** | Dual tachometer Download/Upload, Center HUD readout RFC 3550 Jitter, circular backbone dial, dan throughput fallback. |
| **v2.5** | Gauge speedtest SportsCarSpeedGauge 250°, staged tactile refresh delay, dan canvas idle sleep optimization. |
| **v2.4** | Inline QoS monitor, layout adaptif 1-8 port, dialog custom probing target ke-4, dan log dialog viewer. |
| **v2.3** | Splash screen frameless radial, keyboard shortcuts, dan sound synthesis alerts. |
| **v2.2** | Paket rilis multi-platform Windows / macOS Apple Silicon / Linux, dan 4-engine speedtest benchmark. |
| **v2.0 - v2.1** | Rebranding MODULA, multi-port failover hingga 3 adapter, implementasi formula Jitter RFC 3550. |
| **v1.0** | Pondasi manipulasi Layer-3 Routing Metric untuk proteksi failover transport. |

---

## 📄 Lisensi & Hak Cipta

Proyek ini dirilis di bawah lisensi **MIT License**.

Copyright (c) 2026 **[parikesitad-pm](https://github.com/parikesitad-pm)**.
