import customtkinter as ctk


class ChangelogModal(ctk.CTkToplevel):
    """
    Modal dialog displaying the versioning history and changelog.
    Supports Dual Mode (Dark & Light).
    """

    def __init__(self, master):
        super().__init__(master)
        self.title("📜 Release Notes & Changelog • Smart Auto-Failover")
        self.geometry("540x560")
        self.minsize(480, 420)

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
            text="📜 Version History & Changelog",
            font=("Segoe UI", 16, "bold"),
            text_color=("#0F172A", "#F8FAFC"),
        ).pack(anchor="w")

        ctk.CTkLabel(
            header,
            text="Smart Auto-Failover Network Monitor by parikesitad-pm",
            font=("Segoe UI", 11),
            text_color=("#64748B", "#94A3B8"),
        ).pack(anchor="w")

        # Scrollable textbox for changelog
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

        changelog_text = """
===================================================================
🚀 VERSI 2.0 (Rilis Besar - Major Update)
===================================================================
Tanggal Rilis: September 2026

✨ Fitur Baru & Peningkatan:
1. Dual Mode (Dark & Light Mode):
   - Dukungan penuh pergantian tema Gelap (Dark) dan Terang (Light) secara instan.
   - Penyesuaian kontras tinggi pada kartu, sparkline, dan dialog.

2. Adapter Summary Bar & Manual Port Toggle:
   - Banner ringkasan jumlah port Ethernet dan Wireless aktif.
   - Indikator status berupa bubble 'Terhubung' dan 'Aktif (Zoom Route)'.
   - Saklar manual (Port On/Off) untuk menyambung atau memutus adapter tanpa cabut kabel.

3. Live Traffic & Throughput Monitoring:
   - Visualisasi grafik real-time untuk kecepatan Download (Rx) dan Upload (Tx).
   - Pengukuran Jitter instan (RFC 3550) dan Packet Loss meter.

4. Speedtest Suite Modal:
   - Pengujian kecepatan terpadu dengan 3 provider: Cloudflare Anycast, nPerf / Multi-CDN, dan Ookla.
   - Pilihan Individual Test (per adapter yang di-bind ke Source IP) maupun Bulk Test (semua adapter aktif).

5. Integrasi Footer & Dokumentasi:
   - Tombol Changelog dan Help & FAQ interaktif di footer.
   - Watermark dan tautan langsung ke profil GitHub pembuat (parikesitad-pm).

===================================================================
🌟 VERSI 1.0 (Rilis Perdana)
===================================================================
Tanggal Rilis: September 2026

✨ Fitur Inti:
1. Zero-Drop Zoom Failover:
   - Manipulasi Interface Metric di Windows (netsh & PowerShell) tanpa memutus socket UDP Zoom.
2. Health-Check ICMP Bound Source IP:
   - Probing independen menggunakan parameter ping -S <source_ip> ke 1.1.1.1.
3. 3-Tier Priority State Machine:
   - Skema prioritas: LAN 1 (Metric 10) -> LAN 2 (Metric 20) -> Wi-Fi (Metric 30).
   - Ambang batas failover: 2x RTO berturut-turut.
   - Auto-Recovery: 5x ping sukses berturut-turut.
4. Dukungan Multi-Platform Awal:
   - Arsitektur backend untuk Windows dan macOS.
   - Restorasi otomatis ke Windows Automatic Metric saat aplikasi ditutup.
"""
        textbox.insert("1.0", changelog_text.strip())
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
