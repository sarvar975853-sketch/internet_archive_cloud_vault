import os
import customtkinter as ctk
from tkinter import filedialog, messagebox

COLOR_INPUT_BG     = "#09090B"
COLOR_CARD_BG      = "#18181B"
COLOR_CARD_BORDER  = "#27272A"
COLOR_TEXT_MAIN    = "#F4F4F5"
COLOR_TEXT_SUB     = "#A1A1AA"
COLOR_TEXT_ACCENT  = "#818CF8"
COLOR_TEXT_DIM     = "#52525B"
COLOR_SUCCESS      = "#22C55E"
COLOR_ERROR        = "#EF4444"


class ExplorerFrame(ctk.CTkFrame):
    def __init__(self, master, queue_worker, storage_engine, crypto_engine):
        super().__init__(master, fg_color="transparent")
        self.queue_worker = queue_worker
        self.storage = storage_engine
        self.crypto = crypto_engine
        self.active_folder = ""
        self.files_cache = []

        self.build_ui()

    def build_ui(self):
        # ── Header row ────────────────────────────────────────────────────
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.pack(fill="x", padx=4, pady=(4, 8))

        self.folder_title = ctk.CTkLabel(
            top_bar,
            text="📂  Select a folder from the sidebar",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#52525B"
        )
        self.folder_title.pack(side="left")

        search_frame = ctk.CTkFrame(top_bar, fg_color=COLOR_CARD_BG,
                                     corner_radius=10, border_width=1,
                                     border_color=COLOR_CARD_BORDER)
        search_frame.pack(side="right")

        ctk.CTkLabel(search_frame, text="🔍", font=ctk.CTkFont(size=13),
                     text_color="#52525B").pack(side="left", padx=(8, 0))

        self.search_entry = ctk.CTkEntry(
            search_frame, width=200, height=34,
            placeholder_text="Search files...",
            fg_color="transparent", border_width=0,
            font=ctk.CTkFont(size=12),
            text_color=COLOR_TEXT_MAIN,
            placeholder_text_color="#52525B"
        )
        self.search_entry.pack(side="left", padx=(4, 8))
        self.search_entry.bind("<KeyRelease>", self.filter_files)

        # ── File List ─────────────────────────────────────────────────────
        list_card = ctk.CTkFrame(self, fg_color=COLOR_CARD_BG,
                                  corner_radius=12, border_width=1,
                                  border_color=COLOR_CARD_BORDER)
        list_card.pack(fill="both", expand=True, padx=4, pady=(0, 8))

        self.file_list_frame = ctk.CTkScrollableFrame(list_card, fg_color="transparent")
        self.file_list_frame.pack(fill="both", expand=True, padx=8, pady=8)

        self.selected_file_var = ctk.StringVar(value="")

        # ── Download Action Area ───────────────────────────────────────────
        action_card = ctk.CTkFrame(self, fg_color=COLOR_CARD_BG,
                                    corner_radius=12, border_width=1,
                                    border_color=COLOR_CARD_BORDER)
        action_card.pack(fill="x", padx=4, pady=(0, 6))

        action_inner = ctk.CTkFrame(action_card, fg_color="transparent")
        action_inner.pack(fill="x", padx=14, pady=12)
        action_inner.grid_columnconfigure(0, weight=1)

        action_row = ctk.CTkFrame(action_inner, fg_color="transparent")
        action_row.pack(fill="x", pady=(0, 8))

        self.dl_pass_entry = ctk.CTkEntry(
            action_row, height=38,
            placeholder_text="🔑  Enter Matching Password to Unlock",
            show="•", font=ctk.CTkFont(size=12),
            fg_color=COLOR_INPUT_BG, border_color="#27272A",
            border_width=1, corner_radius=10,
            text_color=COLOR_TEXT_MAIN, placeholder_text_color="#52525B"
        )
        self.dl_pass_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.download_btn = ctk.CTkButton(
            action_row,
            text="🔓  Fetch & Decrypt",
            width=180, height=38,
            corner_radius=10,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#6366F1", hover_color="#4F46E5",
            command=self.start_download
        )
        self.download_btn.pack(side="left")

        # Progress
        self.progress_bar = ctk.CTkProgressBar(
            action_inner, height=6, corner_radius=3,
            progress_color="#6366F1", fg_color="#09090B"
        )
        self.progress_bar.pack(fill="x", pady=(0, 4))
        self.progress_bar.set(0)

        self.status_lbl = ctk.CTkLabel(
            action_inner, text="Ready",
            font=ctk.CTkFont(size=10), text_color=COLOR_TEXT_SUB
        )
        self.status_lbl.pack(anchor="w")

    def load_folder(self, folder_name):
        self.active_folder = folder_name
        self.folder_title.configure(
            text=f"📂  {folder_name}", text_color=COLOR_TEXT_ACCENT
        )
        self.status_lbl.configure(text=f"Loading {folder_name} metadata...")
        self.queue_worker.submit_task(self._fetch_metadata, folder_name)

    def _fetch_metadata(self, folder_name):
        files = self.storage.get_files_in_bucket(folder_name)
        return {"action": "metadata_loaded", "files": files}

    def populate_list(self, files):
        self.files_cache = files
        self.filter_files()
        self.status_lbl.configure(
            text=f"Loaded {len(files)} file(s).", text_color=COLOR_TEXT_SUB
        )

    def filter_files(self, event=None):
        query = self.search_entry.get().lower()

        for widget in self.file_list_frame.winfo_children():
            widget.destroy()

        if not self.files_cache:
            ctk.CTkLabel(
                self.file_list_frame,
                text="No files found in this folder.",
                font=ctk.CTkFont(size=12),
                text_color="#52525B"
            ).pack(pady=30)
            return

        displayed_count = 0
        for f in self.files_cache:
            name = f['name']
            if query and query not in name.lower():
                continue

            displayed_count += 1
            row = ctk.CTkFrame(self.file_list_frame, fg_color="#09090B",
                                corner_radius=8, border_width=1,
                                border_color=COLOR_CARD_BORDER)
            row.pack(fill="x", pady=(0, 4), padx=4)

            rb = ctk.CTkRadioButton(
                row,
                text=f"📄  {name}",
                variable=self.selected_file_var,
                value=name,
                font=ctk.CTkFont(size=11),
                text_color=COLOR_TEXT_MAIN,
                fg_color=COLOR_TEXT_ACCENT
            )
            rb.pack(side="left", anchor="w", padx=10, pady=8)

            size_str = f.get('size', 'Unknown')
            ctk.CTkLabel(row, text=size_str,
                         font=ctk.CTkFont(size=10), text_color="#52525B").pack(
                side="right", padx=10
            )

            # Copy button
            copy_btn = ctk.CTkButton(
                row, text="📋", width=30, height=24,
                corner_radius=6, fg_color="transparent",
                hover_color="#27272A", text_color="#A1A1AA",
                command=lambda n=name: self._copy_filename(n)
            )
            copy_btn.pack(side="right", padx=(0, 4))

            # Delete button
            del_btn = ctk.CTkButton(
                row, text="🗑", width=30, height=24,
                corner_radius=6, fg_color="transparent",
                hover_color="#7F1D1D", text_color="#EF4444",
                command=lambda n=name: self._delete_file(n)
            )
            del_btn.pack(side="right", padx=(0, 4))

        # Show count
        if query and displayed_count == 0:
            ctk.CTkLabel(
                self.file_list_frame,
                text=f"No files match '{query}'",
                font=ctk.CTkFont(size=12),
                text_color="#52525B"
            ).pack(pady=30)

    def _copy_filename(self, filename):
        self.clipboard_clear()
        self.clipboard_append(filename)
        self.update()
        from aegis_vault.gui.toast import show_toast
        show_toast(self.winfo_toplevel(), f"Copied: {filename[:30]}...", 2000, "success")

    def _delete_file(self, filename):
        if not self.active_folder:
            return
        confirm = messagebox.askyesno(
            "Delete File",
            f"Delete '{filename}' from {self.active_folder}?\n\nThis cannot be undone."
        )
        if not confirm:
            return
        self.status_lbl.configure(text=f"Deleting {filename}...")
        self.queue_worker.submit_task(
            self._process_delete, self.active_folder, filename
        )

    def _process_delete(self, bucket, filename):
        self.storage.delete_file(bucket, filename, encrypted=True)
        return {"action": "file_deleted", "filename": filename}

    def start_download(self):
        selected_file = self.selected_file_var.get()
        password = self.dl_pass_entry.get()

        if not selected_file or not self.active_folder or not password:
            messagebox.showerror("Error", "Select a file and enter the password.")
            return

        save_path = filedialog.asksaveasfilename(initialfile=selected_file)
        if not save_path:
            return

        self.download_btn.configure(state="disabled")
        self.status_lbl.configure(text=f"Queued {selected_file} for download...")
        self.progress_bar.set(0)

        self.queue_worker.submit_task(
            self._process_download, self.active_folder, selected_file, password, save_path
        )

    def _process_download(self, bucket, filename, password, save_path):
        temp_enc_path = save_path + ".enc.tmp"

        self.storage.download_file(bucket, filename, temp_enc_path, None)

        try:
            self.crypto.decrypt_file(temp_enc_path, password, save_path)
            return {"action": "download_complete", "msg": f"Successfully decrypted {filename}"}
        finally:
            if os.path.exists(temp_enc_path):
                os.remove(temp_enc_path)

    def on_task_update(self, status, result):
        if status == "success":
            if isinstance(result, dict):
                action = result.get("action")
                if action == "metadata_loaded":
                    self.populate_list(result.get("files", []))
                elif action == "download_complete":
                    self.status_lbl.configure(text=result.get("msg"), text_color=COLOR_SUCCESS)
                    self.progress_bar.set(1.0)
                    self.download_btn.configure(state="normal")
                elif action == "file_deleted":
                    self.status_lbl.configure(
                        text=f"✓ Deleted {result.get('filename', '')}",
                        text_color=COLOR_SUCCESS
                    )
                    # Refresh the file list
                    if self.active_folder:
                        self.load_folder(self.active_folder)
        elif status == "error":
            self.status_lbl.configure(text=f"Error: {result}", text_color=COLOR_ERROR)
            self.download_btn.configure(state="normal")
