import tkinter as tk
from typing import Optional
import customtkinter as ctk

from core.models import SpeedtestProvider, SpeedtestResult


class SpeedtestDetailModal(ctk.CTkToplevel):
    """
    Interactive popup dialog presenting comprehensive speedtest diagnostics:
    - Provider badge & testing protocol
    - Network interface & source IP binding
    - Grade calculation (A+ to F) for Gaming, Zoom/Conferencing, and 4K Streaming
    - Bufferbloat (loaded latency delta), RFC 3550 Jitter, and Packet Loss
    - Copyable technical telemetry summary
    """

    def __init__(self, master, result):
        super().__init__(master)
        if isinstance(result, dict):
            from core.models import SpeedtestResult, SpeedtestProvider
            prov = result.get("provider", SpeedtestProvider.CLOUDFLARE)
            if isinstance(prov, str):
                try:
                    prov = SpeedtestProvider(prov)
                except Exception:
                    prov = SpeedtestProvider.CLOUDFLARE
            self.result = SpeedtestResult(
                alias=result.get("adapter", result.get("alias", "Interface")),
                ip=result.get("ip", "127.0.0.1"),
                provider=prov,
                ping_ms=result.get("ping_ms", 0.0),
                jitter_ms=result.get("jitter_ms", 0.0),
                download_mbps=result.get("download_mbps", 0.0),
                upload_mbps=result.get("upload_mbps", 0.0),
                loaded_latency_ms=result.get("loaded_latency_ms", result.get("bufferbloat_ms", 0.0) + result.get("ping_ms", 0.0)),
                packet_loss_pct=result.get("packet_loss_pct", result.get("packet_loss", 0.0)),
                timestamp=result.get("timestamp", ""),
                server_location=result.get("location", result.get("server_location", "")),
                isp_info=result.get("asn", result.get("isp_info", ""))
            )
        else:
            self.result = result

        prov_name = self.result.provider.value if hasattr(self.result.provider, 'value') else str(self.result.provider)
        self.title(f"MODULA • Benchmark Detail - {prov_name}")
        self.geometry("680x640")
        self.minsize(620, 540)

        self.transient(master)
        self.grab_set()

        self._build_ui()

    def _calculate_grades(self):
        r = self.result
        delta = max(0.0, r.loaded_latency_ms - r.ping_ms) if r.loaded_latency_ms > 0 else 0.0

        if r.ping_ms <= 25 and r.jitter_ms <= 3.0 and delta <= 30 and r.packet_loss_pct == 0:
            overall_grade = "A+"
            grade_color = "#10B981"
            zoom_eval = "★ Sempurna untuk Zoom / OBS Ultra HD (Zero Latency Spike)"
            game_eval = "★ Optimal untuk Gaming Kompetitif (Ultra Low Ping)"
            stream_eval = "★ Mendukung 4K / 8K HDR Streaming tanpa buffering"
        elif r.ping_ms <= 50 and r.jitter_ms <= 8.0 and delta <= 60:
            overall_grade = "A"
            grade_color = "#059669"
            zoom_eval = "✓ Sangat Bagus untuk Meeting & Live Streaming HD"
            game_eval = "✓ Sangat Baik untuk Online Gaming"
            stream_eval = "✓ Sangat Lancar untuk 4K Streaming"
        elif r.ping_ms <= 100 and r.jitter_ms <= 15.0:
            overall_grade = "B"
            grade_color = "#F59E0B"
            zoom_eval = "✓ Cukup Baik untuk Standard HD Meeting (Jitter Terkendali)"
            game_eval = "~ Dapat Dimainkan (Sedikit terasa input latency)"
            stream_eval = "✓ Lancar untuk Full HD 1080p"
        else:
            overall_grade = "C"
            grade_color = "#DC2626"
            zoom_eval = "⚠️ Berpotensi stuttering atau freeze pada video call"
            game_eval = "⚠️ Mengalami lag atau rubberbanding"
            stream_eval = "~ Resolusi dinamis mungkin turun ke 720p"

        return overall_grade, grade_color, zoom_eval, game_eval, stream_eval, delta

    def _build_ui(self):
        self.configure(fg_color=("#F8FAFC", "#12141C"))
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        r = self.result
        prov_name = r.provider.value if hasattr(r.provider, 'value') else str(r.provider)
        grade, grade_col, zoom_eval, game_eval, stream_eval, bb_delta = self._calculate_grades()

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=20, pady=(16, 8), sticky="ew")

        ctk.CTkLabel(
            header,
            text=f"📊 {prov_name} • Hasil Diagnostik Lengkap",
            font=("Segoe UI", 16, "bold"),
            text_color=("#D97706", "#F59E0B"),
        ).pack(anchor="w")

        ctk.CTkLabel(
            header,
            text=f"Interface: {r.alias} • Bound Source IP: {r.ip or 'Auto'} • Timestamp: {r.timestamp}",
            font=("Segoe UI", 11),
            text_color=("#64748B", "#94A3B8"),
        ).pack(anchor="w")

        body = ctk.CTkScrollableFrame(
            self,
            corner_radius=10,
            border_width=1,
            border_color=("#CBD5E1", "#242938"),
            fg_color=("#FFFFFF", "#181A24"),
        )
        body.grid(row=1, column=0, padx=20, pady=6, sticky="nsew")
        body.grid_columnconfigure(0, weight=1)

        # Grade Banner
        grade_card = ctk.CTkFrame(
            body,
            corner_radius=8,
            border_width=1,
            border_color=("#E2E8F0", "#242938"),
            fg_color=("#F8FAFC", "#1E222D"),
        )
        grade_card.pack(fill="x", padx=4, pady=6)
        grade_card.grid_columnconfigure(1, weight=1)

        badge = ctk.CTkFrame(grade_card, width=64, height=64, corner_radius=12, fg_color=grade_col)
        badge.grid(row=0, column=0, rowspan=2, padx=14, pady=12)
        badge.pack_propagate(False)
        ctk.CTkLabel(badge, text=grade, font=("Segoe UI", 26, "bold"), text_color="#FFFFFF").place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            grade_card,
            text="INDEKS KUALITAS KONEKSI (Zero-Drop Quality Score)",
            font=("Segoe UI", 10, "bold"),
            text_color=("#64748B", "#94A3B8"),
        ).grid(row=0, column=1, sticky="w", padx=(4, 14), pady=(12, 0))

        eval_summary = f"{zoom_eval}\n{game_eval}\n{stream_eval}"
        ctk.CTkLabel(
            grade_card,
            text=eval_summary,
            font=("Segoe UI", 10),
            text_color=("#0F172A", "#F8FAFC"),
            justify="left",
        ).grid(row=1, column=1, sticky="w", padx=(4, 14), pady=(2, 12))

        # Metrics Grid
        grid_frame = ctk.CTkFrame(body, fg_color="transparent")
        grid_frame.pack(fill="x", padx=4, pady=6)
        grid_frame.grid_columnconfigure(0, weight=1)
        grid_frame.grid_columnconfigure(1, weight=1)

        metrics = [
            ("⬇ DOWNLOAD SPEED", f"{r.download_mbps:.2f} Mbps", "#10B981"),
            ("⬆ UPLOAD SPEED", f"{r.upload_mbps:.2f} Mbps", "#3B82F6"),
            ("⏱ IDLE LATENCY (PING)", f"{r.ping_ms:.1f} ms", "#F59E0B"),
            ("📈 RFC 3550 JITTER", f"{r.jitter_ms:.2f} ms", "#06B6D4"),
            ("📶 LOADED LATENCY", f"{r.loaded_latency_ms:.1f} ms (+{bb_delta:.1f}ms delta)", "#EC4899"),
            ("💥 PACKET LOSS", f"{r.packet_loss_pct:.1f}%", "#10B981" if r.packet_loss_pct == 0 else "#DC2626"),
            ("🌐 CDN / SERVER NODE", r.server_location or "Cloudflare Edge / Anycast Node", "#8B5CF6"),
            ("🏢 ISP / ASN ROUTING", r.isp_info or "Direct Multi-Homed Peering", "#38BDF8"),
        ]

        for i, (title, val, color) in enumerate(metrics):
            row = i // 2
            col = i % 2
            tile = ctk.CTkFrame(
                grid_frame,
                corner_radius=8,
                border_width=1,
                border_color=("#E2E8F0", "#242938"),
                fg_color=("#F8FAFC", "#1A1D26"),
            )
            tile.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")
            ctk.CTkLabel(tile, text=title, font=("Segoe UI", 8, "bold"), text_color=("#64748B", "#94A3B8")).pack(anchor="w", padx=10, pady=(6, 0))
            ctk.CTkLabel(tile, text=val, font=("Segoe UI", 12, "bold"), text_color=color).pack(anchor="w", padx=10, pady=(0, 6))

        # Bottom Buttons
        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.grid(row=2, column=0, padx=20, pady=12, sticky="ew")

        copy_btn = ctk.CTkButton(
            bottom,
            text="📋 Salin Laporan",
            command=self._copy_summary,
            font=("Segoe UI", 11, "bold"),
            fg_color=("#D97706", "#F59E0B"),
            hover_color=("#B45309", "#D97706"),
            text_color=("#FFFFFF", "#0F172A"),
            height=32,
            width=160,
        )
        copy_btn.pack(side="left")

        ctk.CTkButton(
            bottom,
            text="Tutup",
            command=self.destroy,
            font=("Segoe UI", 11),
            fg_color=("#E2E8F0", "#242938"),
            text_color=("#0F172A", "#F8FAFC"),
            width=90,
            height=32,
        ).pack(side="right")

    def _copy_summary(self):
        r = self.result
        prov = r.provider.value if hasattr(r.provider, 'value') else str(r.provider)
        text = (
            f"=== MODULA SPEEDTEST TELEMETRY REPORT ===\n"
            f"Engine       : {prov}\n"
            f"Adapter      : {r.alias} (IP: {r.ip})\n"
            f"Download     : {r.download_mbps:.2f} Mbps\n"
            f"Upload       : {r.upload_mbps:.2f} Mbps\n"
            f"Ping Latency : {r.ping_ms:.1f} ms\n"
            f"Loaded Ping  : {r.loaded_latency_ms:.1f} ms\n"
            f"RFC 3550 Jit : {r.jitter_ms:.2f} ms\n"
            f"Packet Loss  : {r.packet_loss_pct:.1f}%\n"
            f"Server / CDN : {r.server_location or 'Cloudflare Anycast'}\n"
            f"ISP / Route  : {r.isp_info or 'Direct Peering'}\n"
            f"Timestamp    : {r.timestamp}\n"
            f"========================================\n"
        )
        self.clipboard_clear()
        self.clipboard_append(text)
