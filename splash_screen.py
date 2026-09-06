"""
MODULA - Smart Auto Failover
Enterprise Frameless Splash Screen (v2.6)

Spesifikasi:
- Window frameless (overrideredirect), 560x340, center screen, always on top
- Radial dark gradient background (#1b1512 ke #0a0908)
- Logo Barong bulat (modula_logo.png) diapit rotating ring spinner gradient merah-oranye-emas (60 FPS)
- Nama aplikasi "MODULA" font besar bold dengan letter-spacing lebar & warna oranye emas (#FF9A3C)
- Tagline "SMART AUTO FAILOVER" tracking uppercase abu-abu slate
- Progress bar tipis CTkProgressBar warna gradient oranye (#F97316)
- Dynamic status text monospace dengan persentase dan fase loading jaringan
- Margin 14px inner frame dengan corner brackets aksen emas (#D4AF37)
- Smooth alpha fadeout saat 100% dan membuka window utama MODULA
"""

import math
import os
import sys
import time
import tkinter as tk
from typing import Callable, Optional
import customtkinter as ctk
from PIL import Image, ImageDraw, ImageTk

# Base directory discovery for frozen and development environments
if getattr(sys, "frozen", False):
    BASE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ASSETS_DIR = os.path.join(BASE_DIR, "assets")
LOGO_PATH = os.path.join(ASSETS_DIR, "modula_logo.png")


