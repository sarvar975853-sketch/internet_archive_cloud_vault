"""
OmniFetch — Universal Media Downloader Tab
3-pane CustomTkinter layout: Sidebar | Input Card | Batch Queue

Premium dark-zinc aesthetic matching the Aegis Vault theme.
"""

import os
import customtkinter as ctk
from tkinter import messagebox, filedialog

from aegis_vault.core.media_downloader import (
    MediaDownloader, DownloadTask, DownloadStatus, Platform, detect_platform
)
from aegis_vault.utils.logger import logger
from aegis_vault.gui.theme import THEME


# ─── Color Palette ─────────────────────────────────────────────────────────────

C = {
    "bg":          "#09090B",
    "bg_raised":   "#101012",
    "bg_overlay":  "#18181B",
    "bg_hover":    "#1F1F23",
    "border":      "#27272A",
    "border_soft": "#1C1C20",
    "accent":      "#6366F1",
    "accent_dim":  "#4F46E5",
    "text":        "#FAFAFA",
    "text_sub":    "#A1A1AA",
    "text_dim":    "#52525B",
    "success":     "#22C55E",
    "error":       "#EF4444",
    "warning":     "#F59E0B",
    "red":         "#EF4444",
    "red_dim":     "#991B1B",
    "green":       "#22C55E",
    "green_dim":   "#166534",
    "blue":        "#3B82F6",
    "blue_dim":    "#1E3A5F",
    "youtube":     "#EF4444",
    "instagram":   "#E1306C",
    "spotify":     "#1DB954",
    "music":       "#6366F1",
}

# Platform → (emoji, badge_color)
PLATFORM_BADGES = {
    "youtube":   ("▶", C["youtube"]),
    "instagram": ("◉", C["instagram"]),
    "tiktok":    ("♪", C["text"]),
    "twitter":   ("𝕏", C["text"]),
    "reddit":    ("●", "#FF4500"),
    "twitch":    ("◆", "#9146FF"),
    "spotify":   ("♫", C["spotify"]),
    "jiosaavn":  ("♫", C["music"]),
    "wynk":      ("♫", C["music"]),
    "generic":   ("◎", C["text_dim"]),
}


# ─── Sidebar ───────────────────────────────────────────────────────────────────

