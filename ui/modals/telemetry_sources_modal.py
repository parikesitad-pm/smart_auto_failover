"""
MODULA - Smart Auto Failover
Network Probing & Telemetry Sources Explanation Modal.
Provides full technical transparency on ping targets, RFC 3550 Jitter,
and kernel NetIO bandwidth sampling.
"""
import os
import customtkinter as ctk

from core.sound_engine import SoundEngine, SoundType


class TelemetrySourcesModal(ctk.CTkToplevel):
    """
    Modal dialog detailing the exact network probing mechanisms,
    target IP addresses, RFC 3550 Jitter math, and Kernel NetIO metrics.
    """

    def __init__(self, master):
        super().__init__(master)
        self.title("🌐 Network Probing & Telemetry Sources • MODULA")
        self.geometry("680x620")
        self.minsize(620, 520)

        self.transient(master)
        self.grab_set()

        self._build_ui()
        SoundEngine.play(SoundType.ACTION)

    def _build_ui(self):
        self.configure(fg_color=("#F8FAFC", "#12141C"))
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1. Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=20, pady=(16, 8), sticky="ew")

        ctk.CTkLabel(
            header,
            text="🌐 Transparansi Probing Jaringan & Sumber Data",
            font=("Segoe UI", 16, "bold"),
            text_color=("#D97706", "#F59E0B"),
        ).pack(anchor="w")

        ctk.CTkLabel(
            header,
            text="Penjelasan teknis target ICMP ping, formula RFC 3550 Jitter, dan Kernel NetIO counters",
            font=("Segoe UI", 11),
            text_color=("#64748B", "#94A3B8"),
        ).pack(anchor="w")

        # 2. Scrollable Content
        scroll = ctk.CTkScrollableFrame(
            self,
            corner_radius=10,
            fg_color=("#FFFFFF", "#181A24"),
            border_width=1,
            border_color=("#CBD5E1", "#242938"),
        )
        scroll.grid(row=1, column=0, padx=20, pady=8, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        # Section 1: Ping Targets
        self._add_card(
            scroll,
            title="🎯 Kemana Saja Ping / Probing Dikirim?",
            content=(
                "MODULA melakukan ICMP Echo Probing aktif secara berkala (default: interval 1000ms, timeout 800ms) "
                "ke target Anycast Tier-1 global dengan latensi terendah di dunia:\n\n"
                "• 🥇 Primary Target: 1.1.1.1 (Cloudflare Anycast DNS)\n"
                "  Pusat data terdekat (Jakarta/Singapura Equinix) via rute BGP peering langsung.\n\n"
                "• 🥈 Secondary Target: 8.8.8.8 (Google Public DNS Anycast)\n"
                "  Digunakan sebagai verifikasi sekunder jika target primer mengalami packet drop.\n\n"
                "• 🥉 Tertiary Fallback: 9.9.9.9 (Quad9 Anycast) & Default Gateway\n"
                "  Memastikan apakah kegagalan ada di link lokal (kabel putus) atau rute WAN internet.\n\n"
                "🔒 Catatan Penting (Source IP Binding):\n"
                "Ping TIDAK dikirim lewat rute default sistem biasa, melainkan DI-BINDING KHUSUS ke Source IP "
                "masing-masing adapter (menggunakan flag 'ping -S <source_ip>' di Windows atau SO_BINDTODEVICE di Unix). "
                "Dengan cara ini, LAN 1, LAN 2, dan Wi-Fi dapat dipantau secara simultan dan independen!"
            ),
            badge="Target Anycast BGP",
            badge_color=("#D1FAE5", "#064E3B"),
            text_badge_color=("#065F46", "#6EE7B7"),
        )

        # Section 2: Jitter Formula
        self._add_card(
            scroll,
            title="📶 Dari Mana Angka Jitter Diperoleh? (Standar RFC 3550)",
            content=(
                "Jitter yang ditampilkan MODULA BUKAN angka acak, melainkan dihitung menggunakan formula resmi "
                "IETF RFC 3550 (standar RTP Audio/Video yang persis digunakan oleh Zoom, Cisco Webex, dan Discord VoIP):\n\n"
                "  J(i) = J(i-1) + (|D(i-1, i)| - J(i-1)) / 16\n\n"
                "Keterangan Formula:\n"
                "• D(i-1, i) = Latency(i) - Latency(i-1) (Selisih waktu tempuh antar paket ping berturut-turut).\n"
                "• Angka 16 adalah faktor exponential smoothing filter yang meredam noise sesaat.\n\n"
                "Kriteria Kualitas Jaringan:\n"
                "• 🟢 Jitter < 5 ms    : Sempurna (Zero stutter audio/video pada Zoom call)\n"
                "• 🟡 Jitter 5 - 15 ms : Cukup baik (Sedikit variasi latensi, masih lancar)\n"
                "• 🔴 Jitter > 15 ms   : Buruk (Gejala bufferbloat / jitter buffer Zoom mulai freeze)"
            ),
            badge="Formula RFC 3550",
            badge_color=("#FEF3C7", "#78350F"),
            text_badge_color=("#92400E", "#FDE68A"),
        )

        # Section 3: Download & Upload Throughput
        self._add_card(
            scroll,
            title="⬇️⬆️ Dari Mana Angka Download & Upload Berasal?",
            content=(
                "MODULA membaca langsung statistik perangkat keras jaringan melalui OS Kernel Network Counters "
                "(psutil.net_io_counters per-NIC):\n\n"
                "1. Real-Time Delta Throughput (di Dashboard Utama):\n"
                "   Mengambil counter bytes_recv dan bytes_sent dari driver jaringan setiap detik:\n"
                "   Download (kbps) = (bytes_recv_now - bytes_recv_prev) * 8 / (1000 * dt)\n"
                "   Upload (kbps)   = (bytes_sent_now - bytes_sent_prev) * 8 / (1000 * dt)\n"
                "   Ini mencerminkan seluruh beban bandwidth real-time yang sedang digunakan di laptop Anda.\n\n"
                "2. Benchmark Speedtest Suite (di Modal Speedtest 4-Provider):\n"
                "   Mengalirkan stream multi-chunk HTTP/HTTPS paralel langsung ke node server:\n"
                "   • Cloudflare: https://speed.cloudflare.com/__down (50MB streaming chunk)\n"
                "   • Fast.com: Netflix Open Connect CDN edge servers (OCA Direct)\n"
                "   • nPerf: Multi-CDN Anycast bandwidth nodes\n"
                "   • Ookla: Ookla Speedtest Network endpoints\n"
                "   Hasilnya dihitung berdasarkan throughput puncak (Mbps) dan bufferbloat loaded latency."
            ),
            badge="Kernel NetIO & Edge CDN",
            badge_color=("#DBEAFE", "#1E3A8A"),
            text_badge_color=("#1E40AF", "#93C5FD"),
        )

        # 3. Close Button
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=2, column=0, padx=20, pady=(4, 14), sticky="ew")

        close_btn = ctk.CTkButton(
            footer,
            text="Tutup Informasi",
            command=self.destroy,
            font=("Segoe UI", 12, "bold"),
            fg_color=("#E2E8F0", "#2D3139"),
            hover_color=("#CBD5E1", "#374151"),
            text_color=("#0F172A", "#F8FAFC"),
            height=34,
            corner_radius=8,
        )
        close_btn.pack(side="right")

    def _add_card(self, parent, title: str, content: str, badge: str, badge_color: tuple, text_badge_color: tuple):
        card = ctk.CTkFrame(parent, fg_color=("#F1F5F9", "#1E212B"), corner_radius=8, border_width=1, border_color=("#CBD5E1", "#2D3139"))
        card.pack(fill="x", pady=6, padx=4)

        header_f = ctk.CTkFrame(card, fg_color="transparent")
        header_f.pack(fill="x", padx=12, pady=(10, 4))

        ctk.CTkLabel(
            header_f,
            text=title,
            font=("Segoe UI", 12, "bold"),
            text_color=("#0F172A", "#F8FAFC"),
        ).pack(side="left")

        b_lbl = ctk.CTkLabel(
            header_f,
            text=f" {badge} ",
            font=("Segoe UI", 9, "bold"),
            fg_color=badge_color,
            text_color=text_badge_color,
            corner_radius=4,
        )
        b_lbl.pack(side="right")

        content_lbl = ctk.CTkLabel(
            card,
            text=content,
            font=("Segoe UI", 10),
            text_color=("#334155", "#CBD5E1"),
            justify="left",
            wraplength=580,
        )
        content_lbl.pack(fill="x", padx=12, pady=(0, 10), anchor="w")
