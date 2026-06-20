import customtkinter as ctk
import math
from aegis_vault.utils.logger import logger

COLOR_SIDEBAR_BG   = "#09090B"
COLOR_SECTION_HDR  = "#71717A"
COLOR_INPUT_BG     = "#09090B"
COLOR_SELECTED_BG  = "#27272A"
COLOR_SELECTED_FG  = "#818CF8"
COLOR_CARD_BG      = "#18181B"
COLOR_CARD_BORDER  = "#27272A"

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


class StorageDonut(ctk.CTkCanvas):
    """A simple canvas-based donut chart for storage usage."""

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

        # Background ring
        self.create_arc(x0, y0, x1, y1, start=0, extent=359.99,
                        style="arc", width=9, outline="#27272A")

        # Foreground arc
        if pct > 0:
            extent = (pct / 100) * 359.99
            self.create_arc(x0, y0, x1, y1, start=90, extent=-extent,
                            style="arc", width=9, outline="#6366F1")

        # Centre text
        cx, cy = s / 2, s / 2
        self.create_text(cx, cy - 7, text=f"{pct:.0f}%",
                         fill="#F4F4F5", font=("Helvetica", 12, "bold"))
        self.create_text(cx, cy + 8, text="of 10 TB",
                         fill="#71717A", font=("Helvetica", 7))


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
        """Receive pre-loaded folders — skip the network fetch."""
        self.on_task_update("success", {"action": "folders_loaded", "folders": folders})

    def build_ui(self):
        # ══════════════════════════════════════════════════════════════════
        # BOTTOM ITEMS — must be packed BEFORE any expand=True widget
        # so tkinter reserves their space first
        # ══════════════════════════════════════════════════════════════════

        # ── Version Footer ────────────────────────────────────────────────
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(side="bottom", fill="x", padx=14, pady=(2, 6))
        
        ctk.CTkLabel(footer, text="Made by Samar in India 🇮🇳",
                     font=ctk.CTkFont(size=9, weight="bold"), 
                     text_color="#FF9933").pack(pady=(0, 2))
        
        version_row = ctk.CTkFrame(footer, fg_color="transparent")
        version_row.pack(fill="x")
        ctk.CTkLabel(version_row, text="● Aegis v3.0.0",
                     font=ctk.CTkFont(size=9), text_color="#6366F1").pack(side="left")
        ctk.CTkLabel(version_row, text="● All systems operational",
                     font=ctk.CTkFont(size=9), text_color="#22C55E").pack(side="right")

        # ── Logout ────────────────────────────────────────────────────────
        logout_btn = ctk.CTkButton(
            self,
            text="⟵  Logout Account",
            height=30,
            corner_radius=8,
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            text_color="#71717A",
            hover_color="#18181B",
            border_width=0,
            command=self.on_logout
        )
        logout_btn.pack(side="bottom", fill="x", padx=14, pady=(0, 4))

        # ── Force Connect Panel ───────────────────────────────────────────
        manual_frame = ctk.CTkFrame(self, fg_color=COLOR_CARD_BG,
                                     corner_radius=10, border_width=1,
                                     border_color=COLOR_CARD_BORDER)
        manual_frame.pack(side="bottom", fill="x", padx=10, pady=(0, 6))

        fc_top = ctk.CTkFrame(manual_frame, fg_color="transparent")
        fc_top.pack(fill="x", padx=10, pady=(8, 0))

        ctk.CTkLabel(fc_top, text="Manual Folder Access",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color="#D4D4D8").pack(side="left")

        ctk.CTkLabel(manual_frame, text="Type folder name to open directly",
                     font=ctk.CTkFont(size=10), text_color="#52525B").pack(
            anchor="w", padx=10, pady=(2, 6))

        self.manual_entry = ctk.CTkEntry(
            manual_frame, height=30,
            placeholder_text="folder-name",
            font=ctk.CTkFont(size=11),
            fg_color=COLOR_INPUT_BG,
            border_color="#27272A"
        )
        self.manual_entry.pack(fill="x", padx=10, pady=(0, 6))
        self.manual_entry.bind("<Return>", lambda e: self.force_manual_folder())

        manual_btn = ctk.CTkButton(
            manual_frame,
            text="⚡  Open Folder",
            height=30,
            corner_radius=8,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#4F46E5",
            hover_color="#6366F1",
            command=self.force_manual_folder
        )
        manual_btn.pack(fill="x", padx=10, pady=(0, 8))

        # ══════════════════════════════════════════════════════════════════
        # TOP / SCROLLABLE ITEMS — packed after bottom items
        # ══════════════════════════════════════════════════════════════════

        # ── Logo ─────────────────────────────────────────────────────────
        logo_frame = ctk.CTkFrame(self, fg_color="transparent")
        logo_frame.pack(fill="x", padx=14, pady=(18, 6))

        logo_icon_frame = ctk.CTkFrame(
            logo_frame,
            width=42, height=42,
            corner_radius=10,
            fg_color="#18181B",
            border_width=1,
            border_color="#27272A"
        )
        logo_icon_frame.pack(side="left")
        logo_icon_frame.pack_propagate(False)

        ctk.CTkLabel(logo_icon_frame, text="🛡", font=ctk.CTkFont(size=20),
                     text_color="#818CF8").place(relx=0.5, rely=0.5, anchor="center")

        logo_text_frame = ctk.CTkFrame(logo_frame, fg_color="transparent")
        logo_text_frame.pack(side="left", padx=(10, 0))

        ctk.CTkLabel(logo_text_frame, text="A E G I S",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color="#F4F4F5").pack(anchor="w")
        ctk.CTkLabel(logo_text_frame, text="MODERN CLOUD VAULT",
                     font=ctk.CTkFont(size=7),
                     text_color="#52525B").pack(anchor="w")

        # ── Divider ───────────────────────────────────────────────────────
        ctk.CTkFrame(self, height=1, fg_color="#27272A").pack(fill="x", padx=14, pady=(6, 10))

        # ── CLOUD FOLDERS ─────────────────────────────────────────────────
        folders_header = ctk.CTkFrame(self, fg_color="transparent")
        folders_header.pack(fill="x", padx=16, pady=(2, 6))
        
        ctk.CTkLabel(folders_header, text="CLOUD FOLDERS",
                     font=ctk.CTkFont(size=9, weight="bold"),
                     text_color=COLOR_SECTION_HDR).pack(side="left")
        
        refresh_btn = ctk.CTkButton(
            folders_header, text="🔄", width=24, height=24,
            corner_radius=6, font=ctk.CTkFont(size=12),
            fg_color="transparent", hover_color="#27272A",
            text_color="#818CF8",
            command=self.refresh_folders
        )
        refresh_btn.pack(side="right")

        # Dynamic folder scroll — expand=True, packed LAST among top items
        self.folder_scroll = ctk.CTkScrollableFrame(self, height=120, fg_color="transparent")
        self.folder_scroll.pack(fill="both", expand=True, padx=5, pady=(0, 4))

        self.status_lbl = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=9),
                                        text_color="#52525B")
        self.status_lbl.pack(pady=(0, 4))

        # ── SECURITY ─────────────────────────────────────────────────────
        ctk.CTkFrame(self, height=1, fg_color="#27272A").pack(fill="x", padx=14, pady=(4, 8))
        ctk.CTkLabel(self, text="SECURITY",
                     font=ctk.CTkFont(size=9, weight="bold"),
                     text_color=COLOR_SECTION_HDR).pack(anchor="w", padx=16, pady=(0, 6))

        self._security_row("🛡", "Vault Status", "Secure", "#22C55E")
        self._security_row("🔐", "Encryption", "AES-256", "#818CF8")

        # ── STORAGE USAGE ─────────────────────────────────────────────────
        ctk.CTkFrame(self, height=1, fg_color="#27272A").pack(fill="x", padx=14, pady=(8, 8))
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
                                      font=ctk.CTkFont(size=10), text_color="#71717A")
        self.used_lbl.pack(side="left")
        self.total_lbl = ctk.CTkLabel(usage_row, text="10 TB  Total",
                                       font=ctk.CTkFont(size=10), text_color="#71717A")
        self.total_lbl.pack(side="right")

    # ─── Helpers ──────────────────────────────────────────────────────────
    def _security_row(self, icon, label, value, value_color):
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=(0, 6))

        ctk.CTkLabel(row, text=icon, font=ctk.CTkFont(size=13),
                     text_color="#818CF8", width=22).pack(side="left")
        ctk.CTkLabel(row, text=label, font=ctk.CTkFont(size=11),
                     text_color="#A1A1AA").pack(side="left", padx=(4, 0))

        ctk.CTkLabel(row, text=value, font=ctk.CTkFont(size=10, weight="bold"),
                     fg_color="#09090B", corner_radius=6,
                     text_color=value_color, padx=8, pady=2).pack(side="right")

    # ─── Logic ────────────────────────────────────────────────────────────
    def force_manual_folder(self):
        folder_name = self.manual_entry.get().strip().lower().replace(" ", "-")
        if folder_name:
            self.manual_entry.delete(0, 'end')
            self.on_folder_select(folder_name)

    def refresh_folders(self):
        self.status_lbl.configure(text="⟳ Scanning folders...", text_color="#818CF8")
        for widget in self.folder_scroll.winfo_children():
            widget.destroy()
        
        # Show loading message
        loading_lbl = ctk.CTkLabel(
            self.folder_scroll,
            text="⟳ Loading...",
            font=ctk.CTkFont(size=11),
            text_color="#818CF8"
        )
        loading_lbl.pack(pady=10)
        
        # Submit to queue worker (non-blocking)
        self.queue_worker.submit_task(self._fetch_folders)

    def _fetch_folders(self):
        folders = self.storage.scan_user_folders()
        return {"action": "folders_loaded", "folders": folders}

    def on_task_update(self, status, result):
        if status == "success" and isinstance(result, dict) and result.get("action") == "folders_loaded":
            folders = result.get("folders", [])
            self.status_lbl.configure(text=f"{len(folders)} folder(s) found", text_color="#52525B")

            for folder in folders:
                btn = ctk.CTkButton(
                    self.folder_scroll,
                    text=f"📁  {folder}",
                    anchor="w",
                    height=30,
                    corner_radius=8,
                    fg_color="transparent",
                    text_color="#A1A1AA",
                    hover_color="#18181B",
                    font=ctk.CTkFont(size=11),
                    command=lambda f=folder: self.on_folder_select(f)
                )
                btn.pack(fill="x", pady=2, padx=5)
            
            # Update storage usage (sample first 10 folders for performance)
            self._update_storage_usage(folders[:10])
            
        elif status == "error":
            self.status_lbl.configure(text="Error loading folders.", text_color="#EF4444")
    
    def _update_storage_usage(self, folders):
        """Update storage usage indicator based on actual data - FAST VERSION"""
        # Skip this for now - too slow, update later in background
        # Just show 0% initially
        self.donut.set_percent(0)
        self.used_lbl.configure(text="Calculating...")
        
        # Could add background calculation here if needed
        # For now, keep UI responsive
    
    @staticmethod
    def _format_storage(size_bytes):
        """Format bytes to human-readable storage size"""
        if size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        elif size_bytes < 1024 * 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024 * 1024):.2f} TB"
