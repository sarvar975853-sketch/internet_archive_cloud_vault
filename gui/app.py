import customtkinter as ctk
DND_SUPPORTED = False

from aegis_vault.core.credentials import CredentialManager
from aegis_vault.core.crypto import CryptoEngine
from aegis_vault.core.storage import IAStorageEngine
from aegis_vault.core.queue_worker import QueueWorker
from aegis_vault.utils.logger import logger
from aegis_vault.gui.theme import THEME
from aegis_vault.gui.hover import apply_bubble_hover

COLOR_MAIN_BG  = THEME['main_bg']
COLOR_CARD_BG  = THEME['card_bg']
COLOR_NAV_BG   = THEME['nav_bg']
COLOR_NAV_SEL  = THEME['nav_selected']

class DnDWindow(ctk.CTk):
    pass


class AppGUI(DnDWindow):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("dark")

        self.title("Aegis Vault")
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

    def show_login(self):
        self.clear_view()
        from aegis_vault.gui.login import LoginFrame
        LoginFrame(self.container, self.start_session).pack(fill="both", expand=True)

    def start_session(self, access, secret):
        logger.info("Starting session...")
        self.storage_engine = IAStorageEngine(access, secret)
        self.queue_worker = QueueWorker(self.handle_queue_update, max_workers=6)

        # scan_user_folders() returns instantly from local cache
        self._preloaded_folders = self.storage_engine.scan_user_folders()
        self.show_workspace()

    def clear_view(self):
        for widget in self.container.winfo_children():
            widget.destroy()

    def show_workspace(self):
        self.clear_view()

        from aegis_vault.gui.sidebar import SidebarFrame
        self.sidebar = SidebarFrame(
            self.container, self.queue_worker, self.storage_engine,
            self.on_folder_selected, self.logout
        )
        self.sidebar.pack(side="left", fill="y")

        if self._preloaded_folders is not None:
            self.sidebar.inject_folders(self._preloaded_folders)

        main_area = ctk.CTkFrame(self.container, fg_color="transparent")
        main_area.pack(side="left", fill="both", expand=True)

        top_bar = ctk.CTkFrame(main_area, fg_color="transparent", height=60)
        top_bar.pack(fill="x", padx=20, pady=(14, 0))
        top_bar.pack_propagate(False)

        nav_pill = ctk.CTkFrame(top_bar, fg_color=THEME['glass_overlay'],
                                corner_radius=12, border_width=1,
                                border_color=THEME['border_subtle'])
        nav_pill.pack(side="left", ipadx=4, ipady=4)

        self._tab_labels = [
            ("📊 Dashboard",   0),
            ("⬆ Upload Queue",  1),
            ("🌐 URL Upload",   2),
            ("📥 Explorer",     3),
            ("📂 Files",        4),
        ]

        self._nav_buttons = []
        for i, (label, idx) in enumerate(self._tab_labels):
            is_selected = (i == 0)
            btn = ctk.CTkButton(
                nav_pill, text=label,
                height=34, corner_radius=9,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color=THEME['primary'] if is_selected else "transparent",
                hover_color=THEME['secondary'] if is_selected else THEME['hover_subtle'],
                text_color="#1A1200" if is_selected else THEME['text_sub'],
                command=lambda n=i: self._switch_tab(n)
            )
            btn.pack(side="left", padx=3, pady=4)
            self._nav_buttons.append(btn)

        right_icons = ctk.CTkFrame(top_bar, fg_color="transparent")
        right_icons.pack(side="right", padx=(10, 0))

        settings_btn = ctk.CTkButton(
            right_icons, text="⚙️", width=36, height=36,
            corner_radius=8, font=ctk.CTkFont(size=16),
            fg_color="transparent", hover_color=THEME['hover_subtle'],
            command=self._open_settings
        )
        settings_btn.pack(side="left", padx=4)
        apply_bubble_hover(settings_btn, glow_color=THEME['primary'])

        ctk.CTkLabel(right_icons, text="🛡", font=ctk.CTkFont(size=22),
                     text_color=THEME['accent_indigo']).pack(side="left", padx=4)

        self.content_frame = ctk.CTkFrame(main_area, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=12)

        from aegis_vault.gui.dashboard import DashboardFrame
        dashboard_tab = DashboardFrame(self.content_frame, on_navigate=self._switch_tab,
                                       storage_engine=self.storage_engine,
                                       folders=self._preloaded_folders)
        self._tab_frames = [dashboard_tab, None, None, None, None]

        self._tab_frames[0].pack(fill="both", expand=True)

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
                btn.configure(fg_color=THEME['primary'],
                              hover_color=THEME['secondary'],
                              text_color="#1A1200")
            else:
                btn.configure(fg_color="transparent",
                              hover_color=THEME['hover_subtle'],
                              text_color=THEME['text_sub'])

        old_frame = self._tab_frames[old_index] if old_index < len(self._tab_frames) else None

        self._ensure_tab(index)

        new_frame = self._tab_frames[index]

        if old_frame:
            old_frame.pack_forget()
        new_frame.pack(fill="both", expand=True)

    def _ensure_tab(self, index):
        if self._tab_frames[index] is not None:
            return
        if index == 1:
            from aegis_vault.gui.upload import UploadFrame
            self._tab_frames[index] = UploadFrame(self.content_frame, self.queue_worker, self.storage_engine, self.crypto_engine)
        elif index == 2:
            from aegis_vault.gui.url_upload import URLUploadFrame
            self._tab_frames[index] = URLUploadFrame(self.content_frame, self.queue_worker, self.storage_engine, self.crypto_engine)
        elif index == 3:
            from aegis_vault.gui.explorer import ExplorerFrame
            self._tab_frames[index] = ExplorerFrame(self.content_frame, self.queue_worker, self.storage_engine, self.crypto_engine)
            if self._tab_frames[4] is None:
                from aegis_vault.gui.files import FilesTab
                self._tab_frames[4] = FilesTab(self.content_frame, self.queue_worker, self.storage_engine)
        elif index == 4:
            from aegis_vault.gui.files import FilesTab
            self._tab_frames[index] = FilesTab(self.content_frame, self.queue_worker, self.storage_engine)

    def _open_settings(self):
        from aegis_vault.gui.settings import SettingsWindow
        SettingsWindow(self, self.storage_engine, self.crypto_engine)

    def handle_queue_update(self, task_name, status, result):
        self.after(0, self._sync_handle_queue_update, task_name, status, result)

    def _sync_handle_queue_update(self, task_name, status, result):
        if task_name in ("_process_single_upload",):
            if self._tab_frames[1] is None:
                self._ensure_tab(1)
            self._tab_frames[1].on_task_update(status, result)
        elif task_name == "_process_url_upload":
            if self._tab_frames[2] is None:
                self._ensure_tab(2)
            self._tab_frames[2].on_task_update(status, result)
        elif task_name in ("_fetch_metadata", "_download_encrypted",
                           "_download_encrypted_diff", "_process_delete_encrypted"):
            if self._tab_frames[3] is None:
                self._ensure_tab(3)
            self._tab_frames[3].on_task_update(status, result)
        elif task_name in ("_fetch_files", "_download_plain", "_process_delete_unencrypted"):
            if self._tab_frames[4] is None:
                self._ensure_tab(4)
            self._tab_frames[4].on_task_update(status, result)

    def on_folder_selected(self, folder_name):
        self._switch_tab(3)
        explorer = self._tab_frames[3]
        files = self._tab_frames[4]
        if explorer:
            explorer.load_folder(folder_name)
        if files:
            files.load_folder(folder_name)

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
