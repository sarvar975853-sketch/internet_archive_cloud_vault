import os
import customtkinter as ctk
from tkinter import messagebox

# ─── Colors (matching the app theme) ────────────────────────────────────────
COLOR_INPUT_BG     = "#09090B"
COLOR_CARD_BG      = "#18181B"
COLOR_CARD_BORDER  = "#27272A"
COLOR_TEXT_MAIN    = "#F4F4F5"
COLOR_TEXT_SUB     = "#A1A1AA"
COLOR_TEXT_ACCENT  = "#818CF8"
COLOR_TEXT_DIM     = "#52525B"
COLOR_BTN_PRIMARY  = "#4F46E5"
COLOR_BTN_HOVER    = "#6366F1"
COLOR_PRIMARY      = "#6366F1"
COLOR_SUCCESS      = "#22C55E"
COLOR_ERROR        = "#EF4444"
COLOR_WARN         = "#F59E0B"

# Provider badges: (emoji, label, color)
PROVIDER_INFO = {
    "google_drive": ("☁️", "Google Drive", "#4285F4"),
    "mediafire":    ("🔥", "Mediafire", "#3364FF"),
    "terabox":      ("📦", "Terabox", "#3DB8FF"),
    "dropbox":      ("📘", "Dropbox", "#0061FF"),
    "onedrive":     ("☁️", "OneDrive", "#0078D4"),
    "mega":         ("🔴", "MEGA", "#D9272E"),
    "pcloud":       ("💾", "pCloud", "#00A2FF"),
    "wetransfer":   ("✉️", "WeTransfer", "#409FFF"),
    "box":          ("📦", "Box", "#0061D5"),
    "sendspace":    ("🚀", "SendSpace", "#FF6B00"),
    "zippyshare":   ("⚡", "ZippyShare", "#FF6B35"),
    "fourshared":   ("4️⃣", "4shared", "#8CC63F"),
    "direct":       ("🌐", "Direct Link", "#A1A1AA"),
}


def apply_hover_bump(button, base_w, base_h):
    button.bind("<Enter>", lambda event: button.configure(
        width=base_w + 10,
        height=base_h + 3,
        border_width=1,
        border_color="#818CF8"
    ))
    button.bind("<Leave>", lambda event: button.configure(
        width=base_w,
        height=base_h,
        border_width=0
    ))


