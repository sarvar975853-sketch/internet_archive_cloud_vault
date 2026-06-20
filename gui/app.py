import customtkinter as ctk
import threading
DND_SUPPORTED = False

from aegis_vault.core.credentials import CredentialManager
from aegis_vault.core.crypto import CryptoEngine
from aegis_vault.core.storage import IAStorageEngine
from aegis_vault.core.queue_worker import QueueWorker
from aegis_vault.utils.logger import logger
from aegis_vault.gui.theme import THEME

from aegis_vault.gui.login import LoginFrame
from aegis_vault.gui.dashboard import DashboardFrame
from aegis_vault.gui.sidebar import SidebarFrame
from aegis_vault.gui.upload import UploadFrame
from aegis_vault.gui.url_upload import URLUploadFrame
from aegis_vault.gui.explorer import ExplorerFrame
from aegis_vault.gui.files import FilesTab

COLOR_MAIN_BG  = "#09090B"
COLOR_CARD_BG  = "#18181B"
COLOR_NAV_BG   = "#09090B"
COLOR_NAV_SEL  = "#27272A"

class DnDWindow(ctk.CTk):
    pass


class AppGUI(DnDWindow):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("dark")

        self.title("Aegis Vault v2.0.0 – Modern Cloud Vault")
        self.geometry("1100x740")
        self.minsize(960, 640)

        self.configure(fg_color=(COLOR_MAIN_BG, COLOR_MAIN_BG))
        ctk.set_default_color_theme("blue")

        self.cred_manager  = CredentialManager()
        self.crypto_engine = CryptoEngine()

        self.storage_engine = None
        self.queue_worker   = None
        self._active_tab = 0
        self._preloaded_folders = None

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True)

        access, secret = self.cred_manager.load_credentials()
        if access and secret:
            self.start_session(access, secret)
        else:
            self.show_login()

    # ─── Auth ──────────────────────────────────────────────────────────────
    def show_login(self):
        self.clear_view()
        LoginFrame(self.container, self.start_session).pack(fill="both", expand=True)

    def start_session(self, access, secret):
        logger.info("Starting session...")
        self.storage_engine = IAStorageEngine(access, secret)
        self.queue_worker = QueueWorker(self.handle_queue_update, max_workers=6)

        # Preload folders in background, then show workspace
        self._preload_folders()

    def _preload_folders(self):
        """Fetch folders in background thread before building the GUI."""
        def _fetch():
            try:
                folders = self.storage_engine.scan_user_folders()
                self._preloaded_folders = folders
            except Exception as e:
                logger.error(f"Preload failed: {e}")
                self._preloaded_folders = []
            # Back on main thread — build workspace with pre-loaded data
            self.after(0, self.show_workspace)

        threading.Thread(target=_fetch, daemon=True).start()

    def clear_view(self):
        for widget in self.container.winfo_children():
            widget.destroy()

    # ─── Workspace ─────────────────────────────────────────────────────────
    def show_workspace(self):
        self.clear_view()

        self.container.grid_columnconfigure(0, weight=0)
        self.container.grid_columnconfigure(1, weight=1)
        self.container.grid_rowconfigure(0, weight=1)

        # ── Sidebar ──────────────────────────────────────────────────────
        self.sidebar = SidebarFrame(
            self.container, self.queue_worker, self.storage_engine,
            self.on_folder_selected, self.logout
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        # Inject pre-loaded folders into sidebar (no re-fetch needed)
        if self._preloaded_folders is not None:
            self.sidebar.inject_folders(self._preloaded_folders)

        # ── Main content area ─────────────────────────────────────────────
        main_area = ctk.CTkFrame(self.container, fg_color="transparent")
        main_area.grid(row=0, column=1, sticky="nsew")
        main_area.grid_rowconfigure(0, weight=0)
        main_area.grid_rowconfigure(1, weight=1)
        main_area.grid_columnconfigure(0, weight=1)

        # ── Top Navigation Bar ────────────────────────────────────────────
        top_bar = ctk.CTkFrame(main_area, fg_color="transparent", height=60)
        top_bar.grid(row=0, column=0, sticky="ew", padx=20, pady=(14, 0))
        top_bar.grid_propagate(False)
        top_bar.grid_columnconfigure(0, weight=1)

        nav_pill = ctk.CTkFrame(top_bar, fg_color="#18181B",
                                corner_radius=12, border_width=1,
                                border_color="#27272A", height=44)
        nav_pill.grid(row=0, column=0, sticky="")
        nav_pill.grid_propagate(False)

        self._tab_labels = [
            ("📊 Dashboard",   0),
            ("⬆ Upload Queue",  1),
            ("🌐 URL Upload",   2),
            ("📥 Explorer",     3),
            ("📂 Files",        4),
        ]

        self._nav_buttons = []
        for i, (label, idx) in enumerate(self._tab_labels):
            btn = ctk.CTkButton(
                nav_pill, text=label,
                height=36, corner_radius=9,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color="#27272A" if i == 0 else "transparent",
                hover_color="#18181B",
                text_color="#F4F4F5" if i == 0 else "#A1A1AA",
                command=lambda n=i: self._switch_tab(n)
            )
            btn.pack(side="left", padx=4, pady=4)
            self._nav_buttons.append(btn)

        # Right-side icons
        right_icons = ctk.CTkFrame(top_bar, fg_color="transparent")
        right_icons.grid(row=0, column=1, sticky="e", padx=(10, 0))

        settings_btn = ctk.CTkButton(
            right_icons, text="⚙️", width=36, height=36,
            corner_radius=8, font=ctk.CTkFont(size=16),
            fg_color="transparent", hover_color="#27272A",
            command=self._open_settings
        )
        settings_btn.pack(side="left", padx=4)

        ctk.CTkLabel(right_icons, text="🛡", font=ctk.CTkFont(size=22),
                     text_color="#6366F1").pack(side="left", padx=4)

        # ── Content Frame ─────────────────────────────────────────────────
        self.content_frame = ctk.CTkFrame(main_area, fg_color="transparent")
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=12)

        # Build all tab frames
        self.dashboard_tab = DashboardFrame(self.content_frame, on_navigate=self._switch_tab,
                                           storage_engine=self.storage_engine)
        self.upload_tab    = UploadFrame(self.content_frame, self.queue_worker,
                                          self.storage_engine, self.crypto_engine)
        self.url_upload_tab = URLUploadFrame(self.content_frame, self.queue_worker,
                                              self.storage_engine, self.crypto_engine)
        self.explorer_tab  = ExplorerFrame(self.content_frame, self.queue_worker,
                                            self.storage_engine, self.crypto_engine)
        self.files_tab     = FilesTab(self.content_frame, self.queue_worker,
                                       self.storage_engine)

        self._tab_frames = [
            self.dashboard_tab,
            self.upload_tab,
            self.url_upload_tab,
            self.explorer_tab,
            self.files_tab,
        ]

        # Inject pre-loaded folders into files tab
        if self._preloaded_folders is not None:
            self.files_tab.set_preloaded_folders(self._preloaded_folders)

        # Show dashboard by default
        self._tab_frames[0].pack(fill="both", expand=True)

        # Bind keyboard shortcuts
        self.bind("<Command-1>" if self._is_mac() else "<Control-1>", lambda e: self._switch_tab(0))
        self.bind("<Command-2>" if self._is_mac() else "<Control-2>", lambda e: self._switch_tab(1))
        self.bind("<Command-3>" if self._is_mac() else "<Control-3>", lambda e: self._switch_tab(2))
        self.bind("<Command-4>" if self._is_mac() else "<Control-4>", lambda e: self._switch_tab(3))
        self.bind("<Command-5>" if self._is_mac() else "<Control-5>", lambda e: self._switch_tab(4))
        self.bind("<Command-comma>" if self._is_mac() else "<Control-comma>", lambda e: self._open_settings())
        self.bind("<Command-r>" if self._is_mac() else "<Control-r>", lambda e: self.sidebar.refresh_folders())

    def _is_mac(self):
        import platform
        return platform.system() == "Darwin"

    def _switch_tab(self, index):
        if self._active_tab == index:
            return

        old_index = self._active_tab
        self._active_tab = index

        for i, btn in enumerate(self._nav_buttons):
            if i == index:
                btn.configure(fg_color="#27272A", text_color="#F4F4F5")
            else:
                btn.configure(fg_color="transparent", text_color="#A1A1AA")

        old_frame = self._tab_frames[old_index] if old_index < len(self._tab_frames) else None
        new_frame = self._tab_frames[index]

        if old_frame:
            old_frame.pack_forget()
        new_frame.pack(fill="both", expand=True)

    def _open_settings(self):
        from aegis_vault.gui.settings import SettingsWindow
        SettingsWindow(self, self.storage_engine, self.crypto_engine)

    # ─── Queue routing ─────────────────────────────────────────────────────
    def handle_queue_update(self, task_name, status, result):
        self.after(0, self._sync_handle_queue_update, task_name, status, result)

    def _sync_handle_queue_update(self, task_name, status, result):
        if task_name == "_fetch_folders":
            self.sidebar.on_task_update(status, result)
        elif task_name == "_process_single_upload":
            self.upload_tab.on_task_update(status, result)
        elif task_name == "_process_url_upload":
            self.url_upload_tab.on_task_update(status, result)
        elif task_name in ("_fetch_metadata", "_process_download", "_process_delete"):
            self.explorer_tab.on_task_update(status, result)
        elif task_name in ("_fetch_folders_for_files", "_fetch_all_files",
                           "_fetch_folder_files", "_download_file_task",
                           "_process_delete"):
            self.files_tab.on_task_update(status, result)

    def on_folder_selected(self, folder_name):
        self._switch_tab(3)
        self.explorer_tab.load_folder(folder_name)
        self.files_tab.load_folder(folder_name)

    def logout(self):
        logger.info("Logging out...")
        if self.queue_worker:
            self.queue_worker.stop()
        self.cred_manager.clear_credentials()
        self.show_login()

    def on_closing(self):
        if self.queue_worker:
            self.queue_worker.stop()
        self.destroy()
