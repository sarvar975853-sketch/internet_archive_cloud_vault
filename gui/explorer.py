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
COLOR_SUCCESS      = THEME['success']
COLOR_ERROR        = THEME['error']
COLOR_PRIMARY      = THEME['primary']


class ExplorerFrame(ctk.CTkFrame):
    def __init__(self, master, queue_worker, storage_engine, crypto_engine):
        super().__init__(master, fg_color="transparent")
        self.queue_worker = queue_worker
        self.storage = storage_engine
        self.crypto = crypto_engine
        self.active_folder = ""
        self.files_cache = []
        self._selected_files = {}
        self._batch_total = 0
        self._batch_done = 0
        self._password_mode = "same"

        self.build_ui()

    def build_ui(self):
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.pack(fill="x", padx=4, pady=(4, 8))

        self.folder_title = ctk.CTkLabel(
            top_bar,
            text="📂  Select a folder from the sidebar",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=COLOR_TEXT_DIM
        )
        self.folder_title.pack(side="left")

        search_frame = ctk.CTkFrame(top_bar, fg_color=COLOR_CARD_BG,
                                     corner_radius=10, border_width=1,
                                     border_color=COLOR_CARD_BORDER)
        search_frame.pack(side="right")

        ctk.CTkLabel(search_frame, text="🔍", font=ctk.CTkFont(size=13),
                     text_color=COLOR_TEXT_DIM).pack(side="left", padx=(8, 0))

        self.search_entry = ctk.CTkEntry(
            search_frame, width=200, height=34,
            placeholder_text="Search files...",
            fg_color="transparent", border_width=0,
            font=ctk.CTkFont(size=12),
            text_color=COLOR_TEXT_MAIN,
            placeholder_text_color=COLOR_TEXT_DIM
        )
        self.search_entry.pack(side="left", padx=(4, 8))
        self.search_entry.bind("<KeyRelease>", self.filter_files)

        list_card = ctk.CTkFrame(self, fg_color=COLOR_CARD_BG,
                                  corner_radius=12, border_width=1,
                                  border_color=COLOR_CARD_BORDER)
        list_card.pack(fill="both", expand=True, padx=4, pady=(0, 8))

        self.file_list_frame = ctk.CTkScrollableFrame(list_card, fg_color="transparent")
        self.file_list_frame.pack(fill="both", expand=True, padx=8, pady=8)

        select_all_frame = ctk.CTkFrame(self.file_list_frame, fg_color="transparent")
        select_all_frame.pack(fill="x", pady=(0, 6))

        self._select_all_var = ctk.BooleanVar(value=False)
        self.select_all_cb = ctk.CTkCheckBox(
            select_all_frame, text="Select All",
            variable=self._select_all_var,
            command=self._toggle_select_all,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLOR_TEXT_MAIN,
            fg_color=COLOR_PRIMARY,
            hover_color=THEME['accent_violet']
        )
        self.select_all_cb.pack(side="left")

        self._selected_count_lbl = ctk.CTkLabel(
            select_all_frame, text="0 selected",
            font=ctk.CTkFont(size=10), text_color=COLOR_TEXT_DIM
        )
        self._selected_count_lbl.pack(side="right")

        action_card = ctk.CTkFrame(self, fg_color=COLOR_CARD_BG,
                                    corner_radius=12, border_width=1,
                                    border_color=COLOR_CARD_BORDER)
        action_card.pack(fill="x", padx=4, pady=(0, 6))

        action_inner = ctk.CTkFrame(action_card, fg_color="transparent")
        action_inner.pack(fill="x", padx=14, pady=12)
        action_inner.grid_columnconfigure(0, weight=1)

        mode_row = ctk.CTkFrame(action_inner, fg_color="transparent")
        mode_row.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(mode_row, text="Password Mode:",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=COLOR_TEXT_MAIN).pack(side="left")

        self._password_mode_var = ctk.StringVar(value="same")
        self.same_pass_rb = ctk.CTkRadioButton(
            mode_row, text="Same for all",
            variable=self._password_mode_var, value="same",
            command=self._on_password_mode_change,
            font=ctk.CTkFont(size=11),
            text_color=COLOR_TEXT_MAIN,
            fg_color=COLOR_PRIMARY
        )
        self.same_pass_rb.pack(side="left", padx=(12, 0))

        self.diff_pass_rb = ctk.CTkRadioButton(
            mode_row, text="Different per file",
            variable=self._password_mode_var, value="different",
            command=self._on_password_mode_change,
            font=ctk.CTkFont(size=11),
            text_color=COLOR_TEXT_MAIN,
            fg_color=COLOR_PRIMARY
        )
        self.diff_pass_rb.pack(side="left", padx=(12, 0))

        self._mode_hint = ctk.CTkLabel(
            mode_row, text="",
            font=ctk.CTkFont(size=9), text_color=COLOR_TEXT_DIM
        )
        self._mode_hint.pack(side="left", padx=(8, 0))

        action_row = ctk.CTkFrame(action_inner, fg_color="transparent")
        action_row.pack(fill="x", pady=(0, 8))

        self.dl_pass_entry = ctk.CTkEntry(
            action_row, height=38,
            placeholder_text="🔑  Enter Matching Password to Unlock",
            show="•", font=ctk.CTkFont(size=12),
            fg_color=COLOR_INPUT_BG, border_color=THEME['border_subtle'],
            border_width=1, corner_radius=10,
            text_color=COLOR_TEXT_MAIN, placeholder_text_color=COLOR_TEXT_DIM
        )
        self.dl_pass_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.download_btn = ctk.CTkButton(
            action_row,
            text="🔓  Fetch & Decrypt",
            width=180, height=38,
            corner_radius=10,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=COLOR_PRIMARY, hover_color=THEME['accent_violet'],
            command=self.start_download
        )
        self.download_btn.pack(side="left")
        apply_bubble_hover(self.download_btn, glow_color=COLOR_PRIMARY)

        self.progress_bar = ctk.CTkProgressBar(
            action_inner, height=6, corner_radius=3,
            progress_color=COLOR_PRIMARY, fg_color=COLOR_INPUT_BG
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
        self._selected_files.clear()
        self._select_all_var.set(False)
        self._update_selected_count()
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

        select_all_frame = ctk.CTkFrame(self.file_list_frame, fg_color="transparent")
        select_all_frame.pack(fill="x", pady=(0, 6))

        self._select_all_var.set(False)
        self.select_all_cb = ctk.CTkCheckBox(
            select_all_frame, text="Select All",
            variable=self._select_all_var,
            command=self._toggle_select_all,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLOR_TEXT_MAIN,
            fg_color=COLOR_PRIMARY,
            hover_color=THEME['accent_violet']
        )
        self.select_all_cb.pack(side="left")

        self._selected_count_lbl = ctk.CTkLabel(
            select_all_frame, text=f"{len(self._selected_files)} selected",
            font=ctk.CTkFont(size=10), text_color=COLOR_TEXT_DIM
        )
        self._selected_count_lbl.pack(side="right")

        if not self.files_cache:
            ctk.CTkLabel(
                self.file_list_frame,
                text="No files found in this folder.",
                font=ctk.CTkFont(size=12),
                text_color=COLOR_TEXT_DIM
            ).pack(pady=30)
            return

        displayed_count = 0
        for f in self.files_cache:
            name = f['name']
            if query and query not in name.lower():
                continue

            displayed_count += 1
            row = ctk.CTkFrame(self.file_list_frame, fg_color=THEME['input_bg'],
                                corner_radius=8, border_width=1,
                                border_color=COLOR_CARD_BORDER)
            row.pack(fill="x", pady=(0, 4), padx=4)

            is_checked = name in self._selected_files
            cb_var = ctk.BooleanVar(value=is_checked)
            cb = ctk.CTkCheckBox(
                row,
                text=f"📄  {name}",
                variable=cb_var,
                font=ctk.CTkFont(size=11),
                text_color=COLOR_TEXT_MAIN,
                fg_color=COLOR_PRIMARY,
                hover_color=THEME['accent_violet'],
                command=lambda n=name, v=cb_var: self._toggle_file(n, v)
            )
            cb.pack(side="left", anchor="w", padx=10, pady=8)

            size_str = f.get('size', 'Unknown')
            ctk.CTkLabel(row, text=size_str,
                         font=ctk.CTkFont(size=10), text_color=COLOR_TEXT_DIM).pack(
                side="right", padx=10
            )

            copy_btn = ctk.CTkButton(
                row, text="📋", width=30, height=24,
                corner_radius=6, fg_color="transparent",
                hover_color=THEME['hover_subtle'], text_color=COLOR_TEXT_SUB,
                command=lambda n=name: self._copy_filename(n)
            )
            copy_btn.pack(side="right", padx=(0, 4))

            del_btn = ctk.CTkButton(
                row, text="🗑", width=30, height=24,
                corner_radius=6, fg_color="transparent",
                hover_color="#7F1D1D", text_color=COLOR_ERROR,
                command=lambda n=name: self._delete_file(n)
            )
            del_btn.pack(side="right", padx=(0, 4))

        if query and displayed_count == 0:
            ctk.CTkLabel(
                self.file_list_frame,
                text=f"No files match '{query}'",
                font=ctk.CTkFont(size=12),
                text_color=COLOR_TEXT_DIM
            ).pack(pady=30)

    def _toggle_file(self, name, var):
        if var.get():
            self._selected_files[name] = True
        else:
            self._selected_files.pop(name, None)
        self._update_selected_count()

    def _toggle_select_all(self):
        if self._select_all_var.get():
            for f in self.files_cache:
                self._selected_files[f['name']] = True
        else:
            self._selected_files.clear()
        self.filter_files()

    def _update_selected_count(self):
        count = len(self._selected_files)
        if hasattr(self, '_selected_count_lbl') and self._selected_count_lbl:
            self._selected_count_lbl.configure(text=f"{count} selected")
        if count > 0:
            self.download_btn.configure(text=f"🔓  Fetch & Decrypt ({count})")
        else:
            self.download_btn.configure(text="🔓  Fetch & Decrypt")

    def _on_password_mode_change(self):
        mode = self._password_mode_var.get()
        self._password_mode = mode
        if mode == "same":
            self.dl_pass_entry.configure(
                placeholder_text="🔑  Enter Matching Password to Unlock",
                state="normal"
            )
            self._mode_hint.configure(text="")
        else:
            self.dl_pass_entry.configure(
                placeholder_text="🔑  (will prompt for each file)",
                state="disabled"
            )
            self._mode_hint.configure(text="(you'll be prompted for each password)")

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
        selected = list(self._selected_files.keys())
        password = self.dl_pass_entry.get()

        if not selected or not self.active_folder:
            messagebox.showerror("Error", "Select at least one file to download.")
            return

        if self._password_mode == "same" and not password:
            messagebox.showerror("Error", "Enter a password to decrypt the files.")
            return

        save_dir = filedialog.askdirectory(title="Select download folder")
        if not save_dir:
            return

        self.download_btn.configure(state="disabled")
        self._batch_total = len(selected)
        self._batch_done = 0
        self.progress_bar.set(0)
        self.status_lbl.configure(text=f"Queued {len(selected)} file(s) for download...")

        if self._password_mode == "same":
            for filename in selected:
                save_path = os.path.join(save_dir, filename.replace(".enc", ""))
                self.queue_worker.submit_task(
                    self._download_encrypted, self.active_folder, filename, password, save_path
                )
        else:
            for filename in selected:
                save_path = os.path.join(save_dir, filename.replace(".enc", ""))
                self.queue_worker.submit_task(
                    self._download_encrypted_diff, self.active_folder, filename, save_path
                )

    def _download_encrypted(self, bucket, filename, password, save_path):
        temp_enc_path = save_path + ".enc.tmp"
        result = self.storage.download_file(bucket, filename, temp_enc_path, None)
        speed = result.get('speed_bps', 0) / 1024 / 1024 if isinstance(result, dict) and result.get('speed_bps') else 0

        try:
            self.crypto.decrypt_file(temp_enc_path, password, save_path)
            return {"action": "download_complete", "msg": f"Successfully decrypted {filename}", "speed_mbps": speed}
        finally:
            if os.path.exists(temp_enc_path):
                os.remove(temp_enc_path)

    def _download_encrypted_diff(self, bucket, filename, save_path):
        temp_enc_path = save_path + ".enc.tmp"
        password = self._prompt_password(filename)

        if not password:
            return {"action": "download_skipped", "msg": f"Skipped {filename} (no password)"}

        result = self.storage.download_file(bucket, filename, temp_enc_path, None)
        speed = result.get('speed_bps', 0) / 1024 / 1024 if isinstance(result, dict) and result.get('speed_bps') else 0

        try:
            self.crypto.decrypt_file(temp_enc_path, password, save_path)
            return {"action": "download_complete", "msg": f"Successfully decrypted {filename}", "speed_mbps": speed}
        finally:
            if os.path.exists(temp_enc_path):
                os.remove(temp_enc_path)

    def _prompt_password(self, filename):
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Password for {filename}")
        dialog.geometry("420x200")
        dialog.configure(fg_color=THEME['main_bg'])
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        dialog.resizable(False, False)

        result = {"password": None}

        ctk.CTkLabel(
            dialog, text=f"🔑  Enter password for:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLOR_TEXT_MAIN
        ).pack(pady=(20, 4))

        ctk.CTkLabel(
            dialog, text=filename,
            font=ctk.CTkFont(size=11),
            text_color=COLOR_TEXT_ACCENT,
            wraplength=380
        ).pack(pady=(0, 12))

        pass_entry = ctk.CTkEntry(
            dialog, height=38, show="•",
            placeholder_text="Password",
            fg_color=THEME['card_bg'], border_color=THEME['border_subtle'],
            border_width=1, corner_radius=10,
            font=ctk.CTkFont(size=12),
            text_color=COLOR_TEXT_MAIN
        )
        pass_entry.pack(padx=20, fill="x")
        pass_entry.focus_set()

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=16)

        def on_ok():
            result["password"] = pass_entry.get()
            dialog.destroy()

        def on_cancel():
            dialog.destroy()

        ctk.CTkButton(
            btn_frame, text="Download", width=100, height=34,
            corner_radius=8, fg_color=COLOR_PRIMARY, hover_color=THEME['accent_violet'],
            font=ctk.CTkFont(size=12, weight="bold"),
            command=on_ok
        ).pack(side="left", padx=6)

        ctk.CTkButton(
            btn_frame, text="Skip", width=80, height=34,
            corner_radius=8, fg_color=THEME['card_bg'], hover_color=THEME['hover_subtle'],
            font=ctk.CTkFont(size=12),
            text_color=COLOR_TEXT_SUB,
            command=on_cancel
        ).pack(side="left", padx=6)

        pass_entry.bind("<Return>", lambda e: on_ok())
        dialog.wait_window()
        return result["password"]

    def on_task_update(self, status, result):
        if status == "success":
            if isinstance(result, dict):
                action = result.get("action")
                if action == "metadata_loaded":
                    self.populate_list(result.get("files", []))
                elif action == "download_complete":
                    self._batch_done += 1
                    pct = self._batch_done / self._batch_total if self._batch_total else 1
                    self.progress_bar.set(pct)
                    speed = result.get('speed_mbps', 0)
                    speed_str = f" @ {speed:.1f} MB/s" if speed > 0 else ""
                    self.status_lbl.configure(
                        text=f"✓ {result.get('msg', '')}  ({self._batch_done}/{self._batch_total}){speed_str}",
                        text_color=COLOR_SUCCESS
                    )
                    if self._batch_done >= self._batch_total:
                        self.download_btn.configure(state="normal")
                        self.status_lbl.configure(
                            text=f"✓ All {self._batch_total} file(s) downloaded!",
                            text_color=COLOR_SUCCESS
                        )
                elif action == "download_skipped":
                    self._batch_done += 1
                    pct = self._batch_done / self._batch_total if self._batch_total else 1
                    self.progress_bar.set(pct)
                    self.status_lbl.configure(
                        text=f"⏭ {result.get('msg', '')}  ({self._batch_done}/{self._batch_total})",
                        text_color=COLOR_TEXT_SUB
                    )
                    if self._batch_done >= self._batch_total:
                        self.download_btn.configure(state="normal")
                elif action == "file_deleted":
                    self.status_lbl.configure(
                        text=f"✓ Deleted {result.get('filename', '')}",
                        text_color=COLOR_SUCCESS
                    )
                    if self.active_folder:
                        self.load_folder(self.active_folder)
        elif status == "error":
            self._batch_done += 1
            err_text = result if isinstance(result, str) else str(result)
            self.status_lbl.configure(text=f"Error: {err_text}", text_color=COLOR_ERROR)
            if self._batch_done >= self._batch_total:
                self.download_btn.configure(state="normal")
