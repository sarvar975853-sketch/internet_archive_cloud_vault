import os
import customtkinter as ctk
from tkinter import filedialog, messagebox

DND_SUPPORTED = False

COLOR_INPUT_BG     = "#09090B"
COLOR_CARD_BG      = "#18181B"
COLOR_CARD_BORDER  = "#27272A"
COLOR_TEXT_MAIN    = "#F4F4F5"
COLOR_TEXT_SUB     = "#A1A1AA"
COLOR_TEXT_ACCENT  = "#818CF8"
COLOR_TEXT_DIM     = "#52525B"
COLOR_SUCCESS      = "#22C55E"
COLOR_ERROR        = "#EF4444"
COLOR_WARN         = "#F59E0B"
COLOR_PRIMARY      = "#6366F1"

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


class UploadFrame(ctk.CTkFrame):
    def __init__(self, master, queue_worker, storage_engine, crypto_engine):
        super().__init__(master, fg_color="transparent")
        self.queue_worker = queue_worker
        self.storage = storage_engine
        self.crypto = crypto_engine
        self.selected_files = []
        self._total_tasks = 0
        self._completed_tasks = 0
        self._no_password = False

        self.build_ui()

    def build_ui(self):
        # ── Header ────────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(16, 8))

        ctk.CTkLabel(header, text="⬆  Upload Queue",
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=COLOR_TEXT_MAIN).pack(side="left")

        self.queue_badge = ctk.CTkLabel(
            header, text="0 queued",
            font=ctk.CTkFont(size=11),
            fg_color="#09090B", corner_radius=8,
            text_color=COLOR_TEXT_ACCENT, padx=10, pady=3
        )
        self.queue_badge.pack(side="left", padx=(10, 0))

        # ── Drop Zone ────────────────────────────────────────────────────
        self.drop_frame = ctk.CTkFrame(
            self, height=140, corner_radius=14,
            border_width=2, border_color="#27272A",
            fg_color="#09090B"
        )
        self.drop_frame.pack(fill="x", padx=20, pady=(0, 10))
        self.drop_frame.pack_propagate(False)

        if DND_SUPPORTED:
            try:
                self.drop_frame.drop_target_register(DND_FILES)
                self.drop_frame.dnd_bind('<<Drop>>', self.handle_drop)
                drop_text = "📁  Drag & Drop Files Here\n\nor click to browse"
            except Exception:
                drop_text = "📁  Click to Choose Files"
        else:
            drop_text = "📁  Click to Choose Files"

        self.file_btn = ctk.CTkButton(
            self.drop_frame, text=drop_text,
            fg_color="transparent", hover_color="#18181B",
            font=ctk.CTkFont(size=13),
            text_color="#52525B",
            command=self.select_files
        )
        self.file_btn.pack(expand=True, fill="both")

        # ── File list label ───────────────────────────────────────────────
        self.file_list_lbl = ctk.CTkLabel(
            self, text="No files selected.",
            font=ctk.CTkFont(size=11), text_color="#52525B"
        )
        self.file_list_lbl.pack(pady=(0, 8))

        # ── Inputs row ───────────────────────────────────────────────────
        inputs_row = ctk.CTkFrame(self, fg_color="transparent")
        inputs_row.pack(fill="x", padx=20, pady=(0, 10))
        inputs_row.grid_columnconfigure(0, weight=1)
        inputs_row.grid_columnconfigure(1, weight=1)

        self.bucket_entry = ctk.CTkEntry(
            inputs_row, height=38,
            placeholder_text="Target Folder Name (e.g. samar-vault)",
            font=ctk.CTkFont(size=12),
            fg_color=COLOR_INPUT_BG, border_color="#27272A",
            border_width=1, corner_radius=10,
            text_color=COLOR_TEXT_MAIN, placeholder_text_color="#52525B"
        )
        self.bucket_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self.pass_entry = ctk.CTkEntry(
            inputs_row, height=38,
            placeholder_text="Password to Protect Files",
            show="•", font=ctk.CTkFont(size=12),
            fg_color=COLOR_INPUT_BG, border_color="#27272A",
            border_width=1, corner_radius=10,
            text_color=COLOR_TEXT_MAIN, placeholder_text_color="#52525B"
        )
        self.pass_entry.grid(row=0, column=1, sticky="ew")

        # ── No Password Toggle ───────────────────────────────────────────
        toggle_frame = ctk.CTkFrame(self, fg_color="transparent")
        toggle_frame.pack(fill="x", padx=20, pady=(0, 10))

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

        # ── Progress card ─────────────────────────────────────────────────
        prog_card = ctk.CTkFrame(
            self, fg_color=COLOR_CARD_BG, corner_radius=12,
            border_width=1, border_color=COLOR_CARD_BORDER
        )
        prog_card.pack(fill="x", padx=20, pady=(0, 10))

        prog_inner = ctk.CTkFrame(prog_card, fg_color="transparent")
        prog_inner.pack(fill="x", padx=16, pady=12)

        # Top row: file name label + percentage
        prog_top = ctk.CTkFrame(prog_inner, fg_color="transparent")
        prog_top.pack(fill="x", pady=(0, 6))

        self.current_file_lbl = ctk.CTkLabel(
            prog_top, text="Ready to upload",
            font=ctk.CTkFont(size=11), text_color=COLOR_TEXT_SUB
        )
        self.current_file_lbl.pack(side="left")

        self.pct_lbl = ctk.CTkLabel(
            prog_top, text="",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLOR_TEXT_ACCENT
        )
        self.pct_lbl.pack(side="right")

        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(
            prog_inner, height=8, corner_radius=4,
            progress_color=COLOR_PRIMARY, fg_color="#09090B"
        )
        self.progress_bar.pack(fill="x")
        self.progress_bar.set(0)

        # Bottom row: status text
        self.status_lbl = ctk.CTkLabel(
            prog_inner, text="",
            font=ctk.CTkFont(size=10), text_color=COLOR_TEXT_SUB
        )
        self.status_lbl.pack(anchor="w", pady=(4, 0))

        # ── Upload Button ─────────────────────────────────────────────────
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 4))
        
        self.upload_btn = ctk.CTkButton(
            btn_frame,
            text="🔒  Scramble & Upload Queue",
            height=44, corner_radius=12,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=COLOR_PRIMARY, hover_color="#4F46E5",
            command=self.start_upload
        )
        self.upload_btn.pack(side="left", fill="x", expand=True, padx=(0, 8))
        apply_hover_bump(self.upload_btn, 400, 44)
        
        clear_btn = ctk.CTkButton(
            btn_frame,
            text="🗑️ Clear",
            width=80, height=44, corner_radius=12,
            font=ctk.CTkFont(size=12),
            fg_color="#3F3F46", hover_color="#52525B",
            command=self.clear_queue
        )
        clear_btn.pack(side="right")

    def _toggle_password_mode(self):
        self._no_password = self.no_pass_toggle.get() == 1
        if self._no_password:
            self.pass_entry.configure(state="disabled", fg_color="#18181B")
            self.upload_btn.configure(text="⬆  Upload Without Encryption")
        else:
            self.pass_entry.configure(state="normal", fg_color=COLOR_INPUT_BG)
            self.upload_btn.configure(text="🔒  Scramble & Upload Queue")
    
    def clear_queue(self):
        """Clear the upload queue"""
        self.selected_files.clear()
        self.file_list_lbl.configure(text="No files selected.", text_color="#52525B")
        self.queue_badge.configure(text="0 queued")
        self.progress_bar.set(0)
        self.pct_lbl.configure(text="")
        self.status_lbl.configure(text="")
        self.current_file_lbl.configure(text="Ready to upload")

    # ─── File Selection ───────────────────────────────────────────────────
    def handle_drop(self, event):
        files = self.master.tk.splitlist(event.data)
        self.add_files(files)

    def select_files(self):
        files = filedialog.askopenfilenames()
        if files:
            self.add_files(files)

    def add_files(self, files):
        for f in files:
            if f not in self.selected_files:
                self.selected_files.append(f)

        count = len(self.selected_files)
        if count:
            # Calculate total size
            total_size = sum(os.path.getsize(f) for f in self.selected_files if os.path.exists(f))
            size_str = self._format_size(total_size)
            
            self.file_list_lbl.configure(
                text=f"✓  {count} file(s) queued ({size_str} total)",
                text_color=COLOR_TEXT_ACCENT
            )
            self.queue_badge.configure(text=f"{count} queued")
    
    @staticmethod
    def _format_size(size_bytes):
        """Convert bytes to human-readable format"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

    # ─── Upload ───────────────────────────────────────────────────────────
    def start_upload(self):
        bucket   = self.bucket_entry.get().strip().lower().replace(" ", "-")
        password = self.pass_entry.get()

        if not self.selected_files or not bucket:
            messagebox.showerror("Error", "Files and folder name are required.")
            return

        if not self._no_password and not password:
            messagebox.showerror("Error", "Password is required (or toggle 'Upload without password').")
            return

        self._total_tasks     = len(self.selected_files)
        self._completed_tasks = 0
        self.upload_btn.configure(state="disabled")
        self.progress_bar.set(0)
        self.pct_lbl.configure(text="0%")
        self.status_lbl.configure(text="Preparing upload...", text_color=COLOR_TEXT_SUB)

        files_snapshot = list(self.selected_files)
        for file_path in files_snapshot:
            self.queue_worker.submit_task(self._process_single_upload, file_path, password, bucket, self._no_password)

        self.selected_files.clear()
        self.file_list_lbl.configure(text="Files added to background queue...", text_color="#52525B")
        self.queue_badge.configure(text="0 queued")

    def _process_single_upload(self, file_path, password, bucket, no_password):
        original_filename = os.path.basename(file_path)

        if no_password:
            # Upload without encryption — file stored as-is
            url = self.storage.upload_file_raw(file_path, original_filename, bucket,
                                               progress_callback=lambda sent, total: self._upload_progress(original_filename, sent, total))
            return {"file": original_filename, "url": url, "status": "success"}
        else:
            # Encrypt then upload
            temp_encrypted_path = file_path + ".ia_crypt"
            try:
                self._update_progress_callback("encrypting", original_filename, 0)
                self.crypto.encrypt_file(file_path, password, temp_encrypted_path)
                self._update_progress_callback("uploading", original_filename, 50)
                url = self.storage.upload_file(temp_encrypted_path, original_filename, bucket,
                                               progress_callback=lambda sent, total: self._upload_progress(original_filename, sent, total))
                return {"file": original_filename, "url": url, "status": "success"}
            finally:
                if os.path.exists(temp_encrypted_path):
                    os.remove(temp_encrypted_path)

    def _update_progress_callback(self, stage, filename, base_pct):
        """Update UI from background thread"""
        def update():
            if stage == "encrypting":
                self.current_file_lbl.configure(text=f"🔐 Encrypting: {filename[:40]}")
            elif stage == "uploading":
                self.current_file_lbl.configure(text=f"☁️ Uploading: {filename[:40]}")
            
            overall_pct = int((self._completed_tasks / self._total_tasks) * 100 + base_pct / self._total_tasks)
            self.progress_bar.set(min(overall_pct / 100, 0.99))
            self.pct_lbl.configure(text=f"{overall_pct}%")
        
        self.after(0, update)

    def _upload_progress(self, filename, sent, total):
        """Real-time upload progress callback"""
        if total > 0:
            upload_pct = (sent / total) * 50  # 50% of overall progress for upload
            def update():
                base = (self._completed_tasks / self._total_tasks) * 100
                current = base + (upload_pct / self._total_tasks)
                self.progress_bar.set(min(current / 100, 0.99))
                self.pct_lbl.configure(text=f"{int(current)}%")
            self.after(0, update)

    def on_task_update(self, status, result):
        self._completed_tasks += 1
        real_pct = int((self._completed_tasks / max(self._total_tasks, 1)) * 100)

        if status == "success":
            self.progress_bar.set(real_pct / 100)
            self.pct_lbl.configure(text=f"{real_pct}%", text_color=COLOR_SUCCESS)
            
            if isinstance(result, dict):
                filename = result.get("file", "Unknown")
                self.current_file_lbl.configure(text=f"✓ Completed: {filename}")
                self.status_lbl.configure(
                    text=f"Uploaded {filename} successfully",
                    text_color=COLOR_SUCCESS
                )
            else:
                self.status_lbl.configure(text=str(result)[:80], text_color=COLOR_SUCCESS)
            
            if real_pct >= 100:
                self.current_file_lbl.configure(text="🎉 All files uploaded successfully!")
                self.upload_btn.configure(state="normal")

        elif status == "error":
            self.pct_lbl.configure(text="Error", text_color=COLOR_ERROR)
            self.status_lbl.configure(text=f"❌ Error: {result}", text_color=COLOR_ERROR)
            self.upload_btn.configure(state="normal")

        if self._completed_tasks >= self._total_tasks:
            self.upload_btn.configure(state="normal")
