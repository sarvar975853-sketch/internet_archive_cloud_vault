import os
import customtkinter as ctk
from tkinter import filedialog, messagebox
from aegis_vault.gui.theme import THEME
from aegis_vault.gui.hover import apply_bubble_hover

COLOR_INPUT_BG     = THEME['input_bg']
COLOR_CARD_BG      = THEME['card_bg']
COLOR_CARD_BORDER  = THEME['card_border']
COLOR_TEXT_MAIN    = THEME['text_main']
COLOR_TEXT_SUB     = THEME['text_sub']
COLOR_TEXT_ACCENT  = THEME['text_accent']
COLOR_TEXT_DIM     = THEME['text_dim']
COLOR_BTN_PRIMARY  = THEME['primary']
COLOR_BTN_HOVER    = THEME['secondary']
COLOR_PRIMARY      = THEME['primary']
COLOR_SUCCESS      = THEME['success']
COLOR_ERROR        = THEME['error']
COLOR_WARN         = THEME['warning']

PROVIDER_INFO = {
    "google_drive": ("☁️", "Google Drive", "#4285F4"),
    "mediafire":    ("🔥", "Mediafire", "#3364FF"),
    "terabox":      ("📦", "Terabox", "#3DB8FF"),
    "dropbox":      ("📘", "Dropbox", "#0061FF"),
    "onedrive":     ("☁️", "OneDrive", "#0078D4"),
    "mega":         ("🔴", "MEGA", "#D9272E"),
    "megadb":       ("🗃️", "MegaDB", "#FF6B00"),
    "pcloud":       ("💾", "pCloud", "#00A2FF"),
    "wetransfer":   ("✉️", "WeTransfer", "#409FFF"),
    "box":          ("📦", "Box", "#0061D5"),
    "sendspace":    ("🚀", "SendSpace", "#FF6B00"),
    "zippyshare":   ("⚡", "ZippyShare", "#FF6B35"),
    "fourshared":   ("4️⃣", "4shared", "#8CC63F"),
    "direct":       ("🌐", "Direct Link", COLOR_TEXT_SUB),
}


