import customtkinter as ctk
import threading
from aegis_vault.utils.logger import logger
from aegis_vault.gui.theme import THEME
from aegis_vault.gui.hover import apply_bubble_hover

COLOR_SIDEBAR_BG   = THEME['sidebar_bg']
COLOR_SECTION_HDR  = THEME['section_header']
COLOR_INPUT_BG     = THEME['input_bg']
COLOR_SELECTED_BG  = THEME['selected_bg']
COLOR_SELECTED_FG  = THEME['selected_fg']
COLOR_CARD_BG      = THEME['card_bg']
COLOR_CARD_BORDER  = THEME['card_border']
COLOR_SUCCESS      = THEME['success']

def apply_hover_bump(button, base_w, base_h):
    button.bind("<Enter>", lambda event: button.configure(
        width=base_w + 10,
        height=base_h + 3,
        border_width=1,
        border_color=THEME['border_focus']
    ))
    button.bind("<Leave>", lambda event: button.configure(
        width=base_w,
        height=base_h,
        border_width=0
    ))


class StorageDonut(ctk.CTkCanvas):
    def __init__(self, master, size=90, **kwargs):
        super().__init__(master, width=size, height=size,
                         bg=COLOR_SIDEBAR_BG, highlightthickness=0, **kwargs)
        self.size = size
        self.percent = 0.0
        self._draw(0.0)

    def set_percent(self, pct: float):
        self.percent = max(0.0, min(100.0, pct))
        self._draw(self.percent)

    def _draw(self, pct):
        self.delete("all")
        s = self.size
        pad = 8
        x0, y0, x1, y1 = pad, pad, s - pad, s - pad

        self.create_arc(x0, y0, x1, y1, start=0, extent=359.99,
                        style="arc", width=9, outline=THEME['card_border'])

        if pct > 0:
            extent = (pct / 100) * 359.99
            self.create_arc(x0, y0, x1, y1, start=90, extent=-extent,
                            style="arc", width=9, outline=THEME['accent_indigo'])

        cx, cy = s / 2, s / 2
        self.create_text(cx, cy - 7, text=f"{pct:.0f}%",
                         fill=THEME['text_main'], font=("Helvetica", 12, "bold"))
        self.create_text(cx, cy + 8, text="of 10 TB",
                         fill=THEME['section_header'], font=("Helvetica", 7))


