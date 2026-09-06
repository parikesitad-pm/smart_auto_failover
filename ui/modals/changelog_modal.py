"""
MODULA - Smart Auto Failover
Interactive Version History & Changelog Explorer (v2.3)
"""

from typing import Dict, List
import customtkinter as ctk

from core.sound_engine import SoundEngine, SoundType


CHANGELOG_DATA: Dict[str, dict] = {
    "v2.6": {
        "title": "🏎️ VERSI 2.6 (Pure Sports Car Cockpit Gauges, 100% Circular Backbone Dials & Live I/O Fallback)",
        "date": "September 2026",
        "badge": "LATEST STABLE v2.6",
        "badge_color": ("#D1FAE5", "#064E3B"),
        "badge_text_color": "#059669",
        "items": [
            ("🏎️ Kluster Instrumen Kokpit Supercar Ganda (RPM Download & MPH Upload)", "Menggantikan speedometer lama dengan tachometer analog ganda bergaya kokpit supercar 240° arc. Dial kiri (RPM) memantau kecepatan unduh (download) real-time dengan redline zone glow, dial kanan (MPH) memantau kecepatan unggah (upload) real-time, lengkap dengan dynamic auto-scaling satuan (Kbps / Mbps / Gbps) dan jarum 60 FPS."),
            ("🎯 Center HUD Readout (Jitter RFC 3550 & Rute Aktif)", "Layar HUD digital di bagian tengah kluster menampilkan metrik jitter real-time (rumus IETF RFC 3550), status stabilitas koneksi ('STABLE' / 'FLUCTUATING'), serta badge gear rute jaringan aktif (misal: '🏎️ P1 LAN')."),
            ("🌐 100% Dial-Based ICMP Backbone Indicators (Bilah Dihapus Penuh)", "Bilah vertikal spektrum dihapus sepenuhnya sesuai permintaan desain. Digantikan instrumen dial sirkular murni untuk masing-masing server backbone aktif (3 dial sirkular default untuk 1.1.1.1, 8.8.8.8, 9.9.9.9, dan otomatis bertambah menjadi 4 dial sirkular saat target ke-4 diaktifkan)."),
            ("➕ Modal Form Tunggal Langsung (+ Tambah Target ke-4)", "Tombol '⚙️ Custom Ping' yang redundan dihilangkan dari bilah target. Seluruh alur kini terpusat pada tombol '+ Tambah Target ke-4' / '✏️ Edit Target 4' yang membuka dialog praktis 1-form dengan preset cepat (Cloudflare 1.0.0.1, OpenDNS 208.67.222.222, Gateway Lokal) serta tombol hapus target."),
            ("⚡ Mesin Fallback Throughput Total Sistem (resolve_traffic_stats)", "Memperbaiki bug jarum speed dial yang diam di 0 Kbps akibat ketidakcocokan nama alias Windows. Sistem secara cerdas memindai adapter aktif, adapter kandidat yang terhubung, dan fallback ke total delta I/O sistem sehingga jarum speedometer selalu responsif mengayun saat trafik internet berjalan."),
            ("🚀 Ultra-Smooth 60 FPS Exponential Lerping & Zero Idle CPU", "Animasi jarum analog dan dial sirkular bergerak sangat halus dengan interpolasi eksponensial (lerp), dan siklus animasi canvas otomatis tidur saat kecepatan konstan untuk memastikan pemakaian CPU tetap 0.0%."),
        ],
    },
    "v2.5": {
        "title": "🏎️ VERSI 2.5 (Sports Car Speedtest Tachometer, Staged Refresh Delay & 60 FPS Ultra-Smooth)",
        "date": "September 2026",
        "badge": "STABLE RELEASE",
        "badge_color": ("#E0F2FE", "#0C4A6E"),
        "badge_text_color": "#0284C7",
        "items": [
            ("🏎️ Sports Car Tachometer Speedometer di Speedtest Suite", "Menggantikan speedometer lama dengan SportsCarSpeedGauge berdesain instrumen supercar 250° arc, Redline Rev-Meter Zone (>80% skala), Dynamic Scale Tiers (100, 250, 500, hingga 1000 Mbps), Dynamic Peak Hold Pip cyan #38BDF8, serta digital center HUD readout."),
            ("⏳ Animasi Refresh Staged Delay & Tactile Pacing", "Peningkatan timing dan tahapan animasi refresh modul (~2.2 detik) yang memberikan jeda visual nyata dan berbobot saat memindai adapter PCIe/Docking, routing table, ICMP probing, dan QoS sebelum memperbarui modul dan memainkan chimes audio."),
            ("✨ Splash Screen Synchronized v2.5 & Zero Flicker", "Label versi pada splash screen frameless kini menampilkan 'v2.5 • Zero-Drop Zoom' secara presisi, didukung eliminasi total jeda/flicker jendela sebelum animasi splash screen selesai."),
            ("⚡ Re-Optimasi 0.0% CPU Idle & Clean Teardown", "Canvas redraw dihentikan secara cerdas saat kecepatan konstan untuk menjaga utilisasi CPU 0%, dilengkapi implementasi destroy() bersih pada seluruh komponen animasi untuk mencegah background memory leaks."),
            ("📜 Dynamic Version History & Changelog Navigation", "Bilah navigasi tombol versi di dialog Changelog kini di-generate secara dinamis otomatis dari database riwayat versi tanpa batasan hardcoded."),
        ],
    },
    "v2.4": {
        "title": "🏎️ VERSI 2.4 (Sports Car Cluster, Inline QoS, Dynamic 1-8 Adapters & 4th Target)",
        "date": "September 2026",
        "badge": "STABLE RELEASE",
        "badge_color": ("#E0F2FE", "#0C4A6E"),
        "badge_text_color": "#0284C7",
        "items": [
            ("🏎️ Cluster Tachometer Supercar & Spectrum Bar Ganda", "Instrumen monitor bergaya kluster supercar dengan jarum tachometer analog 60 FPS, redline glow dinamis, dan speedometer HUD digital. Dilengkapi bilah spectrum ganda untuk tiap target server aktif (6 bilah untuk 3 target default, 8 bilah saat target ke-4 diaktifkan)."),
            ("🎛️ Inline Bandwidth QoS Monitor di Dashboard Utama", "Monitor alokasi bandwidth langsung di layar utama tepat di bawah speedometer. Pantau lalu lintas data aplikasi konferensi video (Zoom, Google Meet, Microsoft Teams) dan live streaming (OBS Studio, vMix) dengan tombol cepat 1-klik 'Boost Meeting' dan 'Boost Streaming'."),
            ("🔌 Kartu Antarmuka Adaptif & Responsif (1 s.d. 8 Port)", "Sistem cerdas yang menyesuaikan tata letak dengan perangkat keras Anda. Laptop dengan 1 port LAN hanya menampilkan 1 kartu lebar; jika ada 1 LAN + 1 Wi-Fi tampil 2 kolom; jika ada 3 kartu tampil 3 kolom; serta mendukung hingga 8 port untuk PC workstation / server."),
            ("🎯 Penambahan Target Server Ke-4 (+ Tambah IP Target)", "Modal interaktif untuk menambahkan IP target ke-4 (misalnya OpenDNS 208.67.222.222 atau gateway router lokal) langsung dari dashboard dengan validasi IPv4 otomatis."),
            ("⚡ Eliminasi Glitch Splash Screen (Zero Delay Startup)", "Jendela utama disembunyikan sempurna sejak inisialisasi awal sehingga tidak ada lagi flicker/tampilan jendela sebelum splash screen selesai memutar animasinya."),
            ("🔍 Riwayat Log Lengkap & Dialog Pencarian", "Panel aktivitas di dashboard dibuat lebih ramping dan efisien, dilengkapi tombol 'Buka Log Lengkap' untuk membuka dialog riwayat menyeluruh dengan filter kategori dan fitur ekspor."),
            ("👶 Bahasa Pengaturan Formal yang Mudah Dipahami", "Panduan pengaturan didesain ulang dalam bahasa Indonesia formal yang sangat ramah pemula, manula, hingga teknisi jaringan profesional."),
        ],
    },
    "v2.3": {
        "title": "⚡ VERSI 2.3 (Optimization, Custom Probing, GPU Telemetry & QoS)",
        "date": "September 2026",
        "badge": "STABLE RELEASE",
        "badge_color": ("#E0F2FE", "#0C4A6E"),
        "badge_text_color": "#0284C7",
        "items": [
            ("✨ Enterprise Frameless Splash Screen", "Window 560x340 frameless, radial gradient gelap, logo Barong bulat berputar dengan 60 FPS gradient ring spinner (merah-oranye-emas), dynamic monospace status 0-100%, dan transisi alpha fadeout halus."),
            ("🎯 Custom Ping Target & Advanced Probing", "Kustomisasi 3 IP target probing (Simple Mode: cukup masukkan IP, misal 1.1.1.1, 8.8.8.8, 9.9.9.9) serta Advanced Mode (interval probing, timeout ms, RTO threshold, payload size, dan Source IP Binding)."),
            ("⌨️ Keyboard Shortcuts & Settings Modal", "Dukungan tombol pintas keyboard lengkap (F11 Fullscreen, Ctrl+R Refresh, Ctrl+M Monitoring, Ctrl+T Speedtest, Ctrl+Q QoS, Ctrl+U Mute, Ctrl+S Settings) yang bisa dikustomisasi di jendela Settings."),
            ("💻 Live GPU Usage & Sleek Mini Monitors", "Pemantauan beban GPU real-time (Nvidia/Intel/DirectX) via non-blocking background thread. Visual meter mini di footer menggantikan ASCII kasar dengan tampilan modern dan halus."),
            ("🎛️ Bandwidth QoS Presets & vMixService Fix", "Pembersihan deteksi proses palsu (mengecualikan background service vMixService.exe) dan penambahan 1-Click Priority Presets untuk Video Conference (Zoom/Meet/Teams) dan Live Streaming (OBS/vMix)."),
            ("🖥️ Auto-Maximized & Responsive Layout", "Aplikasi otomatis terbuka maksimal (fit screen) tanpa ada card atau log yang terpotong, dengan dukungan resize responsif hingga 820x560."),
            ("🔄 Unified Module Refresh", "Tombol reload terpisah di header diintegrasikan ke tombol 🔄 Refresh yang otomatis memicu preloader dan merefresh seluruh modul sistem."),
        ],
    },
    "v2.2": {
        "title": "🚀 VERSI 2.2 (Multi-Platform Bundle, QoS Allocator & Fastfetch)",
        "date": "September 2026",
        "badge": "RELEASE",
        "badge_color": ("#E0F2FE", "#0C4A6E"),
        "badge_text_color": "#0284C7",
        "items": [
            ("📦 Multi-Platform Packaging", "Bundle rilis mandiri: Windows (.zip / .exe), macOS Apple Silicon M1/M2/M3 (.dmg) dengan icon resmi Barong modula.icns, dan Linux (.tar.gz)."),
            ("🔊 Audio Alert Engine", "Sintesis suara real-time untuk event port connect, disconnect, failover alarm, dan peringatan beban ekstrem (>85%) dengan master mute switch."),
            ("💬 Toast Bubble Manager", "Notifikasi melayang modern di sudut kanan bawah layar untuk setiap aksi jaringan."),
            ("🎛️ Application Bandwidth QoS", "Alokasi persentase bandwidth pintar antar aplikasi aktif dengan auto-balancing 100% dan Windows NetQoS policies."),
            ("💻 Fastfetch Hardware Diagnostics", "Modal spesifikasi hardware PC lengkap dan grafik canvas rolling 60 detik CPU/RAM."),
            ("📊 Smooth 60 FPS Visualizer", "3 mode grafik ikonik: Cyber Spectrum Bars, RF Internet Wave, dan Smooth Curve anti-patah."),
            ("⚡ 4-Engine Speedtest & Detail Modal", "Benchmark simultan ke Ookla, Fast.com Netflix, nPerf, dan Cloudflare Anycast dengan Deep Telemetry Modal (Rating A+ sampai F)."),
        ],
    },
    "v2.1": {
        "title": "🐲 VERSI 2.1 (MODULA Rebranding & Barong Theme)",
        "date": "September 2026",
        "badge": "OVERHAUL",
        "badge_color": ("#FEF3C7", "#78350F"),
        "badge_text_color": "#D97706",
        "items": [
            ("🎨 Rebranding MODULA", "Nama resmi berganti menjadi 'MODULA - Smart Auto Failover' dengan logo Topeng Barong Bali."),
            ("🎯 Dual Mode Palette", "Dark Mode & Light Mode berpalet Barong Gold, Crimson, dan Obsidian."),
            ("⚡ 4-Provider Speedtest Suite", "Integrasi speedtest langsung ke Cloudflare, nPerf, Ookla, dan Fast.com."),
            ("📶 Multi-Interface Detection", "Peningkatan deteksi cerdas untuk koneksi simultan 2 LAN dan Wi-Fi."),
        ],
    },
    "v2.0": {
        "title": "🛡️ VERSI 2.0 (Dual-Mode & Multi-Port Monitor)",
        "date": "September 2026",
        "badge": "MAJOR",
        "badge_color": ("#EDE9FE", "#4C1D95"),
        "badge_text_color": "#7C3AED",
        "items": [
            ("🌓 Dark & Light Mode", "Dukungan tema ganda dinamis dengan persistensi config.json."),
            ("🔌 Port Summary & Manual Toggles", "Informasi jumlah port Ethernet dan Wireless aktif beserta tombol toggle enable/disable per kartu."),
            ("📈 Traffic Chart Monitor", "Visualisasi throughput live dan perhitungan Jitter real-time sesuai formula IETF RFC 3550."),
            ("🧪 20-Persona Quality Assessment", "Rangkaian simulasi 20 skenario pengguna dunia nyata."),
        ],
    },
    "v1.0": {
        "title": "📦 VERSI 1.0 (Fondasi Zero-Drop Failover)",
        "date": "September 2026",
        "badge": "INITIAL",
        "badge_color": ("#F1F5F9", "#1E293B"),
        "badge_text_color": "#64748B",
        "items": [
            ("🛡️ Zero-Drop UDP Routing", "Failover berbasis Layer-3 Metric switching tanpa memutus socket Zoom / Teams."),
            ("⚡ Anti-Flapping State Machine", "Mencegah osilasi bolak-balik dengan syarat 5x sukses berturut-turut."),
            ("📝 Activity Log & Restoration", "Logging event failover dan pemulihan otomatis metrik saat aplikasi ditutup."),
            ("👤 Watermark & Author Link", "Dedicated project by parikesitad-pm."),
        ],
    },
}


