"""
Files Tab — Browse and download unencrypted files from Internet Archive.
Shows non-.enc files across all user buckets (files uploaded without password).
"""
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
COLOR_PRIMARY      = "#6366F1"
COLOR_HOVER        = "#27272A"


class FilesTab(ctk.CTkFrame):
    def __init__(self, master, queue_worker, storage_engine):
        super().__init__(master, fg_color="transparent")
        self.queue_worker = queue_worker
        self.storage = storage_engine
        self._all_files = []
        self._selected_file = None
        self._active_folder = ""

        self.build_ui()

    def build_ui(self):
        # ── Header ────────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=4, pady=(4, 8))

        ctk.CTkLabel(header, text="📂  Files (Unencrypted)",
                     font=ctk.CTkFont(size=15, weight="bold"),
                     text_color=COLOR_TEXT_MAIN).pack(side="left")

        self.refresh_btn = ctk.CTkButton(
            header, text="🔄 Refresh", width=80, height=30,
            corner_radius=8, font=ctk.CTkFont(size=11),
            fg_color=COLOR_PRIMARY, hover_color="#4F46E5",
            text_color="#F4F4F5",
            command=self._refresh_files
        )
        self.refresh_btn.pack(side="right")

        # ── Folder selector ───────────────────────────────────────────────
        selector_card = ctk.CTkFrame(self, fg_color=COLOR_CARD_BG,
                                      corner_radius=12, border_width=1,
                                      border_color=COLOR_CARD_BORDER)
        selector_card.pack(fill="x", padx=4, pady=(0, 8))

        sel_inner = ctk.CTkFrame(selector_card, fg_color="transparent")
        sel_inner.pack(fill="x", padx=12, pady=10)
        sel_inner.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(sel_inner, text="Select folder to scan:",
                     font=ctk.CTkFont(size=11),
                     text_color=COLOR_TEXT_SUB).pack(anchor="w")

        self.folder_var = ctk.StringVar(value="— Select Folder —")

        folder_row = ctk.CTkFrame(sel_inner, fg_color="transparent")
        folder_row.pack(fill="x", pady=(4, 0))
        folder_row.grid_columnconfigure(0, weight=1)

        self.folder_menu = ctk.CTkOptionMenu(
            folder_row, variable=self.folder_var,
            values=["Loading folders..."],
            height=34, corner_radius=8,
            font=ctk.CTkFont(size=11),
            fg_color=COLOR_INPUT_BG,
            button_color=COLOR_CARD_BORDER,
            button_hover_color=COLOR_HOVER,
            dropdown_fg_color=COLOR_CARD_BG,
            dropdown_hover_color=COLOR_HOVER,
            command=self._on_folder_select
        )
        self.folder_menu.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        load_all_btn = ctk.CTkButton(
            folder_row, text="Load All", width=80, height=34,
            corner_radius=8, font=ctk.CTkFont(size=11),
            fg_color=COLOR_PRIMARY, hover_color="#4F46E5",
            text_color="#F4F4F5",
            command=lambda: self._load_all_files()
        )
        load_all_btn.grid(row=0, column=1)

        # ── Search ────────────────────────────────────────────────────────
        search_frame = ctk.CTkFrame(self, fg_color=COLOR_CARD_BG,
                                     corner_radius=10, border_width=1,
                                     border_color=COLOR_CARD_BORDER)
        search_frame.pack(fill="x", padx=4, pady=(0, 8))

        ctk.CTkLabel(search_frame, text="🔍", font=ctk.CTkFont(size=13),
                     text_color=COLOR_TEXT_DIM).pack(side="left", padx=(8, 0))

        self.search_entry = ctk.CTkEntry(
            search_frame, height=34,
            placeholder_text="Search files...",
            fg_color="transparent", border_width=0,
            font=ctk.CTkFont(size=12),
            text_color=COLOR_TEXT_MAIN,
            placeholder_text_color=COLOR_TEXT_DIM
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(4, 8))
        self.search_entry.bind("<KeyRelease>", lambda e: self._filter_files())

        self.count_lbl = ctk.CTkLabel(search_frame, text="0 files",
                                       font=ctk.CTkFont(size=10),
                                       text_color=COLOR_TEXT_DIM)
        self.count_lbl.pack(side="right", padx=(0, 8))

        # ── File List ─────────────────────────────────────────────────────
        list_card = ctk.CTkFrame(self, fg_color=COLOR_CARD_BG,
                                  corner_radius=12, border_width=1,
                                  border_color=COLOR_CARD_BORDER)
        list_card.pack(fill="both", expand=True, padx=4, pady=(0, 8))

        self.file_list_frame = ctk.CTkScrollableFrame(list_card, fg_color="transparent")
        self.file_list_frame.pack(fill="both", expand=True, padx=8, pady=8)

        # Empty state
        self.empty_lbl = ctk.CTkLabel(
            self.file_list_frame,
            text="Select a folder above or click 'Load All' to browse files.",
            font=ctk.CTkFont(size=12),
            text_color=COLOR_TEXT_DIM
        )
        self.empty_lbl.pack(pady=40)

        # ── Download Action ───────────────────────────────────────────────
        action_card = ctk.CTkFrame(self, fg_color=COLOR_CARD_BG,
                                    corner_radius=12, border_width=1,
                                    border_color=COLOR_CARD_BORDER)
        action_card.pack(fill="x", padx=4, pady=(0, 6))

        action_inner = ctk.CTkFrame(action_card, fg_color="transparent")
        action_inner.pack(fill="x", padx=14, pady=12)

        action_row = ctk.CTkFrame(action_inner, fg_color="transparent")
        action_row.pack(fill="x")

        self.file_info_lbl = ctk.CTkLabel(
            action_row, text="No file selected",
            font=ctk.CTkFont(size=11),
            text_color=COLOR_TEXT_SUB
        )
        self.file_info_lbl.pack(side="left")

        self.download_btn = ctk.CTkButton(
            action_row,
            text="⬇ Download",
            width=120, height=34,
            corner_radius=8,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=COLOR_PRIMARY, hover_color="#4F46E5",
            text_color="#F4F4F5",
            state="disabled",
            command=self._download_file
        )
        self.download_btn.pack(side="right")

        # Progress
        self.progress_bar = ctk.CTkProgressBar(action_inner, height=6, corner_radius=3)
        self.progress_bar.pack(fill="x", pady=(8, 4))
        self.progress_bar.set(0)

        self.status_lbl = ctk.CTkLabel(action_inner, text="",
                                        font=ctk.CTkFont(size=10),
                                        text_color=COLOR_TEXT_SUB)
        self.status_lbl.pack(anchor="w")

    # ─── Public API ────────────────────────────────────────────────────────
    def load_folder(self, folder_name):
        """Load unencrypted files for a specific folder (called from sidebar)."""
        self._active_folder = folder_name
        self.folder_var.set(folder_name)
        self.status_lbl.configure(text=f"Scanning {folder_name} for unencrypted files...")
        self.queue_worker.submit_task(self._fetch_folder_files, folder_name)

    def set_preloaded_folders(self, folders):
        """Receive pre-loaded folder list from app."""
        if folders:
            self.folder_menu.configure(values=["— Select Folder —"] + sorted(folders))

    def on_task_update(self, status, result):
        if status == "success" and isinstance(result, dict):
            action = result.get("action")
            if action == "folders_for_files":
                folders = result.get("folders", [])
                if folders:
                    self.folder_menu.configure(values=["— Select Folder —"] + sorted(folders))
                self.status_lbl.configure(text=f"{len(folders)} folder(s) found")
            elif action == "all_files_loaded":
                self._display_files(result.get("files", []))
            elif action == "folder_files_loaded":
                self._display_files(result.get("files", []))
            elif action == "file_downloaded":
                self.status_lbl.configure(text=f"✓ Downloaded: {result.get('path', '')}",
                                          text_color=COLOR_SUCCESS)
                self.progress_bar.set(1.0)
                self.download_btn.configure(state="normal")
            elif action == "file_deleted":
                self.status_lbl.configure(
                    text=f"✓ Deleted {result.get('filename', '')}",
                    text_color=COLOR_SUCCESS
                )
                if self._active_folder:
                    self.load_folder(self._active_folder)
        elif status == "error":
            self.status_lbl.configure(text=f"Error: {result}",
                                      text_color=COLOR_ERROR)
            self.download_btn.configure(state="normal")

    # ─── Logic ─────────────────────────────────────────────────────────────
    def _refresh_files(self):
        self.status_lbl.configure(text="Loading folders...")
        self.queue_worker.submit_task(self._fetch_folders_for_files)

    def _fetch_folders_for_files(self):
        folders = self.storage.scan_user_folders()
        return {"action": "folders_for_files", "folders": folders}

    def _on_folder_select(self, choice):
        if choice and choice != "— Select Folder —" and choice != "Loading folders...":
            self._active_folder = choice
            self.status_lbl.configure(text=f"Scanning {choice}...")
            self.queue_worker.submit_task(self._fetch_folder_files, choice)

    def _load_all_files(self):
        self.status_lbl.configure(text="Scanning all folders...")
        self.queue_worker.submit_task(self._fetch_all_files)

    def _fetch_all_files(self):
        folders = self.storage.scan_user_folders()
        all_files = []
        for folder in folders:
            try:
                files = self.storage.get_files_unencrypted(folder)
                for f in files:
                    f["bucket"] = folder
                all_files.extend(files)
            except Exception:
                continue
        return {"action": "all_files_loaded", "files": all_files}

    def _fetch_folder_files(self, folder_name):
        files = self.storage.get_files_unencrypted(folder_name)
        for f in files:
            f["bucket"] = folder_name
        return {"action": "folder_files_loaded", "files": files}

    def _display_files(self, files):
        self._all_files = files
        self._filter_files()
        if self._active_folder:
            self.folder_var.set(self._active_folder)
        else:
            folders = list({f.get("bucket", "") for f in files})
            if folders:
                self.folder_menu.configure(values=["— Select Folder —"] + sorted(folders))

    def _filter_files(self):
        query = self.search_entry.get().lower()

        for widget in self.file_list_frame.winfo_children():
            widget.destroy()

        filtered = [f for f in self._all_files if not query or query in f["name"].lower()]
        self.count_lbl.configure(text=f"{len(filtered)} file(s)")

        if not filtered:
            empty_text = "No unencrypted files found." if self._all_files else "No files loaded yet."
            ctk.CTkLabel(
                self.file_list_frame, text=empty_text,
                font=ctk.CTkFont(size=12), text_color=COLOR_TEXT_DIM
            ).pack(pady=40)
            return

        for f in filtered:
            row = ctk.CTkFrame(self.file_list_frame, fg_color="#09090B",
                                corner_radius=8, border_width=1,
                                border_color=COLOR_CARD_BORDER)
            row.pack(fill="x", pady=(0, 4), padx=4)

            # File icon + name
            name_lbl = ctk.CTkLabel(
                row, text=f"📄  {f['name']}",
                font=ctk.CTkFont(size=11),
                text_color=COLOR_TEXT_MAIN,
                anchor="w"
            )
            name_lbl.pack(side="left", padx=10, pady=8)

            # Bucket badge
            bucket = f.get("bucket", "")
            if bucket:
                ctk.CTkLabel(
                    row, text=bucket,
                    font=ctk.CTkFont(size=9),
                    text_color=COLOR_TEXT_ACCENT,
                    fg_color=COLOR_CARD_BG,
                    corner_radius=4, padx=6, pady=2
                ).pack(side="right", padx=(0, 4))

            # Size
            size_str = f.get("size", "")
            if size_str:
                ctk.CTkLabel(
                    row, text=size_str,
                    font=ctk.CTkFont(size=10),
                    text_color=COLOR_TEXT_DIM
                ).pack(side="right", padx=8)

            # Delete button
            del_btn = ctk.CTkButton(
                row, text="🗑", width=30, height=24,
                corner_radius=6, fg_color="transparent",
                hover_color="#7F1D1D", text_color="#EF4444",
                command=lambda file=f: self._delete_file(file)
            )
            del_btn.pack(side="right", padx=(0, 4))

            # Select on click
            row.bind("<Button-1>", lambda e, file=f: self._select_file(file, row))
            name_lbl.bind("<Button-1>", lambda e, file=f, r=row: self._select_file(file, r))

    def _select_file(self, file, row_widget):
        self._selected_file = file
        self.file_info_lbl.configure(
            text=f"{file['name']}  •  {file.get('size', '?')}  •  {file.get('bucket', '')}",
            text_color=COLOR_TEXT_MAIN
        )
        self.download_btn.configure(state="normal")

        # Highlight selected row
        for widget in self.file_list_frame.winfo_children():
            if isinstance(widget, ctk.CTkFrame):
                widget.configure(border_color=COLOR_CARD_BORDER)
        row_widget.configure(border_color=COLOR_PRIMARY)

    def _delete_file(self, file):
        bucket = file.get("bucket", "")
        name = file["name"]
        if not bucket:
            return
        confirm = messagebox.askyesno(
            "Delete File",
            f"Delete '{name}' from {bucket}?\n\nThis cannot be undone."
        )
        if not confirm:
            return
        self.status_lbl.configure(text=f"Deleting {name}...")
        self.queue_worker.submit_task(self._process_delete, bucket, name)

    def _process_delete(self, bucket, filename):
        self.storage.delete_file(bucket, filename, encrypted=False)
        return {"action": "file_deleted", "filename": filename}

    def _download_file(self):
        if not self._selected_file:
            return

        file = self._selected_file
        bucket = file.get("bucket", "")
        name = file["name"]

        save_path = filedialog.asksaveasfilename(initialfile=name)
        if not save_path:
            return

        self.download_btn.configure(state="disabled")
        self.status_lbl.configure(text=f"Downloading {name}...")
        self.progress_bar.set(0)

        self.queue_worker.submit_task(
            self._download_file_task, bucket, name, save_path
        )

    def _download_file_task(self, bucket, filename, save_path):
        download_url = f"https://archive.org/download/{bucket}/{filename}"
        import requests
        response = requests.get(download_url, stream=True, timeout=30)
        if response.status_code != 200:
            raise Exception(f"Download failed: HTTP {response.status_code}")

        total = int(response.headers.get("content-length", 0))

        with open(save_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=4096):
                f.write(chunk)

        return {"action": "file_downloaded", "path": save_path}