class SidebarFrame(ctk.CTkFrame):
    def __init__(self, master, queue_worker, storage_engine, on_folder_select, on_logout):
        super().__init__(master, width=255, corner_radius=0, fg_color=COLOR_SIDEBAR_BG)
        self.grid_propagate(False)
        self.queue_worker = queue_worker
        self.storage = storage_engine
        self.on_folder_select = on_folder_select
        self.on_logout = on_logout
        self._folder_buttons = []

        self.build_ui()

    def inject_folders(self, folders):
        for widget in self.folder_scroll.winfo_children():
            widget.destroy()
        self._folder_buttons.clear()
        self.on_task_update("success", {"action": "folders_loaded", "folders": folders})

    def build_ui(self):
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(side="bottom", fill="x", padx=14, pady=(2, 6))

        ctk.CTkLabel(footer, text="Made by Samar in India 🇮🇳",
                     font=ctk.CTkFont(size=9, weight="bold"),
                     text_color="#FF9933").pack(pady=(0, 2))

        version_row = ctk.CTkFrame(footer, fg_color="transparent")
        version_row.pack(fill="x")
        ctk.CTkLabel(version_row, text="● Aegis v3.5.0",
                     font=ctk.CTkFont(size=9), text_color=THEME['accent_indigo']).pack(side="left")
        ctk.CTkLabel(version_row, text="● All systems operational",
                     font=ctk.CTkFont(size=9), text_color=THEME['success']).pack(side="right")

        support_btn = ctk.CTkButton(
            footer,
            text="♥ Support via Ads",
            height=22,
            corner_radius=6,
            font=ctk.CTkFont(size=9),
            fg_color="transparent",
            text_color="#888",
            hover_color=THEME['hover_subtle'],
            border_width=0,
            command=lambda: self._open_support_site()
        )
        support_btn.pack(pady=(2, 0))

        logout_btn = ctk.CTkButton(
            self,
            text="⟵  Logout Account",
            height=30,
            corner_radius=8,
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            text_color=THEME['section_header'],
            hover_color=THEME['hover_subtle'],
            border_width=0,
            command=self.on_logout
        )
        logout_btn.pack(side="bottom", fill="x", padx=14, pady=(0, 4))
        apply_bubble_hover(logout_btn, glow_color=THEME['error'])

        manual_frame = ctk.CTkFrame(self, fg_color=COLOR_CARD_BG,
                                     corner_radius=10, border_width=1,
                                     border_color=COLOR_CARD_BORDER)
        manual_frame.pack(side="bottom", fill="x", padx=10, pady=(0, 6))

        fc_top = ctk.CTkFrame(manual_frame, fg_color="transparent")
        fc_top.pack(fill="x", padx=10, pady=(8, 0))

        ctk.CTkLabel(fc_top, text="Manual Folder Access",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=THEME['text_main']).pack(side="left")

        ctk.CTkLabel(manual_frame, text="Type folder name to open directly",
                     font=ctk.CTkFont(size=10), text_color=THEME['text_dim']).pack(
            anchor="w", padx=10, pady=(2, 6))

        self.manual_entry = ctk.CTkEntry(
            manual_frame, height=30,
            placeholder_text="folder-name",
            font=ctk.CTkFont(size=11),
            fg_color=COLOR_INPUT_BG,
            border_color=THEME['border_subtle']
        )
        self.manual_entry.pack(fill="x", padx=10, pady=(0, 6))
        self.manual_entry.bind("<Return>", lambda e: self.force_manual_folder())

        manual_btn = ctk.CTkButton(
            manual_frame,
            text="⚡  Open Folder",
            height=30,
            corner_radius=8,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=THEME['primary'],
            hover_color=THEME['accent_indigo'],
            command=self.force_manual_folder
        )
        manual_btn.pack(fill="x", padx=10, pady=(0, 8))
        apply_bubble_hover(manual_btn, glow_color=THEME['primary'])

        logo_frame = ctk.CTkFrame(self, fg_color="transparent")
        logo_frame.pack(fill="x", padx=14, pady=(18, 6))

        logo_icon_frame = ctk.CTkFrame(
            logo_frame,
            width=42, height=42,
            corner_radius=10,
            fg_color=THEME['glass_overlay'],
            border_width=1,
            border_color=THEME['border_subtle']
        )
        logo_icon_frame.pack(side="left")
        logo_icon_frame.pack_propagate(False)

        ctk.CTkLabel(logo_icon_frame, text="🛡", font=ctk.CTkFont(size=20),
                     text_color=THEME['accent_indigo']).place(relx=0.5, rely=0.5, anchor="center")

        logo_text_frame = ctk.CTkFrame(logo_frame, fg_color="transparent")
        logo_text_frame.pack(side="left", padx=(10, 0))

        ctk.CTkLabel(logo_text_frame, text="A E G I S",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=THEME['text_main']).pack(anchor="w")
        ctk.CTkLabel(logo_text_frame, text="MODERN CLOUD VAULT",
                     font=ctk.CTkFont(size=7),
                     text_color=THEME['text_dim']).pack(anchor="w")

        ctk.CTkFrame(self, height=1, fg_color=THEME['border_subtle']).pack(fill="x", padx=14, pady=(6, 10))

        folders_header = ctk.CTkFrame(self, fg_color="transparent")
        folders_header.pack(fill="x", padx=16, pady=(2, 6))

        ctk.CTkLabel(folders_header, text="CLOUD FOLDERS",
                     font=ctk.CTkFont(size=9, weight="bold"),
                     text_color=COLOR_SECTION_HDR).pack(side="left")

        refresh_btn = ctk.CTkButton(
            folders_header, text="🔄", width=24, height=24,
            corner_radius=6, font=ctk.CTkFont(size=12),
            fg_color="transparent", hover_color=THEME['hover_subtle'],
            text_color=THEME['accent_indigo'],
            command=self.refresh_folders
        )
        refresh_btn.pack(side="right")

        create_folder_btn = ctk.CTkButton(
            folders_header, text="＋", width=24, height=24,
            corner_radius=6, font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="transparent", hover_color=THEME['hover_subtle'],
            text_color=COLOR_SUCCESS,
            command=self._create_folder
        )
        create_folder_btn.pack(side="right", padx=(0, 4))

        self.folder_scroll = ctk.CTkScrollableFrame(self, height=120, fg_color="transparent")
        self.folder_scroll.pack(fill="both", expand=True, padx=5, pady=(0, 4))

        self.status_lbl = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=9),
                                        text_color=THEME['text_dim'])
        self.status_lbl.pack(pady=(0, 4))

        ctk.CTkFrame(self, height=1, fg_color=THEME['border_subtle']).pack(fill="x", padx=14, pady=(4, 8))
        ctk.CTkLabel(self, text="SECURITY",
                     font=ctk.CTkFont(size=9, weight="bold"),
                     text_color=COLOR_SECTION_HDR).pack(anchor="w", padx=16, pady=(0, 6))

        self._security_row("🛡", "Vault Status", "Secure", THEME['success'])
        self._security_row("🔐", "Encryption", "AES-256", THEME['accent_indigo'])

        ctk.CTkFrame(self, height=1, fg_color=THEME['border_subtle']).pack(fill="x", padx=14, pady=(8, 8))
        ctk.CTkLabel(self, text="STORAGE USAGE",
                     font=ctk.CTkFont(size=9, weight="bold"),
                     text_color=COLOR_SECTION_HDR).pack(anchor="w", padx=16, pady=(0, 8))

        donut_frame = ctk.CTkFrame(self, fg_color="transparent")
        donut_frame.pack(pady=(0, 4))

        self.donut = StorageDonut(donut_frame, size=90)
        self.donut.pack()

        usage_row = ctk.CTkFrame(self, fg_color="transparent")
        usage_row.pack(fill="x", padx=16, pady=(4, 6))
        self.used_lbl = ctk.CTkLabel(usage_row, text="0 B  Used",
                                      font=ctk.CTkFont(size=10), text_color=THEME['section_header'])
        self.used_lbl.pack(side="left")
        self.total_lbl = ctk.CTkLabel(usage_row, text="10 TB  Total",
                                       font=ctk.CTkFont(size=10), text_color=THEME['section_header'])
        self.total_lbl.pack(side="right")

    def _security_row(self, icon, label, value, value_color):
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=(0, 6))

        ctk.CTkLabel(row, text=icon, font=ctk.CTkFont(size=13),
                     text_color=THEME['accent_indigo'], width=22).pack(side="left")
        ctk.CTkLabel(row, text=label, font=ctk.CTkFont(size=11),
                     text_color=THEME['text_sub']).pack(side="left", padx=(4, 0))

        ctk.CTkLabel(row, text=value, font=ctk.CTkFont(size=10, weight="bold"),
                     fg_color=THEME['input_bg'], corner_radius=6,
                     text_color=value_color, padx=8, pady=2).pack(side="right")

    def force_manual_folder(self):
        folder_name = self.manual_entry.get().strip().lower().replace(" ", "-")
        if folder_name:
            self.manual_entry.delete(0, 'end')
            self.on_folder_select(folder_name)

    def refresh_folders(self):
        folders = self.storage.scan_user_folders()
        self.inject_folders(folders)

    def on_task_update(self, status, result):
        if status == "success" and isinstance(result, dict) and result.get("action") == "folders_loaded":
            folders = result.get("folders", [])
            self.status_lbl.configure(text=f"{len(folders)} folder(s) found", text_color=THEME['text_dim'])

            for folder in folders:
                btn = ctk.CTkButton(
                    self.folder_scroll,
                    text=f"📁  {folder}",
                    anchor="w",
                    height=30,
                    corner_radius=8,
                    fg_color="transparent",
                    text_color=THEME['text_sub'],
                    hover_color=THEME['hover_subtle'],
                    font=ctk.CTkFont(size=11),
                    command=lambda f=folder: self.on_folder_select(f)
                )
                btn.pack(fill="x", pady=2, padx=5)
                self._folder_buttons.append(btn)

            self._update_storage_usage(folders[:10])

        elif status == "error":
            self.status_lbl.configure(text="Error loading folders.", text_color=THEME['error'])

    def _open_support_site(self):
        import webbrowser
        webbrowser.open("https://sarvar975853-sketch.github.io/")

    def _create_folder(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Create New Folder")
        dialog.geometry("400x180")
        dialog.configure(fg_color=THEME['main_bg'])
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        dialog.resizable(False, False)

        ctk.CTkLabel(
            dialog, text="📁  New Folder Name",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=THEME['text_main']
        ).pack(pady=(20, 8))

        name_entry = ctk.CTkEntry(
            dialog, height=36,
            placeholder_text="e.g. my-new-folder",
            font=ctk.CTkFont(size=12),
            fg_color=THEME['input_bg'], border_color=THEME['border_subtle'],
            border_width=1, corner_radius=8,
            text_color=THEME['text_main']
        )
        name_entry.pack(fill="x", padx=30, pady=(0, 12))
        name_entry.focus_set()

        def on_create():
            name = name_entry.get().strip()
            if not name:
                return
            name = name.lower().replace(" ", "-")
            dialog.destroy()
            self.status_lbl.configure(text=f"Creating folder '{name}'...")
            threading.Thread(target=self._do_create_folder, args=(name,), daemon=True).start()

        name_entry.bind("<Return>", lambda e: on_create())

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack()
        ctk.CTkButton(
            btn_frame, text="Create Folder", width=120, height=32,
            corner_radius=8, fg_color=COLOR_SUCCESS,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#000",
            command=on_create
        ).pack(side="left", padx=6)
        ctk.CTkButton(
            btn_frame, text="Cancel", width=80, height=32,
            corner_radius=8, fg_color=THEME['card_bg'],
            text_color=THEME['text_sub'],
            command=dialog.destroy
        ).pack(side="left", padx=6)

    def _do_create_folder(self, name):
        try:
            self.storage.create_folder(name)
            self.after(0, lambda: self._on_folder_created(name))
        except Exception as e:
            err_msg = str(e)
            self.after(0, lambda msg=err_msg: self.status_lbl.configure(
                text=f"Error creating folder: {msg}", text_color=THEME['error']
            ))

    def _on_folder_created(self, name):
        self.status_lbl.configure(text=f"✓ Created '{name}'", text_color=THEME['success'])
        self.refresh_folders()
        self.on_folder_select(name)

    def _update_storage_usage(self, folders):
        total_bytes = 0
        for folder in folders:
            try:
                data = self.storage._get_bucket_metadata(folder)
                if data and isinstance(data, dict):
                    for f in data.get("files", []):
                        size = f.get("size", 0)
                        if isinstance(size, (int, str)):
                            try:
                                total_bytes += int(size)
                            except (ValueError, TypeError):
                                pass
            except Exception:
                pass
        pct = min(total_bytes / (10 * 1024**4) * 100, 100) if total_bytes > 0 else 0
        self.donut.set_percent(pct)
        self.used_lbl.configure(text=self._format_storage(total_bytes))

    @staticmethod
    def _format_storage(size_bytes):
        if size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        elif size_bytes < 1024 * 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024 * 1024):.2f} TB"