class SplashScreen(ctk.CTkToplevel):
    """
    Frameless, high-tech HUD splash screen for MODULA.
    Displays animated rotating spinner, Barong logo, real-time stage progress,
    and transitions seamlessly into the main application.
    """

    WIDTH = 560
    HEIGHT = 340

    def __init__(
        self,
        master=None,
        on_finish: Optional[Callable[[], None]] = None,
        duration: float = 3.0,
        version_text: str = "v2.6",
    ):
        if master is None:
            self._own_root = ctk.CTk()
            self._own_root.withdraw()
            super().__init__(self._own_root)
            self._standalone = True
        else:
            self._own_root = None
            super().__init__(master)
            self._standalone = False

        self.on_finish = on_finish
        self.duration = max(1.0, duration)
        self.version_text = version_text
        self.start_time = time.time()
        self.spin_angle = 0
        self.current_progress = 0.0
        self._fading = False
        self.is_active = True

        # Configure Window
        self.title("MODULA • Initializing...")
        self.overrideredirect(True)
        self._center_window()
        self.attributes("-topmost", True)

        # Set appearance mode dark
        ctk.set_appearance_mode("Dark")

        # Build UI Elements
        self._build_ui()

        # Start 60 FPS animation loop
        self._anim_tick()

    def _center_window(self):
        """Center the 560x340 frameless window on the active monitor."""
        self.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = max(0, (screen_w - self.WIDTH) // 2)
        y = max(0, (screen_h - self.HEIGHT) // 2)
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}+{x}+{y}")

    def _create_radial_background(self, w: int, h: int) -> ImageTk.PhotoImage:
        """Render high-speed radial gradient background from #201713 at top-center to #0a0908."""
        bg = Image.new("RGB", (w, h), "#0a0908")
        draw = ImageDraw.Draw(bg)
        cx, cy = w // 2, 88
        steps = 45
        for i in range(steps, 0, -1):
            f = i / steps
            r = int(10 + (36 - 10) * f)
            g = int(9 + (26 - 9) * f)
            b = int(8 + (20 - 8) * f)
            rx = int(320 * f)
            ry = int(220 * f)
            draw.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=(r, g, b))
        return ImageTk.PhotoImage(bg)

    def _prepare_logo(self, size: int = 76) -> Optional[ImageTk.PhotoImage]:
        """Crop and mask circular Barong logo avatar with smooth anti-aliasing."""
        if os.path.exists(LOGO_PATH):
            try:
                img = Image.open(LOGO_PATH).convert("RGBA")
                w, h = img.size
                cx, cy = int(w * 0.5), int(h * 0.40)
                r = int(min(w, h) * 0.35)
                crop_box = (cx - r, cy - r, cx + r, cy + r)
                face = img.crop(crop_box).resize((size, size), Image.Resampling.LANCZOS)

                # Circular mask
                mask = Image.new("L", (size, size), 0)
                ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)

                out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
                out.paste(face, (0, 0), mask=mask)
                return ImageTk.PhotoImage(out)
            except Exception as e:
                print(f"[!] Warning: Could not process logo for splash: {e}")

        # Fallback procedural circular badge if image file is missing
        fallback = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(fallback)
        draw.ellipse((2, 2, size - 2, size - 2), fill="#D4AF37", outline="#FFB703", width=2)
        draw.text((size // 2, size // 2), "M", fill="#0A0908", anchor="mm")
        return ImageTk.PhotoImage(fallback)

    def _build_ui(self):
        """Construct the canvas, HUD brackets, logo, spinner, progress bar, and status labels."""
        w, h = self.WIDTH, self.HEIGHT

        # 1. Main Canvas
        self.canvas = tk.Canvas(
            self,
            width=w,
            height=h,
            highlightthickness=0,
            bg="#0a0908",
        )
        self.canvas.pack(fill="both", expand=True)

        # 2. Radial Gradient Background
        self.bg_photo = self._create_radial_background(w, h)
        self.canvas.create_image(0, 0, image=self.bg_photo, anchor="nw")

        # 3. Inner Frame (14px Margin) & Cyber HUD Corner Accents
        m = 14
        self.canvas.create_rectangle(m, m, w - m, h - m, outline="#2a221d", width=1)
        gold = "#d4af37"
        arm = 14

        # Top-Left Bracket
        self.canvas.create_line(m, m + arm, m, m, m + arm, m, fill=gold, width=2)
        # Top-Right Bracket
        self.canvas.create_line(w - m - arm, m, w - m, m, w - m, m + arm, fill=gold, width=2)
        # Bottom-Left Bracket
        self.canvas.create_line(m, h - m - arm, m, h - m, m + arm, h - m, fill=gold, width=2)
        # Bottom-Right Bracket
        self.canvas.create_line(w - m - arm, h - m, w - m, h - m, w - m, h - m - arm, fill=gold, width=2)

        # 4. Center Coordinates for Logo & Spinner
        cx, cy = w // 2, 88

        # Subtle ambient halo behind logo
        self.canvas.create_oval(cx - 44, cy - 44, cx + 44, cy + 44, fill="#1a130f", outline="#382618", width=1)

        # Circular Barong Logo
        self.logo_photo = self._prepare_logo(76)
        if self.logo_photo:
            self.canvas.create_image(cx, cy, image=self.logo_photo, anchor="center")

        # 5. Multi-Color Rotating Gradient Ring Spinner (Radius 48px)
        spin_r = 48
        bbox = (cx - spin_r, cy - spin_r, cx + spin_r, cy + spin_r)
        # Crimson Red Arc
        self.arc1 = self.canvas.create_arc(bbox, start=0, extent=85, style="arc", outline="#E63946", width=3)
        # Vibrant Orange Arc
        self.arc2 = self.canvas.create_arc(bbox, start=115, extent=75, style="arc", outline="#F97316", width=3)
        # Radiant Gold Arc
        self.arc3 = self.canvas.create_arc(bbox, start=220, extent=65, style="arc", outline="#F59E0B", width=3)
        # Leading Edge Gold Sparkle
        self.arc4 = self.canvas.create_arc(bbox, start=325, extent=20, style="arc", outline="#FFD166", width=3)

        # Inner subtle counter-rotating ring (Radius 42px)
        inner_r = 42
        in_box = (cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r)
        self.arc_inner = self.canvas.create_arc(in_box, start=0, extent=160, style="arc", outline="#3D281E", width=1)

        # 6. App Name "MODULA" with Wide Letter Spacing & Drop Shadow
        title_font = ("Segoe UI", 24, "bold")
        self.canvas.create_text(cx + 1, 161, text="M O D U L A", font=title_font, fill="#381804")  # Shadow
        self.canvas.create_text(cx, 160, text="M O D U L A", font=title_font, fill="#FF9A3C")

        # 7. Tagline "SMART AUTO FAILOVER"
        tag_font = ("Segoe UI", 8, "bold")
        self.canvas.create_text(cx, 186, text="S M A R T   A U T O   F A I L O V E R", font=tag_font, fill="#8E847D")

        # 8. Thin CTkProgressBar
        self.progress_bar = ctk.CTkProgressBar(
            self,
            width=380,
            height=5,
            corner_radius=2,
            progress_color="#F97316",
            fg_color="#1E1814",
            border_width=1,
            border_color="#382A22",
        )
        self.progress_bar.set(0.0)
        self.progress_bar.place(in_=self, relx=0.5, y=218, anchor="center")

        # 9. Dynamic Status Text (Monospace font with percentage indicator)
        status_font = ("Consolas", 9)
        self.status_txt = self.canvas.create_text(
            cx,
            248,
            text="[   0% ]  Mendeteksi physical & virtual network adapter...",
            font=status_font,
            fill="#CBD5E1",
        )

        # 10. Footers
        foot_font = ("Segoe UI", 8)
        foot_color = "#6B625B"
        # Left: App Version
        self.canvas.create_text(28, 314, text=f"{self.version_text} • Zero-Drop Zoom", font=foot_font, fill=foot_color, anchor="w")
        # Right: Developer Name
        self.canvas.create_text(532, 314, text="Dibuat oleh parikesitad-pm", font=foot_font, fill=foot_color, anchor="e")

    def _anim_tick(self):
        """60 FPS Non-blocking Animation Tick for Spinner, Progress, and Status."""
        if not self.is_active:
            return

        elapsed = time.time() - self.start_time
        target_progress = min(1.0, elapsed / self.duration)

        # Smooth exponential lerping
        self.current_progress += (target_progress - self.current_progress) * 0.25
        if abs(target_progress - self.current_progress) < 0.005 and target_progress >= 1.0:
            self.current_progress = 1.0

        # Rotate Spinner Arcs (6 degrees per tick)
        self.spin_angle = (self.spin_angle + 6) % 360
        self.canvas.itemconfigure(self.arc1, start=self.spin_angle)
        self.canvas.itemconfigure(self.arc2, start=(self.spin_angle + 115) % 360)
        self.canvas.itemconfigure(self.arc3, start=(self.spin_angle + 220) % 360)
        self.canvas.itemconfigure(self.arc4, start=(self.spin_angle + 325) % 360)
        self.canvas.itemconfigure(self.arc_inner, start=(-self.spin_angle * 1.5) % 360)

        # Update CTkProgressBar
        self.progress_bar.set(self.current_progress)

        # Update Dynamic Monospace Status
        pct = int(self.current_progress * 100)
        if pct < 20:
            status = "Mendeteksi network adapter fisik & virtual..."
        elif pct < 42:
            status = "Menginisialisasi route metric orchestrator..."
        elif pct < 68:
            status = "Memverifikasi probing target (1.1.1.1, 8.8.8.8, 9.9.9.9)..."
        elif pct < 86:
            status = "Menyiapkan monitoring engine & zero-drop router..."
        elif pct < 98:
            status = "Sinkronisasi konfigurasi Zero-Drop Zoom..."
        else:
            status = "Sistem Siap. Membuka MODULA..."

        self.canvas.itemconfigure(self.status_txt, text=f"[ {pct:3d}% ]  {status}")

        # Check for completion
        if self.current_progress >= 0.999 and elapsed >= self.duration:
            # Hold at 100% for 120ms then start smooth fadeout
            self.after(120, self._start_fadeout)
        else:
            self.after(16, self._anim_tick)

    def _start_fadeout(self):
        """Initiate graceful window alpha fadeout."""
        if self._fading:
            return
        self._fading = True
        self._fade_step(1.0)

    def _fade_step(self, alpha: float):
        """Stepwise opacity decrement."""
        if alpha > 0.05:
            alpha -= 0.12
            try:
                self.attributes("-alpha", max(0.0, alpha))
            except Exception:
                pass
            self.after(20, lambda: self._fade_step(alpha))
        else:
            self._complete()

    def _complete(self):
        """Clean up splash window and invoke completion callback."""
        self.is_active = False
        try:
            self.destroy()
        except Exception:
            pass

        if self.on_finish:
            self.on_finish()

        if self._standalone and self._own_root:
            try:
                self._own_root.destroy()
            except Exception:
                pass

    @classmethod
    def show_standalone(cls, duration: float = 3.0):
        """Helper to run the splash screen in standalone preview mode."""
        root = ctk.CTk()
        root.withdraw()

        def _done():
            root.destroy()

        cls(master=root, on_finish=_done, duration=duration)
        root.mainloop()


if __name__ == "__main__":
    print("[*] Running MODULA Splash Screen in standalone preview mode...")
    SplashScreen.show_standalone(duration=3.0)