class OmniFetchSidebar(ctk.CTkFrame):
    """Left navigation sidebar for OmniFetch."""

    NAV_ITEMS = [
        ("Dashboard",       "dashboard"),
        ("Active Downloads","active"),
        ("Completed",       "completed"),
        ("Settings",        "settings"),
    ]

    def __init__(self, master, on_navigate):
        super().__init__(master, width=200, corner_radius=0, fg_color=C["bg_raised"])
        self.grid_propagate(False)
        self.on_navigate = on_navigate
        self._nav_buttons = {}
        self._active_id = None
        self.build_ui()

    def build_ui(self):
        # ── Logo ─────────────────────────────────────────────────────────
        logo = ctk.CTkFrame(self, fg_color="transparent")
        logo.pack(fill="x", padx=14, pady=(18, 8))

        icon_frame = ctk.CTkFrame(logo, width=32, height=32, corner_radius=8,
                                  fg_color=C["accent"])
        icon_frame.pack(side="left")
        icon_frame.pack_propagate(False)
        ctk.CTkLabel(icon_frame, text="⚡", font=ctk.CTkFont(size=16),
                     text_color="white").place(relx=0.5, rely=0.5, anchor="center")

        text_frame = ctk.CTkFrame(logo, fg_color="transparent")
        text_frame.pack(side="left", padx=(10, 0))
        ctk.CTkLabel(text_frame, text="OMNIFETCH",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=C["text"]).pack(anchor="w")
        ctk.CTkLabel(text_frame, text="MEDIA DOWNLOADER",
                     font=ctk.CTkFont(size=7),
                     text_color=C["text_dim"]).pack(anchor="w")

        # ── Divider ──────────────────────────────────────────────────────
        ctk.CTkFrame(self, height=1, fg_color=C["border"]).pack(
            fill="x", padx=14, pady=(10, 10))

        # ── Nav Items ────────────────────────────────────────────────────
        nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        nav_frame.pack(fill="x", padx=10)

        for label, nav_id in self.NAV_ITEMS:
            btn = ctk.CTkButton(
                nav_frame,
                text=f"  {label}",
                anchor="w",
                height=34,
                corner_radius=8,
                font=ctk.CTkFont(size=12),
                fg_color="transparent",
                text_color=C["text_sub"],
                hover_color=C["bg_hover"],
                command=lambda n=nav_id: self._navigate(n),
            )
            btn.pack(fill="x", pady=1)
            self._nav_buttons[nav_id] = btn

        # ── Engine Status (bottom) ───────────────────────────────────────
        spacer = ctk.CTkFrame(self, fg_color="transparent")
        spacer.pack(fill="both", expand=True)

        status_frame = ctk.CTkFrame(self, fg_color=C["bg_overlay"],
                                     corner_radius=8, border_width=1,
                                     border_color=C["border"])
        status_frame.pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkLabel(status_frame, text="ENGINE STATUS",
                     font=ctk.CTkFont(size=8, weight="bold"),
                     text_color=C["text_dim"]).pack(anchor="w", padx=10, pady=(8, 4))

        self._status_labels = {}
        for name in ["yt-dlp", "FFmpeg", "aria2c"]:
            row = ctk.CTkFrame(status_frame, fg_color="transparent")
            row.pack(fill="x", padx=10, pady=1)
            ctk.CTkLabel(row, text=name, font=ctk.CTkFont(size=10),
                         text_color=C["text_sub"]).pack(side="left")
            lbl = ctk.CTkLabel(row, text="●", font=ctk.CTkFont(size=10),
                               text_color=C["text_dim"])
            lbl.pack(side="right")
            self._status_labels[name] = lbl

    def _navigate(self, nav_id):
        if self._active_id == nav_id:
            return
        self._active_id = nav_id
        for nid, btn in self._nav_buttons.items():
            if nid == nav_id:
                btn.configure(fg_color=C["blue_dim"], text_color=C["text"])
            else:
                btn.configure(fg_color="transparent", text_color=C["text_sub"])
        self.on_navigate(nav_id)

    def update_engine_status(self, status: dict):
        mapping = {
            "yt-dlp": status.get("yt_dlp", False),
            "FFmpeg": status.get("ffmpeg", False),
            "aria2c": status.get("aria2c", False),
        }
        for name, available in mapping.items():
            lbl = self._status_labels.get(name)
            if lbl:
                lbl.configure(text_color=C["green"] if available else C["red"])


# ─── Main Input Panel ──────────────────────────────────────────────────────────

