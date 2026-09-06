import customtkinter as ctk


class HelpFaqModal(ctk.CTkToplevel):
    """
    Interactive Help & FAQ modal dialog explaining Zero-Drop mechanics,
    docking setups, USB tethering, and troubleshooting tips.
    Supports Dual Mode (Dark & Light).
    """

    def __init__(self, master):
        super().__init__(master)
        self.title("❓ Bantuan & FAQ • Smart Auto-Failover")
        self.geometry("640x650")
        self.minsize(540, 480)

        self.transient(master)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        self.configure(fg_color=("#F8FAFC", "#181A20"))
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=20, pady=(16, 8), sticky="ew")

        ctk.CTkLabel(
            header,
            text="❓ Panduan & Tanya Jawab (Help & FAQ)",
            font=("Segoe UI", 16, "bold"),
            text_color=("#0F172A", "#F8FAFC"),
        ).pack(anchor="w")

        ctk.CTkLabel(
            header,
            text="Informasi lengkap cara kerja sistem, trik hardware, dan pemecahan masalah",
            font=("Segoe UI", 11),
            text_color=("#64748B", "#94A3B8"),
        ).pack(anchor="w")

        # Scrollable textbox
        textbox = ctk.CTkTextbox(
            self,
            corner_radius=10,
            fg_color=("#FFFFFF", "#1E212B"),
            text_color=("#0F172A", "#E2E8F0"),
            font=("Segoe UI", 11),
            border_width=1,
            border_color=("#E2E8F0", "#2D3139"),
            wrap="word",
        )
        textbox.grid(row=1, column=0, padx=20, pady=8, sticky="nsew")

        faq_text = """
===================================================================
1. APA ITU 'ZERO-DROP' UNTUK ZOOM MEETING?
===================================================================
Zoom Meeting dan panggilan VoIP/Video menggunakan protokol transport UDP (connectionless).
Jika Anda menonaktifkan (disable) network adapter saat kabel putus:
- Windows akan langsung mematikan socket jaringan Zoom.
- Panggilan Anda akan freeze 5-15 detik dan muncul status "Reconnecting...".

Sebaliknya, Smart Auto-Failover membiarkan adapter tetap 'Connected', dan HANYA mengubah Route Metric di Windows. Hasilnya:
- Paket data UDP Zoom berikutnya seketika dialirkan keluar lewat jalur cadangan (LAN 2 / Wi-Fi / HP).
- Media server Zoom mengenali roaming IP secara instan tanpa memutus sesi panggilan!

===================================================================
2. BAGAIMANA CARA KERJA SISTEM METRIC?
===================================================================
Di sistem operasi (Windows & Mac), rute default internet ditentukan oleh nilai Metric:
- Metric 10: Jalur Utama (Primary) - Seluruh traffic Zoom keluar lewat sini.
- Metric 20: Jalur Cadangan 1 (Standby)
- Metric 30: Jalur Cadangan 2 (Standby)
- Metric 50: Jalur yang sedang mengalami gangguan/RTO (Demoted).

Nilai metric yang LEBIH KECIL selalu diprioritaskan oleh sistem operasi.

===================================================================
3. BAGAIMANA CARA MENAMBAH USB TETHERING DARI HP?
===================================================================
1. Hubungkan HP ke laptop menggunakan kabel data USB.
2. Di HP Anda: Buka Pengaturan -> Hotspot Pribadi / Tethering -> Aktifkan "USB Tethering".
3. Windows akan otomatis mengenali HP Anda sebagai adapter Ethernet baru (biasanya bernama Ethernet 2 / 3 atau Remote NDIS).
4. Di aplikasi ini: Klik tombol "🔄 Refresh Adapters", lalu pilih adapter HP tersebut di slot Priority 2 atau Priority 3.
5. Klik "▶ Start Monitoring".

===================================================================
4. APA FUNGSI REAL-TIME JITTER & BANDWIDTH MONITOR?
===================================================================
- Jitter adalah variasi selisih waktu antar paket (latency fluctuation). Untuk Zoom meeting, Jitter di bawah 10ms adalah sangat baik. Jitter di atas 30ms dapat menyebabkan suara patah-patah seperti robot.
- Throughput Monitor menampilkan konsumsi bandwidth Download (Rx) dan Upload (Tx) secara langsung di tiap adapter.

===================================================================
5. BAGAIMANA CARA SPEEDTEST MEMILIH INTERFACE?
===================================================================
Speedtest di aplikasi ini menggunakan teknologi socket source-binding. Setiap koneksi HTTP/HTTPS di-bind secara khusus ke Source IP adapter yang Anda pilih. Dengan demikian, Anda bisa menguji kecepatan LAN 1, LAN 2, dan Wi-Fi secara independen tanpa saling mengganggu.

===================================================================
6. APAKAH PENGATURAN AMAN KETIKA APLIKASI DITUTUP?
===================================================================
YA, 100% AMAN.
Aplikasi ini memiliki mekanisme keselamatan otomatis (Safety Teardown):
Begitu Anda menekan "Stop Monitoring" atau menutup jendela aplikasi, seluruh adapter otomatis dikembalikan ke setelan bawaan Windows: 'Automatic Metric' (Set-NetIPInterface -AutomaticMetric Enabled).
"""
        textbox.insert("1.0", faq_text.strip())
        textbox.configure(state="disabled")

        # Bottom Close Button
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=2, column=0, padx=20, pady=12, sticky="e")

        close_btn = ctk.CTkButton(
            btn_frame,
            text="Tutup",
            command=self.destroy,
            width=90,
            height=30,
            fg_color=("#3B82F6", "#2563EB"),
            hover_color=("#2563EB", "#1D4ED8"),
        )
        close_btn.pack()
