import customtkinter as ctk
import threading
import time
from aegis_vault.utils.logger import logger
from aegis_vault.gui.theme import THEME
from aegis_vault.gui.hover import apply_bubble_hover

COLOR_BG           = THEME['main_bg']
COLOR_CARD_BG      = THEME['card_bg']
COLOR_CARD_BORDER  = THEME['card_border']
COLOR_INPUT_BG     = THEME['input_bg']
COLOR_TEXT_MAIN    = THEME['text_main']
COLOR_TEXT_SUB     = THEME['text_sub']
COLOR_TEXT_ACCENT  = THEME['text_accent']
COLOR_TEXT_DIM     = THEME['text_dim']
COLOR_SUCCESS      = THEME['success']
COLOR_WARN         = THEME['warning']
COLOR_ERROR        = THEME['error']
COLOR_PRIMARY      = THEME['primary']


class DashboardFrame(ctk.CTkFrame):
    def __init__(self, master, on_navigate=None, storage_engine=None):
        super().__init__(master, fg_color="transparent")
        self.on_navigate = on_navigate
        self.storage_engine = storage_engine
        self._stat_vars = {}
        self.build_ui()
        self.after(300, self._load_stats_background)

    def build_ui(self):
        self.scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=THEME['card_border'],
            scrollbar_button_hover_color=THEME['hover'],
        )
        self.scroll.pack(fill="both", expand=True)

        banner = ctk.CTkFrame(self.scroll, fg_color=COLOR_CARD_BG,
                               corner_radius=14, border_width=1,
                               border_color=COLOR_CARD_BORDER)
        banner.pack(fill="x", padx=2, pady=(2, 10))

        banner_content = ctk.CTkFrame(banner, fg_color="transparent")
        banner_content.pack(fill="x", padx=22, pady=18)

        ctk.CTkLabel(banner_content, text="Aegis Vault",
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=COLOR_TEXT_MAIN).pack(anchor="w")
        ctk.CTkLabel(banner_content,
                     text="Zero-knowledge encrypted cloud storage with Internet Archive.",
                     font=ctk.CTkFont(size=12),
                     text_color=COLOR_TEXT_SUB).pack(anchor="w", pady=(4, 0))

        tags_frame = ctk.CTkFrame(banner_content, fg_color="transparent")
        tags_frame.pack(anchor="w", pady=(8, 0))
        features = [
            ("AES-256 Encryption", THEME['glass_overlay'], THEME['primary']),
            ("Zero-Knowledge", THEME['glass_overlay'], THEME['secondary']),
            ("6 Concurrent Workers", THEME['glass_overlay'], THEME['success']),
        ]
        for text, bg, fg in features:
            tag = ctk.CTkLabel(tags_frame, text=text,
                               font=ctk.CTkFont(size=9, weight="bold"),
                               text_color=fg, fg_color=bg,
                               corner_radius=6, padx=8, pady=3)
            tag.pack(side="left", padx=(0, 6))

        cards_row = ctk.CTkFrame(self.scroll, fg_color="transparent")
        cards_row.pack(fill="x", padx=2, pady=(0, 10))
        cards_row.grid_columnconfigure((0, 1, 2, 3), weight=1)

        stat_defs = [
            ("FOLDERS", "folders", "—", "Scanning...", "📁", THEME['primary']),
            ("FILES",   "files",   "—", "Encrypted",   "📄", THEME['success']),
            ("STORAGE", "storage", "—", "Total used",  "💾", THEME['secondary']),
        ]

        for col, (header, key, default_val, default_sub, icon, icon_color) in enumerate(stat_defs):
            val_var = ctk.StringVar(value=default_val)
            sub_var = ctk.StringVar(value=default_sub)
            self._stat_vars[key] = (val_var, sub_var)

            card = ctk.CTkFrame(cards_row, fg_color=COLOR_CARD_BG,
                                 corner_radius=12, border_width=1,
                                 border_color=COLOR_CARD_BORDER)
            card.grid(row=0, column=col, sticky="nsew", padx=(0, 8) if col < 3 else 0)

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="both", expand=True, padx=14, pady=12)

            ctk.CTkLabel(inner, text=header,
                         font=ctk.CTkFont(size=9, weight="bold"),
                         text_color=COLOR_TEXT_SUB).pack(anchor="w")

            val_row = ctk.CTkFrame(inner, fg_color="transparent")
            val_row.pack(fill="x", pady=(4, 0))

            ctk.CTkLabel(val_row, textvariable=val_var,
                         font=ctk.CTkFont(size=22, weight="bold"),
                         text_color=COLOR_TEXT_MAIN).pack(side="left")
            ctk.CTkLabel(val_row, text=icon,
                         font=ctk.CTkFont(size=20),
                         text_color=icon_color).pack(side="right")

            ctk.CTkLabel(inner, textvariable=sub_var,
                         font=ctk.CTkFont(size=10),
                         text_color=COLOR_TEXT_SUB).pack(anchor="w", pady=(2, 0))

        two_col = ctk.CTkFrame(self.scroll, fg_color="transparent")
        two_col.pack(fill="x", padx=2, pady=(0, 10))
        two_col.grid_columnconfigure(0, weight=3)
        two_col.grid_columnconfigure(1, weight=2)
        two_col.grid_rowconfigure(0, weight=1)

        folders_card = ctk.CTkFrame(two_col, fg_color=COLOR_CARD_BG,
                                     corner_radius=12, border_width=1,
                                     border_color=COLOR_CARD_BORDER)
        folders_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        hdr = ctk.CTkFrame(folders_card, fg_color="transparent")
        hdr.pack(fill="x", padx=16, pady=(12, 6))
        ctk.CTkLabel(hdr, text="☁ Cloud Folders",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=COLOR_TEXT_MAIN).pack(side="left")
        self._folder_count_lbl = ctk.CTkLabel(hdr, text="",
                                              font=ctk.CTkFont(size=11),
                                              text_color=COLOR_TEXT_SUB)
        self._folder_count_lbl.pack(side="right")

        self.folders_scroll = ctk.CTkScrollableFrame(
            folders_card, height=150, fg_color="transparent",
            scrollbar_button_color=THEME['card_border'],
            scrollbar_button_hover_color=THEME['hover'])
        self.folders_scroll.pack(fill="x", padx=12, pady=(0, 12))

        self._folder_loading = ctk.CTkLabel(
            self.folders_scroll, text="Scanning folders...",
            font=ctk.CTkFont(size=11), text_color=COLOR_TEXT_SUB)
        self._folder_loading.pack(pady=20)

        right_col = ctk.CTkFrame(two_col, fg_color="transparent")
        right_col.grid(row=0, column=1, sticky="nsew")



        qa_card = ctk.CTkFrame(right_col, fg_color=COLOR_CARD_BG,
                                corner_radius=12, border_width=1,
                                border_color=COLOR_CARD_BORDER)
        qa_card.pack(fill="x")

        ctk.CTkLabel(qa_card, text="Quick Actions",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=COLOR_TEXT_MAIN).pack(anchor="w", padx=16, pady=(12, 8))

        actions = [
            ("⬆", "Upload Files", "Encrypt & upload to IA", THEME['glass_overlay'], THEME['primary'], 1),
            ("🌐", "URL Upload", "From Google Drive, Dropbox...", THEME['glass_overlay'], THEME['success'], 2),
            ("📥", "Explorer", "Browse encrypted vault", THEME['glass_overlay'], THEME['secondary'], 3),
            ("📂", "Files", "Browse unencrypted files", THEME['glass_overlay'], THEME['primary'], 4),
        ]

        for icon, title, subtitle, bg, accent, tab_idx in actions:
            btn = ctk.CTkButton(
                qa_card, text=f"{icon}  {title}",
                anchor="w", height=32, corner_radius=8,
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color=bg, hover_color=THEME['hover_subtle'],
                text_color=accent,
                command=lambda t=tab_idx: self.on_navigate(t) if self.on_navigate else None)
            btn.pack(fill="x", padx=12, pady=2)
            apply_bubble_hover(btn, glow_color=accent)

        ctk.CTkFrame(qa_card, height=8, fg_color="transparent").pack()

        feat_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        feat_frame.pack(fill="x", padx=2, pady=(0, 2))
        feat_frame.grid_columnconfigure((0, 1, 2), weight=1)

        feats = [
            ("🔒", "Zero-Knowledge Encryption",
             "Files are encrypted locally with AES-256 before upload. Neither Internet Archive nor anyone else can read your data without your password.",
             THEME['primary']),
            ("☁", "Internet Archive Storage",
             "Your encrypted files are stored on archive.org — a non-profit digital library with 99.99% uptime and permanent preservation.",
             THEME['secondary']),
            ("⚡", "Multi-Threaded Transfers",
             "6 concurrent worker threads handle uploads and downloads in parallel. Smart retry logic with exponential backoff for failed transfers.",
             THEME['success']),
        ]

        for col, (icon, title, desc, color) in enumerate(feats):
            card = ctk.CTkFrame(feat_frame, fg_color=COLOR_CARD_BG,
                                 corner_radius=12, border_width=1,
                                 border_color=COLOR_CARD_BORDER)
            card.grid(row=0, column=col, sticky="nsew",
                       padx=(0, 8) if col < 2 else 0)

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="both", padx=14, pady=14)

            ctk.CTkLabel(inner, text=icon, font=ctk.CTkFont(size=24),
                         text_color=color).pack(anchor="w")
            ctk.CTkLabel(inner, text=title,
                         font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=COLOR_TEXT_MAIN).pack(anchor="w", pady=(6, 2))
            ctk.CTkLabel(inner, text=desc,
                         font=ctk.CTkFont(size=9),
                         text_color=COLOR_TEXT_SUB, wraplength=200,
                         justify="left").pack(anchor="w")

    def _load_stats_background(self):
        if not self.storage_engine:
            return

        def load():
            try:
                folders = self.storage_engine.scan_user_folders()
                if not folders:
                    return

                folder_details = [(f, "—") for f in folders]

                try:
                    self.after(0, lambda: self._update_stats(
                        len(folders), "—", "—", folder_details))
                except Exception:
                    pass
            except Exception as e:
                logger.error(f"Dashboard stats load failed: {e}")

        threading.Thread(target=load, daemon=True).start()

    def _update_stats(self, folder_count, file_count, total_bytes, folder_details):
        folders_var, folders_sub = self._stat_vars["folders"]
        files_var, files_sub = self._stat_vars["files"]
        storage_var, storage_sub = self._stat_vars["storage"]

        folders_var.set(str(folder_count))
        folders_sub.set(f"{folder_count} folder{'s' if folder_count != 1 else ''} in vault")

        files_var.set(str(file_count))
        if isinstance(file_count, int):
            files_sub.set(f"{file_count} encrypted file{'s' if file_count != 1 else ''}")
        else:
            files_sub.set("Click Explorer to browse")

        if isinstance(total_bytes, int):
            storage_var.set(self._fmt_size(total_bytes))
        else:
            storage_var.set("—")
        storage_sub.set(f"Across {folder_count} folders")



        if self._folder_loading.winfo_exists():
            self._folder_loading.destroy()

        if self._folder_count_lbl.winfo_exists():
            self._folder_count_lbl.configure(text=f"{folder_count} folders")

        for folder, folder_files in folder_details:
            row = ctk.CTkFrame(self.folders_scroll, fg_color="transparent")
            row.pack(fill="x", pady=1, padx=4)

            ctk.CTkLabel(row, text="📁", font=ctk.CTkFont(size=12),
                         text_color=THEME['primary'], width=24).pack(side="left")
            ctk.CTkLabel(row, text=folder,
                         font=ctk.CTkFont(size=11),
                         text_color=COLOR_TEXT_MAIN).pack(side="left", padx=(4, 0))
            ctk.CTkLabel(row, text=f"{folder_files} file{'s' if folder_files != 1 else ''}",
                         font=ctk.CTkFont(size=9),
                         text_color=COLOR_TEXT_SUB).pack(side="right")

    @staticmethod
    def _fmt_size(size_bytes):
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

    def on_task_update(self, status, result):
        pass