class OmniFetchInput(ctk.CTkFrame):
    """URL input card with format/quality selectors and download button."""

    def __init__(self, master, on_submit, on_browse):
        super().__init__(master, fg_color=C["bg_overlay"],
                         corner_radius=12, border_width=1,
                         border_color=C["border"])
        self.on_submit = on_submit
        self.on_browse = on_browse
        self._detected_platform = None
        self.build_ui()

    def build_ui(self):
        # ── Header ───────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(14, 4))

        ctk.CTkLabel(header, text="New Download",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=C["text"]).pack(side="left")
        ctk.CTkLabel(header, text="Paste a URL to begin",
                     font=ctk.CTkFont(size=11),
                     text_color=C["text_dim"]).pack(side="left", padx=(10, 0))

        # ── URL Input Row ────────────────────────────────────────────────
        url_frame = ctk.CTkFrame(self, fg_color="transparent")
        url_frame.pack(fill="x", padx=16, pady=(8, 4))
        url_frame.grid_columnconfigure(1, weight=1)

        self.url_icon = ctk.CTkLabel(url_frame, text="◎",
                                     font=ctk.CTkFont(size=18),
                                     text_color=C["text_dim"], width=28)
        self.url_icon.grid(row=0, column=0, padx=(0, 6))

        self.url_entry = ctk.CTkEntry(
            url_frame,
            height=44,
            placeholder_text="Paste YouTube, Instagram, Spotify URL...",
            font=ctk.CTkFont(size=13),
            fg_color=C["bg"],
            border_color=C["border"],
            border_width=1,
            corner_radius=10,
            text_color=C["text"],
            placeholder_text_color=C["text_dim"],
        )
        self.url_entry.grid(row=0, column=1, sticky="ew")
        self.url_entry.bind("<Return>", lambda e: self._submit())
        self.url_entry.bind("<KeyRelease>", self._on_url_change)

        self.platform_badge = ctk.CTkLabel(
            url_frame, text="", font=ctk.CTkFont(size=9, weight="bold"),
            fg_color=C["bg"], corner_radius=6, padx=6, pady=2)
        self.platform_badge.grid(row=0, column=2, padx=(8, 0))

        # ── Selectors Row ────────────────────────────────────────────────
        selectors = ctk.CTkFrame(self, fg_color="transparent")
        selectors.pack(fill="x", padx=16, pady=(6, 4))
        selectors.grid_columnconfigure(0, weight=1)
        selectors.grid_columnconfigure(1, weight=1)
        selectors.grid_columnconfigure(2, weight=1)
        selectors.grid_columnconfigure(3, weight=0)

        # Format
        ctk.CTkLabel(selectors, text="FORMAT",
                     font=ctk.CTkFont(size=9, weight="bold"),
                     text_color=C["text_dim"]).grid(row=0, column=0, sticky="w", padx=(0, 4))
        self.format_var = ctk.StringVar(value="best")
        self.format_menu = ctk.CTkOptionMenu(
            selectors, variable=self.format_var,
            values=["best", "mp4", "mkv", "webm", "mp3", "flac", "wav", "m4a", "opus"],
            height=36, corner_radius=8,
            font=ctk.CTkFont(size=11),
            fg_color=C["bg"],
            button_color=C["border"],
            button_hover_color=C["bg_hover"],
            dropdown_fg_color=C["bg_overlay"],
            dropdown_hover_color=C["blue_dim"],
        )
        self.format_menu.grid(row=1, column=0, sticky="ew", padx=(0, 8))

        # Quality
        ctk.CTkLabel(selectors, text="QUALITY",
                     font=ctk.CTkFont(size=9, weight="bold"),
                     text_color=C["text_dim"]).grid(row=0, column=1, sticky="w", padx=(0, 4))
        self.quality_var = ctk.StringVar(value="best")
        self.quality_menu = ctk.CTkOptionMenu(
            selectors, variable=self.quality_var,
            values=["best", "2160p", "1080p", "720p", "480p", "audio-only"],
            height=36, corner_radius=8,
            font=ctk.CTkFont(size=11),
            fg_color=C["bg"],
            button_color=C["border"],
            button_hover_color=C["bg_hover"],
            dropdown_fg_color=C["bg_overlay"],
            dropdown_hover_color=C["blue_dim"],
        )
        self.quality_menu.grid(row=1, column=1, sticky="ew", padx=(0, 8))

        # Destination
        ctk.CTkLabel(selectors, text="DESTINATION",
                     font=ctk.CTkFont(size=9, weight="bold"),
                     text_color=C["text_dim"]).grid(row=0, column=2, sticky="w", padx=(0, 4))
        self.path_var = ctk.StringVar(value=os.path.expanduser("~/Downloads/OmniFetch"))
        path_frame = ctk.CTkFrame(selectors, fg_color="transparent")
        path_frame.grid(row=1, column=2, sticky="ew", padx=(0, 8))
        path_frame.grid_columnconfigure(0, weight=1)

        self.path_entry = ctk.CTkEntry(
            path_frame, height=36,
            font=ctk.CTkFont(size=11),
            fg_color=C["bg"],
            border_color=C["border"],
            corner_radius=8,
            text_color=C["text_sub"],
        )
        self.path_entry.grid(row=0, column=0, sticky="ew")
        self.path_entry.insert(0, self.path_var.get())

        browse_btn = ctk.CTkButton(
            path_frame, text="...", width=32, height=36,
            corner_radius=8, font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=C["border"], hover_color=C["bg_hover"],
            command=lambda: self.on_browse(self.path_entry),
        )
        browse_btn.grid(row=0, column=1, padx=(4, 0))

        # Download Button
        self.download_btn = ctk.CTkButton(
            selectors, text="⬇  Fetch", height=36, width=100,
            corner_radius=8, font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=C["accent"], hover_color=C["accent_dim"],
            command=self._submit,
        )
        self.download_btn.grid(row=1, column=3, padx=(8, 0))

        # ── Error Label ──────────────────────────────────────────────────
        self.error_lbl = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=10),
                                      text_color=C["error"])
        self.error_lbl.pack(anchor="w", padx=16, pady=(2, 6))

    def _on_url_change(self, event=None):
        url = self.url_entry.get().strip()
        platform = detect_platform(url) if url.startswith("http") else None

        if platform and platform != Platform.GENERIC:
            emoji, color = PLATFORM_BADGES.get(platform.value, ("◎", C["text_dim"]))
            self.platform_badge.configure(text=f" {platform.value.upper()} ",
                                          fg_color=C["bg_overlay"], text_color=color)
            self.url_icon.configure(text=emoji, text_color=color)
        else:
            self.platform_badge.configure(text="")
            self.url_icon.configure(text="◎", text_color=C["text_dim"])

    def _submit(self):
        url = self.url_entry.get().strip()
        if not url:
            self.error_lbl.configure(text="Please enter a URL")
            return
        if not url.startswith(("http://", "https://")):
            self.error_lbl.configure(text="URL must start with http:// or https://")
            return
        self.error_lbl.configure(text="")
        self.on_submit(
            url=url,
            quality=self.quality_var.get(),
            fmt=self.format_var.get(),
            path=self.path_entry.get().strip() or self.path_var.get(),
        )
        self.url_entry.delete(0, "end")
        self.platform_badge.configure(text="")
        self.url_icon.configure(text="◎", text_color=C["text_dim"])

    def set_busy(self, busy: bool):
        if busy:
            self.download_btn.configure(state="disabled", text="⟳  Parsing...")
        else:
            self.download_btn.configure(state="normal", text="⬇  Fetch")