class ChangelogModal(ctk.CTkToplevel):
    """
    Interactive Version History & Changelog Modal for MODULA.
    Features version shortcut tabs to jump directly between releases.
    """

    def __init__(self, master):
        super().__init__(master)
        self.title("📜 Riwayat Versi & Changelog • MODULA")
        self.geometry("700x620")
        self.minsize(620, 480)

        self.transient(master)
        self.grab_set()

        self.current_version = "v2.6"
        self._build_ui()
        self._show_version("v2.6")

    def _build_ui(self):
        self.configure(fg_color=("#F8FAFC", "#12141C"))
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1. Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=20, pady=(16, 6), sticky="ew")

        ctk.CTkLabel(
            header,
            text="📜 MODULA Versioning & Release Changelog",
            font=("Segoe UI", 16, "bold"),
            text_color=("#D97706", "#F59E0B"),
        ).pack(anchor="w")

        ctk.CTkLabel(
            header,
            text="Jelajahi riwayat evolusi, fitur baru, dan optimasi arsitektur di setiap versi.",
            font=("Segoe UI", 11),
            text_color=("#64748B", "#94A3B8"),
        ).pack(anchor="w")

        # 2. Version Shortcut Navigation Bar
        nav_bar = ctk.CTkFrame(
            self,
            fg_color=("#FFFFFF", "#181A24"),
            corner_radius=10,
            border_width=1,
            border_color=("#CBD5E1", "#242938"),
        )
        nav_bar.grid(row=1, column=0, padx=20, pady=6, sticky="ew")

        ctk.CTkLabel(
            nav_bar,
            text="PILIH VERSI:",
            font=("Segoe UI", 10, "bold"),
            text_color=("#64748B", "#94A3B8"),
        ).pack(side="left", padx=12, pady=10)

        self.ver_buttons: Dict[str, ctk.CTkButton] = {}
        for idx, ver_key in enumerate(CHANGELOG_DATA.keys()):
            is_latest = (idx == 0)
            ver_lbl = f"🏎️ {ver_key} (Terbaru)" if is_latest else f"📦 {ver_key}"
            btn = ctk.CTkButton(
                nav_bar,
                text=ver_lbl,
                command=lambda v=ver_key: self._show_version(v),
                font=("Segoe UI", 10, "bold"),
                fg_color=("#D97706", "#F59E0B") if is_latest else ("#E2E8F0", "#242938"),
                hover_color=("#B45309", "#D97706"),
                text_color=("#FFFFFF", "#0F172A") if is_latest else ("#0F172A", "#F8FAFC"),
                height=28,
                width=115 if is_latest else 68,
            )
            btn.pack(side="left", padx=2)
            self.ver_buttons[ver_key] = btn

        # 3. Scrollable Release Content Card
        self.content_scroll = ctk.CTkScrollableFrame(
            self,
            corner_radius=10,
            border_width=1,
            border_color=("#CBD5E1", "#242938"),
            fg_color=("#FFFFFF", "#181A24"),
        )
        self.content_scroll.grid(row=2, column=0, padx=20, pady=6, sticky="nsew")

        # 4. Footer Close Bar
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=3, column=0, padx=20, pady=(6, 14), sticky="ew")

        ctk.CTkLabel(
            footer,
            text="Dibuat dengan dedikasi oleh parikesitad-pm • Lisensi MIT",
            font=("Segoe UI", 10),
            text_color=("#64748B", "#94A3B8"),
        ).pack(side="left")

        ctk.CTkButton(
            footer,
            text="Tutup",
            command=self.destroy,
            font=("Segoe UI", 11),
            fg_color=("#E2E8F0", "#2D3139"),
            hover_color=("#CBD5E1", "#374151"),
            text_color=("#0F172A", "#F8FAFC"),
            width=90,
            height=30,
        ).pack(side="right")

    def _show_version(self, ver_key: str):
        SoundEngine.play(SoundType.ACTION)
        self.current_version = ver_key

        # Update button highlights
        for k, btn in self.ver_buttons.items():
            if k == ver_key:
                btn.configure(
                    fg_color=("#D97706", "#F59E0B"),
                    text_color=("#FFFFFF", "#0F172A"),
                )
            else:
                btn.configure(
                    fg_color=("#E2E8F0", "#242938"),
                    text_color=("#0F172A", "#F8FAFC"),
                )

        # Clear scrollable container
        for widget in self.content_scroll.winfo_children():
            widget.destroy()

        data = CHANGELOG_DATA.get(ver_key)
        if not data:
            return

        # Version Title & Badge Bar
        top_bar = ctk.CTkFrame(self.content_scroll, fg_color="transparent")
        top_bar.pack(fill="x", padx=14, pady=(10, 6))

        title_lbl = ctk.CTkLabel(
            top_bar,
            text=data["title"],
            font=("Segoe UI", 14, "bold"),
            text_color=("#0F172A", "#F8FAFC"),
        )
        title_lbl.pack(side="left")

        badge = ctk.CTkLabel(
            top_bar,
            text=f" {data['badge']} ",
            font=("Segoe UI", 9, "bold"),
            fg_color=data["badge_color"],
            text_color=data["badge_text_color"],
            corner_radius=6,
        )
        badge.pack(side="right")

        date_lbl = ctk.CTkLabel(
            self.content_scroll,
            text=f"📅 Tanggal Rilis: {data['date']}",
            font=("Segoe UI", 10),
            text_color=("#64748B", "#94A3B8"),
        )
        date_lbl.pack(anchor="w", padx=14, pady=(0, 10))

        # Items list
        for title, desc in data["items"]:
            item_box = ctk.CTkFrame(
                self.content_scroll,
                fg_color=("#F8FAFC", "#1E222D"),
                corner_radius=8,
                border_width=1,
                border_color=("#E2E8F0", "#2E3345"),
            )
            item_box.pack(fill="x", padx=10, pady=5)

            h_box = ctk.CTkFrame(item_box, fg_color="transparent")
            h_box.pack(fill="x", padx=12, pady=(8, 2))

            ctk.CTkLabel(
                h_box,
                text=title,
                font=("Segoe UI", 11, "bold"),
                text_color=("#D97706", "#F59E0B"),
            ).pack(side="left")

            ctk.CTkLabel(
                item_box,
                text=desc,
                font=("Segoe UI", 10),
                text_color=("#334155", "#CBD5E1"),
                wraplength=600,
                justify="left",
            ).pack(anchor="w", padx=12, pady=(0, 8))