class URLUploadFrame(ctk.CTkFrame):
    def __init__(self, master, queue_worker, storage_engine, crypto_engine):
        super().__init__(master, fg_color="transparent")
        self.queue_worker = queue_worker
        self.storage = storage_engine
        self.crypto = crypto_engine
        self.queued_urls = []
        self._total_urls = 0
        self._completed_urls = 0
        self._no_password = False
        self._download_only = False
        self._save_dir = ""

        self.build_ui()

    def build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 5))

        title = ctk.CTkLabel(
            header,
            text="🔗  URL Transfer",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLOR_TEXT_MAIN,
        )
        title.pack(side="left")

        desc = ctk.CTkLabel(
            header,
            text="Download from Google Drive, Dropbox, Mediafire, MEGA, Terabox, MegaDB & 12+ providers",
            font=ctk.CTkFont(size=12),
            text_color=COLOR_TEXT_SUB,
        )
        desc.pack(side="left", padx=(15, 0))

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
            placeholder_text="Paste URL here... (Google Drive, Dropbox, Mediafire, Terabox, etc.)",
            font=ctk.CTkFont(size=13),
            fg_color=COLOR_INPUT_BG,
            border_color=THEME['border_subtle'],
            border_width=1,
            corner_radius=10,
            text_color=COLOR_TEXT_MAIN,
            placeholder_text_color=COLOR_TEXT_DIM,
        )
        self.url_entry.grid(row=0, column=1, sticky="ew")
        self.url_entry.bind("<FocusIn>", lambda e: self.url_entry.configure(border_color=COLOR_TEXT_ACCENT))
        self.url_entry.bind("<FocusOut>", lambda e: self.url_entry.configure(border_color=THEME['border_subtle']))
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
        apply_bubble_hover(add_btn, glow_color=COLOR_PRIMARY)

        badges_frame = ctk.CTkFrame(self, fg_color="transparent")
        badges_frame.pack(fill="x", padx=25, pady=(2, 6))

        top_providers = ["google_drive", "dropbox", "onedrive", "mediafire", "terabox", "mega", "direct"]
        for key in top_providers:
            if key in PROVIDER_INFO:
                emoji, label, color = PROVIDER_INFO[key]
                badge = ctk.CTkLabel(
                    badges_frame,
                    text=f"{emoji} {label}",
                    font=ctk.CTkFont(size=9),
                    text_color=color,
                    fg_color=THEME['glass_overlay'],
                    corner_radius=6,
                    padx=6,
                    pady=2,
                )
                badge.pack(side="left", padx=(0, 4))

        queue_label = ctk.CTkLabel(
            self,
            text="Queued URLs",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLOR_TEXT_SUB,
        )
        queue_label.pack(anchor="w", padx=22, pady=(5, 2))

        self.queue_frame = ctk.CTkScrollableFrame(
            self,
            height=100,
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
            text_color=COLOR_TEXT_DIM,
            font=ctk.CTkFont(size=12),
        )
        self.empty_lbl.grid(row=0, column=0, pady=20)

        # ── Mode Toggle ─────────────────────────────────────────────────
        mode_card = ctk.CTkFrame(self, fg_color=COLOR_CARD_BG, corner_radius=12,
                                  border_width=1, border_color=COLOR_CARD_BORDER)
        mode_card.pack(fill="x", padx=20, pady=(0, 8))

        mode_inner = ctk.CTkFrame(mode_card, fg_color="transparent")
        mode_inner.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(mode_inner, text="Mode:",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=COLOR_TEXT_MAIN).pack(side="left", padx=(0, 10))

        self._mode_var = ctk.StringVar(value="upload")

        self.upload_mode_rb = ctk.CTkRadioButton(
            mode_inner, text="⬆ Upload to Vault",
            variable=self._mode_var, value="upload",
            command=self._on_mode_change,
            font=ctk.CTkFont(size=11),
            text_color=COLOR_TEXT_MAIN,
            fg_color=COLOR_PRIMARY
        )
        self.upload_mode_rb.pack(side="left", padx=(0, 15))

        self.download_mode_rb = ctk.CTkRadioButton(
            mode_inner, text="📥 Download to Disk",
            variable=self._mode_var, value="download",
            command=self._on_mode_change,
            font=ctk.CTkFont(size=11),
            text_color=COLOR_TEXT_MAIN,
            fg_color=COLOR_PRIMARY
        )
        self.download_mode_rb.pack(side="left")

        # ── Config Area (folder + password or save dir) ──────────────────
        self.config_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.config_frame.pack(fill="x", padx=20, pady=(0, 8))
        self.config_frame.grid_columnconfigure(0, weight=1)
        self.config_frame.grid_columnconfigure(1, weight=1)

        self.bucket_entry = ctk.CTkEntry(
            self.config_frame,
            height=38,
            placeholder_text="Target Folder Name (e.g. my-vault)",
            font=ctk.CTkFont(size=12),
            fg_color=COLOR_INPUT_BG,
            border_color=THEME['border_subtle'],
            border_width=1,
            corner_radius=10,
            text_color=COLOR_TEXT_MAIN,
            placeholder_text_color=COLOR_TEXT_DIM,
        )
        self.bucket_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self.pass_entry = ctk.CTkEntry(
            self.config_frame,
            height=38,
            placeholder_text="Encryption Password (optional for unencrypted)",
            show="•",
            font=ctk.CTkFont(size=12),
            fg_color=COLOR_INPUT_BG,
            border_color=THEME['border_subtle'],
            border_width=1,
            corner_radius=10,
            text_color=COLOR_TEXT_MAIN,
            placeholder_text_color=COLOR_TEXT_DIM,
        )
        self.pass_entry.grid(row=0, column=1, sticky="ew")

        # Save dir row (hidden by default, shown in download mode)
        self.save_dir_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.save_dir_frame.pack(fill="x", padx=20, pady=(0, 8))

        self.save_dir_entry = ctk.CTkEntry(
            self.save_dir_frame,
            height=38,
            placeholder_text="Save location (click Browse to select folder)",
            font=ctk.CTkFont(size=12),
            fg_color=COLOR_INPUT_BG,
            border_color=THEME['border_subtle'],
            border_width=1,
            corner_radius=10,
            text_color=COLOR_TEXT_MAIN,
            placeholder_text_color=COLOR_TEXT_DIM,
            state="disabled"
        )
        self.save_dir_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.browse_btn = ctk.CTkButton(
            self.save_dir_frame,
            text="📁 Browse",
            width=100, height=38,
            corner_radius=10,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=COLOR_BTN_PRIMARY,
            hover_color=COLOR_BTN_HOVER,
            command=self._pick_save_dir
        )
        self.browse_btn.pack(side="right")
        apply_bubble_hover(self.browse_btn, glow_color=COLOR_PRIMARY)

        # Initially hidden
        self.save_dir_frame.pack_forget()

        toggle_frame = ctk.CTkFrame(self, fg_color="transparent")
        toggle_frame.pack(fill="x", padx=20, pady=(0, 8))

        self.no_pass_toggle = ctk.CTkSwitch(
            toggle_frame,
            text="Upload without encryption (unencrypted)",
            font=ctk.CTkFont(size=12),
            text_color=COLOR_TEXT_SUB,
            fg_color=COLOR_CARD_BORDER,
            progress_color=COLOR_PRIMARY,
            button_color=COLOR_TEXT_MAIN,
            button_hover_color=COLOR_TEXT_ACCENT,
            command=self._toggle_password_mode
        )
        self.no_pass_toggle.pack(side="left")

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

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 15))

        self.action_btn = ctk.CTkButton(
            btn_frame,
            text="🔒  Download, Encrypt & Upload All",
            height=44,
            corner_radius=12,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLOR_PRIMARY,
            hover_color=THEME['secondary'],
            command=self.start_action,
        )
        self.action_btn.pack(side="left", expand=True, fill="x", padx=(0, 8))
        apply_bubble_hover(self.action_btn, glow_color=COLOR_PRIMARY)

        clear_btn = ctk.CTkButton(
            btn_frame,
            text="🗑  Clear",
            height=44,
            width=100,
            corner_radius=12,
            font=ctk.CTkFont(size=13),
            fg_color=COLOR_CARD_BG,
            hover_color=THEME['hover_subtle'],
            text_color=COLOR_TEXT_SUB,
            border_width=1,
            border_color=COLOR_CARD_BORDER,
            command=self.clear_queue,
        )
        clear_btn.pack(side="right")
        apply_bubble_hover(clear_btn, glow_color=COLOR_ERROR)

    # ─── Mode Handling ──────────────────────────────────────────────────
    def _on_mode_change(self):
        mode = self._mode_var.get()
        if mode == "download":
            self._download_only = True
            self.save_dir_frame.pack(fill="x", padx=20, pady=(0, 8), after=self.config_frame)
            self.config_frame.pack_forget()
            self.no_pass_toggle.pack_forget()
            self.action_btn.configure(
                text="📥  Download All to Disk",
                fg_color=THEME['success'],
                hover_color=THEME['accent_cyan'],
            )
        else:
            self._download_only = False
            self.save_dir_frame.pack_forget()
            self.config_frame.pack(fill="x", padx=20, pady=(0, 8))
            self.no_pass_toggle.pack(fill="x", padx=20, pady=(0, 8))
            self._toggle_password_mode()

    def _toggle_password_mode(self):
        self._no_password = self.no_pass_toggle.get() == 1
        if self._no_password:
            self.pass_entry.configure(state="disabled", fg_color=THEME['glass_overlay'])
            self.action_btn.configure(text="⬆  Download & Upload (Unencrypted)")
        else:
            self.pass_entry.configure(state="normal", fg_color=COLOR_INPUT_BG)
            self.action_btn.configure(text="🔒  Download, Encrypt & Upload All")

    def _pick_save_dir(self):
        d = filedialog.askdirectory(title="Select download folder")
        if d:
            self._save_dir = d
            self.save_dir_entry.configure(state="normal")
            self.save_dir_entry.delete(0, "end")
            self.save_dir_entry.insert(0, d)
            self.save_dir_entry.configure(state="disabled")

    # ─── URL Management ─────────────────────────────────────────────────
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
                text_color=COLOR_TEXT_DIM,
                font=ctk.CTkFont(size=12),
            )
            self.empty_lbl.grid(row=0, column=0, pady=20)
            return

        for i, url in enumerate(self.queued_urls):
            row = ctk.CTkFrame(self.queue_frame, fg_color="transparent")
            row.grid(row=i, column=0, sticky="ew", pady=2, padx=5)
            row.grid_columnconfigure(1, weight=1)

            from aegis_vault.core.url_downloader import URLDownloader
            provider = URLDownloader._detect_provider(url)
            info = PROVIDER_INFO.get(provider, ("🌐", "Link", COLOR_TEXT_SUB))
            emoji, label, color = info

            badge = ctk.CTkLabel(
                row,
                text=f"{emoji} {label}",
                font=ctk.CTkFont(size=10),
                text_color=color,
                fg_color=THEME['input_bg'],
                corner_radius=4,
                width=90,
            )
            badge.grid(row=0, column=0, padx=(0, 8))

            display_url = url if len(url) <= 65 else url[:62] + "..."
            url_lbl = ctk.CTkLabel(
                row,
                text=display_url,
                font=ctk.CTkFont(size=11),
                text_color=COLOR_TEXT_MAIN,
                anchor="w",
            )
            url_lbl.grid(row=0, column=1, sticky="w")

            remove_btn = ctk.CTkButton(
                row,
                text="✕",
                width=26,
                height=26,
                corner_radius=6,
                font=ctk.CTkFont(size=12),
                fg_color="transparent",
                hover_color=COLOR_ERROR,
                text_color=COLOR_TEXT_DIM,
                command=lambda u=url: self.remove_url(u),
            )
            remove_btn.grid(row=0, column=2, padx=(4, 0))

    # ─── Action Start ───────────────────────────────────────────────────
    def start_action(self):
        if not self.queued_urls:
            messagebox.showerror("Error", "No URLs in the queue. Add at least one URL.")
            return

        if self._download_only:
            self._start_download_only()
        else:
            self._start_upload()

    def _start_download_only(self):
        if not self._save_dir:
            messagebox.showerror("Error", "Select a save folder first.")
            return

        self.action_btn.configure(state="disabled", text="⟳  Downloading...")
        self.progress_bar.set(0)
        self._total_urls = len(self.queued_urls)
        self._completed_urls = 0

        for url in self.queued_urls:
            self.queue_worker.submit_task(
                self._process_download_only, url, self._save_dir
            )

        total = len(self.queued_urls)
        self.queued_urls.clear()
        self._refresh_queue_list()
        self.status_lbl.configure(
            text=f"Downloading {total} file(s) to disk...",
            text_color=COLOR_TEXT_ACCENT,
        )

    def _start_upload(self):
        bucket = self.bucket_entry.get().strip().lower().replace(" ", "-")
        password = self.pass_entry.get()

        if not bucket:
            messagebox.showerror("Error", "Target folder name is required.")
            return
        if not self._no_password and not password:
            messagebox.showerror("Error", "Encryption password is required (or toggle unencrypted).")
            return

        self.action_btn.configure(state="disabled", text="⟳  Processing...")
        self.progress_bar.set(0)
        self._total_urls = len(self.queued_urls)
        self._completed_urls = 0

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

    # ─── Background Tasks ───────────────────────────────────────────────
    def _process_download_only(self, url: str, save_dir: str) -> str:
        from aegis_vault.core.url_downloader import URLDownloader

        downloader = URLDownloader(download_dir=save_dir)
        result = downloader.download(url)

        if not result["success"]:
            raise Exception(f"Download failed: {result['error']}")

        file_path = result["file_path"]
        file_name = result["file_name"]
        file_size = result["file_size"]

        return f"✓ Saved {file_name} ({self._fmt_size(file_size)}) → {save_dir}"

    def _process_url_upload(self, url: str, password: str, bucket: str, no_password: bool) -> str:
        from aegis_vault.core.url_downloader import URLDownloader

        downloader = URLDownloader()
        result = downloader.download(url)

        if not result["success"]:
            raise Exception(f"Download failed: {result['error']}")

        file_path = result["file_path"]
        original_filename = result["file_name"]

        if no_password:
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
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

    # ─── Task Update Handler ────────────────────────────────────────────
    def on_task_update(self, status, result):
        self._completed_urls += 1
        progress = self._completed_urls / max(self._total_urls, 1)
        self.progress_bar.set(progress)

        if status == "success":
            self.status_lbl.configure(text=str(result), text_color=COLOR_SUCCESS)
        elif status == "error":
            self.status_lbl.configure(text=f"❌ {result}", text_color=COLOR_ERROR)

        if self._completed_urls >= self._total_urls:
            mode_text = "downloaded" if self._download_only else "uploaded"
            self.action_btn.configure(
                state="normal",
                text="📥  Download All to Disk" if self._download_only
                     else ("⬆  Download & Upload (Unencrypted)" if self._no_password
                           else "🔒  Download, Encrypt & Upload All")
            )
            if status == "success":
                self.status_lbl.configure(
                    text=f"✓ All {self._total_urls} URL(s) {mode_text} successfully!",
                    text_color=COLOR_SUCCESS
                )