# ─── Batch Queue Table ─────────────────────────────────────────────────────────

class OmniFetchQueue(ctk.CTkFrame):
    """Scrollable queue table showing active/completed downloads."""

    STATUS_COLORS = {
        DownloadStatus.QUEUED:      C["text_dim"],
        DownloadStatus.EXTRACTING:  C["warning"],
        DownloadStatus.DOWNLOADING: C["accent"],
        DownloadStatus.PROCESSING:  C["warning"],
        DownloadStatus.COMPLETED:   C["green"],
        DownloadStatus.ERROR:       C["red"],
        DownloadStatus.CANCELLED:   C["text_dim"],
    }

    def __init__(self, master, on_cancel, on_pause):
        super().__init__(master, fg_color=C["bg_overlay"],
                         corner_radius=12, border_width=1,
                         border_color=C["border"])
        self.on_cancel = on_cancel
        self.on_pause = on_pause
        self._rows: dict[str, ctk.CTkFrame] = {}
        self.build_ui()

    def build_ui(self):
        # ── Header ───────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(12, 4))

        ctk.CTkLabel(header, text="Download Queue",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=C["text"]).pack(side="left")

        self.count_lbl = ctk.CTkLabel(header, text="0 items",
                                      font=ctk.CTkFont(size=11),
                                      text_color=C["text_dim"])
        self.count_lbl.pack(side="right")

        # ── Column Headers ───────────────────────────────────────────────
        cols = ctk.CTkFrame(self, fg_color="transparent")
        cols.pack(fill="x", padx=16, pady=(4, 2))
        headers = [("Media", 3), ("Status", 1), ("Progress", 2),
                   ("Speed", 1), ("ETA", 1), ("Size", 1), ("", 0)]
        for text, weight in headers:
            ctk.CTkLabel(cols, text=text, width=0,
                         font=ctk.CTkFont(size=9, weight="bold"),
                         text_color=C["text_dim"]).grid(
                row=0, column=headers.index((text, weight)),
                sticky="w" if text else "e", padx=(0, 8))

        # ── Scrollable Content ───────────────────────────────────────────
        self.scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=C["border"],
            scrollbar_button_hover_color=C["bg_hover"],
        )
        self.scroll.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.scroll.grid_columnconfigure(0, weight=1)

        # Empty state
        self.empty_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.empty_frame.grid(row=0, column=0, pady=40)
        ctk.CTkLabel(self.empty_frame, text="No downloads yet",
                     font=ctk.CTkFont(size=13),
                     text_color=C["text_sub"]).pack()
        ctk.CTkLabel(self.empty_frame, text="Paste a URL above to start",
                     font=ctk.CTkFont(size=11),
                     text_color=C["text_dim"]).pack(pady=(4, 0))

    def update_task(self, task: DownloadTask):
        """Add or update a task row in the queue."""
        if task.id not in self._rows:
            self._create_row(task)
        self._update_row(task)
        self._update_count()

    def _create_row(self, task: DownloadTask):
        """Create a new row for a task."""
        # Remove empty state
        if self.empty_frame.winfo_exists():
            self.empty_frame.destroy()

        row = ctk.CTkFrame(self.scroll, fg_color=C["bg"],
                           corner_radius=8, border_width=1,
                           border_color=C["border_soft"])
        row.grid(row=len(self._rows), column=0, sticky="ew", pady=2, padx=4)
        row.grid_columnconfigure(1, weight=1)

        # Platform icon
        badge = PLATFORM_BADGES.get(task.platform.value, ("◎", C["text_dim"]))
        icon_lbl = ctk.CTkLabel(row, text=badge[0], font=ctk.CTkFont(size=14),
                                text_color=badge[1], width=28)
        icon_lbl.grid(row=0, column=0, rowspan=2, padx=(8, 4), pady=6)

        # Title
        title_lbl = ctk.CTkLabel(row, text=task.title[:50],
                                 font=ctk.CTkFont(size=11, weight="bold"),
                                 text_color=C["text"], anchor="w")
        title_lbl.grid(row=0, column=1, sticky="sw", padx=(0, 8))

        # Subtitle (quality + format)
        sub_lbl = ctk.CTkLabel(row, text=f"{task.quality} · {task.format.upper()}",
                               font=ctk.CTkFont(size=9),
                               text_color=C["text_dim"], anchor="w")
        sub_lbl.grid(row=1, column=1, sticky="nw", padx=(0, 8))

        # Progress bar
        progress_frame = ctk.CTkFrame(row, fg_color="transparent", width=140)
        progress_frame.grid(row=0, column=2, rowspan=2, padx=8, pady=8)
        progress_frame.grid_propagate(False)

        progress_bar = ctk.CTkProgressBar(progress_frame, height=6,
                                          corner_radius=3, progress_color=C["accent"])
        progress_bar.pack(fill="x", pady=(6, 2))
        progress_bar.set(0)

        pct_lbl = ctk.CTkLabel(progress_frame, text="0%",
                               font=ctk.CTkFont(size=9),
                               text_color=C["text_dim"])
        pct_lbl.pack(anchor="e")

        # Speed
        speed_lbl = ctk.CTkLabel(row, text="--",
                                 font=ctk.CTkFont(size=10),
                                 text_color=C["text_sub"], width=80)
        speed_lbl.grid(row=0, column=3, rowspan=2, padx=8, pady=8)

        # ETA
        eta_lbl = ctk.CTkLabel(row, text="--",
                               font=ctk.CTkFont(size=10),
                               text_color=C["text_sub"], width=60)
        eta_lbl.grid(row=0, column=4, rowspan=2, padx=8, pady=8)

        # Size
        size_lbl = ctk.CTkLabel(row, text="--",
                                font=ctk.CTkFont(size=10),
                                text_color=C["text_sub"], width=80)
        size_lbl.grid(row=0, column=5, rowspan=2, padx=8, pady=8)

        # Status badge
        status_lbl = ctk.CTkLabel(row, text="Queued",
                                  font=ctk.CTkFont(size=9, weight="bold"),
                                  fg_color=C["bg_overlay"], corner_radius=6,
                                  padx=6, pady=2)
        status_lbl.grid(row=0, column=6, rowspan=2, padx=(0, 4), pady=8)

        # Action buttons
        btn_frame = ctk.CTkFrame(row, fg_color="transparent", width=60)
        btn_frame.grid(row=0, column=7, rowspan=2, padx=(0, 8), pady=4)
        btn_frame.grid_propagate(False)

        pause_btn = ctk.CTkButton(
            btn_frame, text="⏸", width=26, height=26,
            corner_radius=6, font=ctk.CTkFont(size=11),
            fg_color="transparent", hover_color=C["bg_hover"],
            text_color=C["text_dim"],
            command=lambda t=task: self.on_pause(t.id))
        pause_btn.pack(side="left", padx=1)

        cancel_btn = ctk.CTkButton(
            btn_frame, text="✕", width=26, height=26,
            corner_radius=6, font=ctk.CTkFont(size=11),
            fg_color="transparent", hover_color=C["red_dim"],
            text_color=C["text_dim"],
            command=lambda t=task: self.on_cancel(t.id))
        cancel_btn.pack(side="left", padx=1)

        # Store references
        self._rows[task.id] = {
            "frame": row,
            "title": title_lbl,
            "sub": sub_lbl,
            "progress": progress_bar,
            "pct": pct_lbl,
            "speed": speed_lbl,
            "eta": eta_lbl,
            "size": size_lbl,
            "status": status_lbl,
            "icon": icon_lbl,
        }

    def _update_row(self, task: DownloadTask):
        """Update an existing row with task data."""
        refs = self._rows.get(task.id)
        if not refs:
            return

        refs["title"].configure(text=task.title[:50])
        refs["sub"].configure(text=f"{task.quality} · {task.format.upper()}")
        refs["progress"].set(task.progress / 100.0)
        refs["pct"].configure(text=f"{task.progress:.0f}%")
        refs["speed"].configure(text=task.speed)
        refs["eta"].configure(text=task.eta)
        refs["size"].configure(text=task.total_size if task.total_size != "--" else task.downloaded)

        # Status color
        color = self.STATUS_COLORS.get(task.status, C["text_dim"])
        refs["status"].configure(
            text=task.status.value.replace("_", " ").title(),
            text_color=color,
            fg_color=C["bg_overlay"],
        )

        # Progress bar color
        if task.status == DownloadStatus.COMPLETED:
            refs["progress"].configure(progress_color=C["green"])
        elif task.status == DownloadStatus.ERROR:
            refs["progress"].configure(progress_color=C["red"])
        elif task.status == DownloadStatus.DOWNLOADING:
            refs["progress"].configure(progress_color=C["accent"])
        else:
            refs["progress"].configure(progress_color=C["accent"])

        # Final size on completion
        if task.status == DownloadStatus.COMPLETED and task.output_path:
            try:
                size = os.path.getsize(task.output_path)
                refs["size"].configure(text=self._fmt_size(size))
            except OSError:
                pass

    def remove_task(self, task_id: str):
        """Remove a task row from the queue."""
        refs = self._rows.pop(task_id, None)
        if refs:
            refs["frame"].destroy()
        self._update_count()
        if not self._rows:
            self._show_empty()

    def _update_count(self):
        self.count_lbl.configure(text=f"{len(self._rows)} items")

    def _show_empty(self):
        if not self.empty_frame.winfo_exists():
            self.empty_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
            self.empty_frame.grid(row=0, column=0, pady=40)
            ctk.CTkLabel(self.empty_frame, text="No downloads yet",
                         font=ctk.CTkFont(size=13),
                         text_color=C["text_sub"]).pack()
            ctk.CTkLabel(self.empty_frame, text="Paste a URL above to start",
                         font=ctk.CTkFont(size=11),
                         text_color=C["text_dim"]).pack(pady=(4, 0))

    @staticmethod
    def _fmt_size(size: int) -> str:
        for unit in ("B", "KB", "MB", "GB"):
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.2f} TB"