class URLUploadFrame(ctk.CTkFrame):
    """
    GUI tab for uploading files to the vault from remote URLs.
    Supports Google Drive, Mediafire, Terabox, and direct links.
    Flow: User pastes URL → file downloads to temp → encrypted → uploaded to IA.
    """

    def __init__(self, master, queue_worker, storage_engine, crypto_engine):
        super().__init__(master, fg_color="transparent")
        self.queue_worker = queue_worker
        self.storage = storage_engine
        self.crypto = crypto_engine
        self.queued_urls = []
        self._total_urls = 0
        self._completed_urls = 0
        self._no_password = False

        self.build_ui()

    def build_ui(self):
        # ── Header ───────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 5))

        title = ctk.CTkLabel(
            header,
            text="🔗  Upload from URL",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLOR_TEXT_MAIN,
        )
        title.pack(side="left")

        desc = ctk.CTkLabel(
            header,
            text="Paste any download link — Google Drive, Dropbox, OneDrive, Mediafire, Terabox, and more!",
            font=ctk.CTkFont(size=12),
            text_color=COLOR_TEXT_SUB,
        )
        desc.pack(side="left", padx=(15, 0))

        # ── URL Input Area ───────────────────────────────────────────────
        url_frame = ctk.CTkFrame(
            self,
            fg_color=COLOR_CARD_BG,
            corner_radius=12,
            border_width=1,
            border_color=COLOR_CARD_BORDER,
        )
        url_frame.pack(fill="x", padx=20, pady=(10, 8))

        url_inner = ctk.CTkFrame(url_frame, fg_color="transparent")
        url_inner.pack(fill="x", padx=15, pady=12)
        url_inner.grid_columnconfigure(1, weight=1)

        url_icon = ctk.CTkLabel(
            url_inner, text="🔗", font=ctk.CTkFont(size=20), width=30
        )
        url_icon.grid(row=0, column=0, padx=(0, 8))

        self.url_entry = ctk.CTkEntry(
            url_inner,
            height=42,
            placeholder_text="Paste URL here... (Google Drive, Dropbox, OneDrive, Mediafire, Terabox, and more)",
            font=ctk.CTkFont(size=13),
            fg_color=COLOR_INPUT_BG,
            border_color="#27272A",
            border_width=1,
            corner_radius=10,
            text_color=COLOR_TEXT_MAIN,
            placeholder_text_color="#52525B",
        )
        self.url_entry.grid(row=0, column=1, sticky="ew")
        self.url_entry.bind("<FocusIn>", lambda e: self.url_entry.configure(border_color=COLOR_TEXT_ACCENT))
        self.url_entry.bind("<FocusOut>", lambda e: self.url_entry.configure(border_color="#27272A"))
        self.url_entry.bind("<Return>", lambda e: self.add_url())

        add_btn = ctk.CTkButton(
            url_inner,
            text="＋ Add",
            width=80,
            height=42,
            corner_radius=10,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=COLOR_BTN_PRIMARY,
            hover_color=COLOR_BTN_HOVER,
            command=self.add_url,
        )
        add_btn.grid(row=0, column=2, padx=(8, 0))

        # ── Provider badges row ──────────────────────────────────────────
        ctk.CTkLabel(self, text="✨ Supported Platforms:",
                     font=ctk.CTkFont(size=10, weight="bold"),
                     text_color="#71717A").pack(anchor="w", padx=25, pady=(6, 2))
        
        badges_frame = ctk.CTkFrame(self, fg_color="transparent")
        badges_frame.pack(fill="x", padx=25, pady=(0, 8))

        # Show top 6 most common providers
        top_providers = ["google_drive", "dropbox", "onedrive", "mediafire", "terabox", "direct"]
        for key in top_providers:
            if key in PROVIDER_INFO:
                emoji, label, color = PROVIDER_INFO[key]
                badge = ctk.CTkLabel(
                    badges_frame,
                    text=f"{emoji} {label}",
                    font=ctk.CTkFont(size=10),
                    text_color=color,
                    fg_color="#18181B",
                    corner_radius=6,
                    padx=7,
                    pady=2,
                )
                badge.pack(side="left", padx=(0, 6))

        # ── Queued URLs List ─────────────────────────────────────────────
        queue_label = ctk.CTkLabel(
            self,
            text="Queued URLs",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLOR_TEXT_SUB,
        )
        queue_label.pack(anchor="w", padx=22, pady=(5, 2))

        self.queue_frame = ctk.CTkScrollableFrame(
            self,
            height=130,
            fg_color=COLOR_CARD_BG,
            corner_radius=10,
            border_width=1,
            border_color=COLOR_CARD_BORDER,
        )
        self.queue_frame.pack(fill="both", expand=True, padx=20, pady=(0, 8))
        self.queue_frame.grid_columnconfigure(0, weight=1)

        self.empty_lbl = ctk.CTkLabel(
            self.queue_frame,
            text="No URLs queued yet. Paste a link above and click ＋ Add.",
            text_color="#52525B",
            font=ctk.CTkFont(size=12),
        )
        self.empty_lbl.grid(row=0, column=0, pady=20)

        # ── Target Folder + Password ─────────────────────────────────────
        config_frame = ctk.CTkFrame(self, fg_color="transparent")
        config_frame.pack(fill="x", padx=20, pady=(0, 8))
        config_frame.grid_columnconfigure(0, weight=1)
        config_frame.grid_columnconfigure(1, weight=1)

        self.bucket_entry = ctk.CTkEntry(
            config_frame,
            height=40,
            placeholder_text="Target Folder Name (e.g. my-vault)",
            font=ctk.CTkFont(size=12),
            fg_color=COLOR_INPUT_BG,
            border_color="#27272A",
            border_width=1,
            corner_radius=10,
            text_color=COLOR_TEXT_MAIN,
            placeholder_text_color="#52525B",
        )
        self.bucket_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self.pass_entry = ctk.CTkEntry(
            config_frame,
            height=40,
            placeholder_text="Encryption Password",
            show="•",
            font=ctk.CTkFont(size=12),
            fg_color=COLOR_INPUT_BG,
            border_color="#27272A",
            border_width=1,
            corner_radius=10,
            text_color=COLOR_TEXT_MAIN,
            placeholder_text_color="#52525B",
        )
        self.pass_entry.grid(row=0, column=1, sticky="ew")

        # ── No Password Toggle ───────────────────────────────────────────
        toggle_frame = ctk.CTkFrame(self, fg_color="transparent")
        toggle_frame.pack(fill="x", padx=20, pady=(0, 8))

        self.no_pass_toggle = ctk.CTkSwitch(
            toggle_frame,
            text="Upload without password (unencrypted)",
            font=ctk.CTkFont(size=12),
            text_color=COLOR_TEXT_SUB,
            fg_color=COLOR_CARD_BORDER,
            progress_color=COLOR_PRIMARY,
            button_color=COLOR_TEXT_MAIN,
            button_hover_color=COLOR_TEXT_ACCENT,
            command=self._toggle_password_mode
        )
        self.no_pass_toggle.pack(side="left")

        # ── Progress ─────────────────────────────────────────────────────
        self.progress_bar = ctk.CTkProgressBar(self, height=6, corner_radius=3)
        self.progress_bar.pack(fill="x", padx=20, pady=(4, 2))
        self.progress_bar.set(0)

        self.status_lbl = ctk.CTkLabel(
            self,
            text="Ready",
            font=ctk.CTkFont(size=12),
            text_color=COLOR_TEXT_SUB,
        )
        self.status_lbl.pack(pady=(0, 4))

        # ── Action Buttons ───────────────────────────────────────────────
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 15))

        self.upload_btn = ctk.CTkButton(
            btn_frame,
            text="🔒  Download, Encrypt & Upload All",
            height=44,
            corner_radius=12,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLOR_PRIMARY,
            hover_color="#4F46E5",
            command=self.start_url_upload,
        )
        self.upload_btn.pack(side="left", expand=True, fill="x", padx=(0, 8))
        apply_hover_bump(self.upload_btn, 300, 44)

        clear_btn = ctk.CTkButton(
            btn_frame,
            text="🗑  Clear Queue",
            height=44,
            width=140,
            corner_radius=12,
            font=ctk.CTkFont(size=13),
            fg_color="#3F3F46",
            hover_color="#52525B",
            command=self.clear_queue,
        )
        clear_btn.pack(side="right")
        apply_hover_bump(clear_btn, 140, 44)

    def _toggle_password_mode(self):
        self._no_password = self.no_pass_toggle.get() == 1
        if self._no_password:
            self.pass_entry.configure(state="disabled", fg_color="#18181B")
            self.upload_btn.configure(text="⬆  Download & Upload All (Unencrypted)")
        else:
            self.pass_entry.configure(state="normal", fg_color=COLOR_INPUT_BG)
            self.upload_btn.configure(text="🔒  Download, Encrypt & Upload All")

    # ─── URL Management ──────────────────────────────────────────────────
    def add_url(self):
        url = self.url_entry.get().strip()
        if not url:
            return

        if not url.startswith(("http://", "https://")):
            messagebox.showerror("Invalid URL", "Please enter a valid HTTP/HTTPS URL.")
            return

        if url in self.queued_urls:
            messagebox.showinfo("Duplicate", "This URL is already in the queue.")
            return

        self.queued_urls.append(url)
        self.url_entry.delete(0, "end")
        self._refresh_queue_list()

    def remove_url(self, url: str):
        if url in self.queued_urls:
            self.queued_urls.remove(url)
            self._refresh_queue_list()

    def clear_queue(self):
        self.queued_urls.clear()
        self._refresh_queue_list()
        self.status_lbl.configure(text="Queue cleared.", text_color=COLOR_TEXT_SUB)
        self.progress_bar.set(0)

    def _refresh_queue_list(self):
        for widget in self.queue_frame.winfo_children():
            widget.destroy()

        if not self.queued_urls:
            self.empty_lbl = ctk.CTkLabel(
                self.queue_frame,
                text="No URLs queued yet. Paste a link above and click ＋ Add.",
                text_color="#52525B",
                font=ctk.CTkFont(size=12),
            )
            self.empty_lbl.grid(row=0, column=0, pady=20)
            return

        for i, url in enumerate(self.queued_urls):
            row = ctk.CTkFrame(self.queue_frame, fg_color="transparent")
            row.grid(row=i, column=0, sticky="ew", pady=2, padx=5)
            row.grid_columnconfigure(1, weight=1)

            # Provider badge
            from aegis_vault.core.url_downloader import URLDownloader
            provider = URLDownloader._detect_provider(url)
            info = PROVIDER_INFO.get(provider, ("🌐", "Link", "#A1A1AA"))
            emoji, label, color = info

            badge = ctk.CTkLabel(
                row,
                text=f"{emoji} {label}",
                font=ctk.CTkFont(size=11),
                text_color=color,
                fg_color="#09090B",
                corner_radius=4,
                width=100,
            )
            badge.grid(row=0, column=0, padx=(0, 8))

            # Truncated URL
            display_url = url if len(url) <= 70 else url[:67] + "..."
            url_lbl = ctk.CTkLabel(
                row,
                text=display_url,
                font=ctk.CTkFont(size=12),
                text_color=COLOR_TEXT_MAIN,
                anchor="w",
            )
            url_lbl.grid(row=0, column=1, sticky="w")

            # Remove button
            remove_btn = ctk.CTkButton(
                row,
                text="✕",
                width=28,
                height=28,
                corner_radius=6,
                font=ctk.CTkFont(size=13),
                fg_color="transparent",
                hover_color="#EF4444",
                text_color="#A1A1AA",
                command=lambda u=url: self.remove_url(u),
            )
            remove_btn.grid(row=0, column=2, padx=(5, 0))

    # ─── Upload Pipeline ─────────────────────────────────────────────────
    def start_url_upload(self):
        bucket = self.bucket_entry.get().strip().lower().replace(" ", "-")
        password = self.pass_entry.get()

        if not self.queued_urls:
            messagebox.showerror("Error", "No URLs in the queue. Add at least one URL.")
            return
        if not bucket:
            messagebox.showerror("Error", "Target folder name is required.")
            return
        if not self._no_password and not password:
            messagebox.showerror("Error", "Encryption password is required (or toggle 'Upload without password').")
            return

        self.upload_btn.configure(state="disabled", text="⟳  Processing...")
        self.progress_bar.set(0)
        self._total_urls = len(self.queued_urls)
        self._completed_urls = 0

        # Submit each URL as a separate background task
        for url in self.queued_urls:
            self.queue_worker.submit_task(
                self._process_url_upload, url, password, bucket, self._no_password
            )

        total = len(self.queued_urls)
        self.queued_urls.clear()
        self._refresh_queue_list()
        self.status_lbl.configure(
            text=f"Processing {total} URL(s)...",
            text_color=COLOR_TEXT_ACCENT,
        )

    def _process_url_upload(self, url: str, password: str, bucket: str, no_password: bool) -> str:
        """Background task: download from URL → encrypt → upload to IA."""
        from aegis_vault.core.url_downloader import URLDownloader

        downloader = URLDownloader()

        # Step 1: Download file from URL
        result = downloader.download(url)

        if not result["success"]:
            raise Exception(f"Download failed: {result['error']}")

        file_path = result["file_path"]
        original_filename = result["file_name"]

        if no_password:
            # Upload without encryption
            try:
                ia_url = self.storage.upload_file_raw(file_path, original_filename, bucket)
                return f"✓ Uploaded {original_filename} ({self._fmt_size(result['file_size'])}) → {ia_url}"
            finally:
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except Exception:
                    pass
        else:
            # Encrypt then upload
            temp_encrypted_path = file_path + ".ia_crypt"
            try:
                self.crypto.encrypt_file(file_path, password, temp_encrypted_path)
                ia_url = self.storage.upload_file(
                    temp_encrypted_path, original_filename, bucket
                )
                return f"✓ Uploaded {original_filename} ({self._fmt_size(result['file_size'])}) → {ia_url}"
            finally:
                for path in [file_path, temp_encrypted_path]:
                    try:
                        if os.path.exists(path):
                            os.remove(path)
                    except Exception:
                        pass

    @staticmethod
    def _fmt_size(size_bytes: int) -> str:
        """Human-readable file size."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

    # ─── Task Update Handler ─────────────────────────────────────────────
    def on_task_update(self, status, result):
        self._completed_urls += 1
        progress = self._completed_urls / max(self._total_urls, 1)
        self.progress_bar.set(progress)
        
        if status == "success":
            self.status_lbl.configure(text=str(result), text_color=COLOR_SUCCESS)
        elif status == "error":
            self.status_lbl.configure(text=f"❌ {result}", text_color=COLOR_ERROR)

        if self._completed_urls >= self._total_urls:
            self.upload_btn.configure(
                state="normal", text="🔒  Download, Encrypt & Upload All"
            )
            if status == "success":
                self.status_lbl.configure(
                    text=f"✓ All {self._total_urls} URL(s) processed successfully!",
                    text_color=COLOR_SUCCESS
                )