# ─── Settings Panel ────────────────────────────────────────────────────────────

class OmniFetchSettings(ctk.CTkFrame):
    """Settings panel for engine configuration."""

    def __init__(self, master, downloader: MediaDownloader):
        super().__init__(master, fg_color="transparent")
        self.downloader = downloader
        self.build_ui()

    def build_ui(self):
        ctk.CTkLabel(self, text="Settings",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=C["text"]).pack(anchor="w", padx=4, pady=(0, 12))

        # ── Engine Status Card ───────────────────────────────────────────
        card = ctk.CTkFrame(self, fg_color=C["bg_overlay"],
                            corner_radius=12, border_width=1,
                            border_color=C["border"])
        card.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(card, text="ENGINE STATUS",
                     font=ctk.CTkFont(size=9, weight="bold"),
                     text_color=C["text_dim"]).pack(anchor="w", padx=16, pady=(12, 8))

        status = self.downloader.get_engine_status()
        for name, available in status.items():
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=2)
            display_name = name.replace("_", "-").upper()
            ctk.CTkLabel(row, text=display_name, font=ctk.CTkFont(size=12),
                         text_color=C["text"]).pack(side="left")
            color = C["green"] if available else C["red"]
            text = "Installed" if available else "Not found"
            ctk.CTkLabel(row, text=text, font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=color).pack(side="right")

        # ── Configuration Card ───────────────────────────────────────────
        config_card = ctk.CTkFrame(self, fg_color=C["bg_overlay"],
                                   corner_radius=12, border_width=1,
                                   border_color=C["border"])
        config_card.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(config_card, text="DOWNLOAD CONFIGURATION",
                     font=ctk.CTkFont(size=9, weight="bold"),
                     text_color=C["text_dim"]).pack(anchor="w", padx=16, pady=(12, 8))

        # Max concurrent
        row1 = ctk.CTkFrame(config_card, fg_color="transparent")
        row1.pack(fill="x", padx=16, pady=4)
        ctk.CTkLabel(row1, text="Max Concurrent Downloads",
                     font=ctk.CTkFont(size=12),
                     text_color=C["text"]).pack(side="left")
        self.concurrent_var = ctk.StringVar(value=str(self.downloader.max_concurrent))
        ctk.CTkOptionMenu(row1, variable=self.concurrent_var,
                          values=["1", "2", "3", "4", "6", "8", "10"],
                          width=80, height=30, corner_radius=6,
                          font=ctk.CTkFont(size=11),
                          fg_color=C["bg"],
                          button_color=C["border"]).pack(side="right")

        # aria2c chunks
        row2 = ctk.CTkFrame(config_card, fg_color="transparent")
        row2.pack(fill="x", padx=16, pady=4)
        ctk.CTkLabel(row2, text="aria2c Download Chunks",
                     font=ctk.CTkFont(size=12),
                     text_color=C["text"]).pack(side="left")
        self.chunks_var = ctk.StringVar(value=str(self.downloader.aria2_chunks))
        ctk.CTkOptionMenu(row2, variable=self.chunks_var,
                          values=["1", "4", "8", "12", "16"],
                          width=80, height=30, corner_radius=6,
                          font=ctk.CTkFont(size=11),
                          fg_color=C["bg"],
                          button_color=C["border"]).pack(side="right")

        # Download dir
        row3 = ctk.CTkFrame(config_card, fg_color="transparent")
        row3.pack(fill="x", padx=16, pady=(4, 12))
        ctk.CTkLabel(row3, text="Default Download Directory",
                     font=ctk.CTkFont(size=12),
                     text_color=C["text"]).pack(side="left")
        ctk.CTkLabel(row3, text=self.downloader.download_dir,
                     font=ctk.CTkFont(size=10),
                     text_color=C["text_dim"]).pack(side="right")


# ─── Main OmniFetch Tab ────────────────────────────────────────────────────────

class OmniFetchTab(ctk.CTkFrame):
    """
    Complete OmniFetch media downloader tab.
    3-pane layout: Sidebar | Main Content (Input + Queue)
    """

    def __init__(self, master, queue_worker):
        super().__init__(master, fg_color=C["bg"])
        self.queue_worker = queue_worker

        # Create engine
        self.downloader = MediaDownloader(
            download_dir=os.path.expanduser("~/Downloads/OmniFetch"),
            progress_callback=self._on_progress,
        )

        self._current_view = "dashboard"
        self.build_ui()

        # Check engine status on load
        self.after(200, self._check_engines)

    def build_ui(self):
        self.grid_columnconfigure(0, weight=0)  # sidebar
        self.grid_columnconfigure(1, weight=1)  # main
        self.grid_rowconfigure(0, weight=1)

        # ── Sidebar ──────────────────────────────────────────────────────
        self.sidebar = OmniFetchSidebar(self, on_navigate=self._navigate)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        # ── Main Content ─────────────────────────────────────────────────
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.grid(row=0, column=1, sticky="nsew", padx=(1, 0))
        main.grid_rowconfigure(1, weight=1)
        main.grid_columnconfigure(0, weight=1)

        # Input card (always visible at top)
        self.input_card = OmniFetchInput(main, on_submit=self._submit_url,
                                         on_browse=self._browse_folder)
        self.input_card.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 6))

        # Content area (switches between views)
        self.content_frame = ctk.CTkFrame(main, fg_color="transparent")
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)

        # Queue (always present)
        self.queue = OmniFetchQueue(self.content_frame,
                                    on_cancel=self._cancel_download,
                                    on_pause=self._pause_download)
        self.queue.grid(row=0, column=0, sticky="nsew")

        # Settings (hidden by default)
        self.settings = OmniFetchSettings(self.content_frame, self.downloader)

        # Status bar
        self.status_bar = ctk.CTkFrame(main, fg_color="transparent", height=28)
        self.status_bar.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 8))
        self.status_lbl = ctk.CTkLabel(self.status_bar, text="Ready",
                                       font=ctk.CTkFont(size=10),
                                       text_color=C["text_dim"])
        self.status_lbl.pack(side="left")

    # ─── Navigation ──────────────────────────────────────────────────────────

    def _navigate(self, view_id):
        self._current_view = view_id

        if view_id == "settings":
            self.queue.grid_forget()
            self.settings.grid(row=0, column=0, sticky="nsew")
        else:
            self.settings.grid_forget()
            self.queue.grid(row=0, column=0, sticky="nsew")

    # ─── URL Submission ─────────────────────────────────────────────────────

    def _submit_url(self, url: str, quality: str, fmt: str, path: str):
        """Submit a URL for download via the queue worker."""
        self.input_card.set_busy(True)
        os.makedirs(path, exist_ok=True)

        # Submit to background queue
        self.queue_worker.submit_task(
            self._extract_and_enqueue, url, quality, fmt, path,
            task_name="omnifetch_extract"
        )

    def _extract_and_enqueue(self, url: str, quality: str, fmt: str, path: str):
        """Background: extract info then submit the download task."""
        task = self.downloader.submit(url, quality=quality, fmt=fmt, output_dir=path)
        # Extract info (blocking, runs in worker thread)
        info = self.downloader.extract_info(url)
        if info.get("success"):
            self.downloader.update_task(task.id,
                                        title=info.get("title", url),
                                        formats=info.get("formats", []))
        return {"action": "omnifetch_extracted", "task_id": task.id}

    def _on_task_done(self, status, result):
        """Handle queue worker callback."""
        if status == "success" and isinstance(result, dict):
            action = result.get("action")
            if action == "omnifetch_extracted":
                task_id = result.get("task_id")
                task = self.downloader.get_task(task_id)
                if task:
                    self.input_card.set_busy(False)
                    self.queue.update_task(task)
                    # Start the actual download in background
                    self.downloader.start_task(task_id)

    def _browse_folder(self, path_entry):
        """Open folder browser dialog."""
        path = filedialog.askdirectory()
        if path:
            path_entry.delete(0, "end")
            path_entry.insert(0, path)

    # ─── Progress ───────────────────────────────────────────────────────────

    def _on_progress(self, task: DownloadTask):
        """Called by engine on every progress update. Runs in engine thread."""
        self.after(0, self._sync_progress, task)

    def _sync_progress(self, task: DownloadTask):
        """Update UI on main thread."""
        self.queue.update_task(task)

        if task.status == DownloadStatus.DOWNLOADING:
            self.status_lbl.configure(
                text=f"Downloading: {task.title[:40]} — {task.speed}",
                text_color=C["accent"])
        elif task.status == DownloadStatus.COMPLETED:
            self.status_lbl.configure(
                text=f"✓ Completed: {task.title[:40]}",
                text_color=C["green"])
        elif task.status == DownloadStatus.ERROR:
            self.status_lbl.configure(
                text=f"✕ Error: {task.error[:50]}",
                text_color=C["red"])
        elif task.status == DownloadStatus.EXTRACTING:
            self.status_lbl.configure(
                text=f"Extracting: {task.url[:50]}",
                text_color=C["warning"])

    # ─── Actions ────────────────────────────────────────────────────────────

    def _cancel_download(self, task_id):
        self.downloader.cancel_task(task_id)
        task = self.downloader.get_task(task_id)
        if task:
            self.queue.update_task(task)

    def _pause_download(self, task_id):
        task = self.downloader.get_task(task_id)
        if task:
            if task.status == DownloadStatus.PAUSED:
                self.downloader.start_task(task_id)
            else:
                self.downloader.update_task(task_id, status=DownloadStatus.PAUSED)
                self.queue.update_task(task)

    # ─── Engine Check ───────────────────────────────────────────────────────

    def _check_engines(self):
        status = self.downloader.get_engine_status()
        self.sidebar.update_engine_status(status)

        missing = [k for k, v in status.items() if not v]
        if missing:
            names = ", ".join(m.replace("_", "-") for m in missing)
            self.status_lbl.configure(
                text=f"⚠ Missing engines: {names}",
                text_color=C["warning"])
