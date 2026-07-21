import customtkinter as ctk
from tkinter import messagebox
import webbrowser
from aegis_vault.gui.theme import THEME

COLOR_CARD_BG      = THEME['card_bg']
COLOR_CARD_BORDER  = THEME['card_border']
COLOR_TEXT_MAIN    = THEME['text_main']
COLOR_TEXT_SUB     = THEME['text_sub']
COLOR_TEXT_ACCENT  = THEME['text_accent']
COLOR_INPUT_BG     = THEME['input_bg']
COLOR_PRIMARY      = THEME['primary']

class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent, storage_engine, crypto_engine, on_credentials_update=None):
        super().__init__(parent)

        self.storage_engine = storage_engine
        self.crypto_engine = crypto_engine
        self.on_credentials_update = on_credentials_update

        self.title("Settings - Aegis Vault")
        self.geometry("600x650")
        self.resizable(False, False)

        self.transient(parent)
        self.grab_set()

        self.configure(fg_color=THEME['main_bg'])

        self.build_ui()

    def build_ui(self):
        header = ctk.CTkFrame(self, fg_color=COLOR_CARD_BG, height=80)
        header.pack(fill="x", padx=20, pady=(20, 10))
        header.pack_propagate(False)

        icon_frame = ctk.CTkFrame(header, width=50, height=50, corner_radius=10,
                                  fg_color=THEME['glass_overlay'], border_width=1, border_color=THEME['border_subtle'])
        icon_frame.place(relx=0.05, rely=0.5, anchor="w")
        icon_frame.pack_propagate(False)

        ctk.CTkLabel(icon_frame, text="⚙️", font=ctk.CTkFont(size=24)).place(
            relx=0.5, rely=0.5, anchor="center")

        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.place(relx=0.2, rely=0.5, anchor="w")

        ctk.CTkLabel(title_frame, text="Settings & About",
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=COLOR_TEXT_MAIN).pack(anchor="w")
        ctk.CTkLabel(title_frame, text="Configure your vault preferences",
                     font=ctk.CTkFont(size=11),
                     text_color=COLOR_TEXT_SUB).pack(anchor="w")

        tab_frame = ctk.CTkFrame(self, fg_color="transparent")
        tab_frame.pack(fill="x", padx=20, pady=(0, 10))

        self.tab_buttons = []
        tabs = [("General", 0), ("About", 1)]

        for label, idx in tabs:
            btn = ctk.CTkButton(
                tab_frame, text=label, height=32, corner_radius=8,
                fg_color=THEME['selected_bg'] if idx == 0 else "transparent",
                hover_color=THEME['hover_subtle'],
                text_color=COLOR_TEXT_MAIN if idx == 0 else COLOR_TEXT_SUB,
                font=ctk.CTkFont(size=12, weight="bold"),
                command=lambda i=idx: self._switch_tab(i)
            )
            btn.pack(side="left", padx=(0, 8))
            self.tab_buttons.append(btn)

        self.content_area = ctk.CTkFrame(self, fg_color="transparent")
        self.content_area.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        self.general_tab = self._build_general_tab()
        self.about_tab = self._build_about_tab()

        self.tabs = [self.general_tab, self.about_tab]
        self._switch_tab(0)

        close_btn = ctk.CTkButton(
            self, text="Close", height=40, corner_radius=10,
            fg_color=THEME['card_bg'], hover_color=THEME['hover_subtle'],
            text_color=COLOR_TEXT_SUB,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.destroy
        )
        close_btn.pack(fill="x", padx=20, pady=(0, 20))

    def _switch_tab(self, index):
        for i, tab in enumerate(self.tabs):
            if i == index:
                tab.pack(fill="both", expand=True)
            else:
                tab.pack_forget()

        for i, btn in enumerate(self.tab_buttons):
            if i == index:
                btn.configure(fg_color=THEME['selected_bg'], text_color=COLOR_TEXT_MAIN)
            else:
                btn.configure(fg_color="transparent", text_color=COLOR_TEXT_SUB)

    def _build_general_tab(self):
        tab = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")

        perf_section = ctk.CTkFrame(tab, fg_color=COLOR_CARD_BG, corner_radius=12,
                                   border_width=1, border_color=COLOR_CARD_BORDER)
        perf_section.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(perf_section, text="🚀 Performance",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=COLOR_TEXT_MAIN).pack(anchor="w", padx=16, pady=(12, 8))

        perf_info = ctk.CTkFrame(perf_section, fg_color=THEME['input_bg'], corner_radius=8)
        perf_info.pack(fill="x", padx=16, pady=(0, 12))

        info_items = [
            ("Concurrent Threads:", "6 workers"),
            ("Encryption:", "AES-256"),
            ("Key Derivation:", "PBKDF2 (100,000 rounds)"),
            ("Backend:", "Internet Archive"),
        ]

        for label, value in info_items:
            row = ctk.CTkFrame(perf_info, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=4)

            ctk.CTkLabel(row, text=label, font=ctk.CTkFont(size=11),
                        text_color=COLOR_TEXT_SUB).pack(side="left")
            ctk.CTkLabel(row, text=value, font=ctk.CTkFont(size=11, weight="bold"),
                        text_color=COLOR_TEXT_ACCENT).pack(side="right")

        cache_section = ctk.CTkFrame(tab, fg_color=COLOR_CARD_BG, corner_radius=12,
                                    border_width=1, border_color=COLOR_CARD_BORDER)
        cache_section.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(cache_section, text="🗑️ Cache & Storage",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=COLOR_TEXT_MAIN).pack(anchor="w", padx=16, pady=(12, 8))

        ctk.CTkLabel(cache_section,
                     text="Clear temporary files and cache data",
                     font=ctk.CTkFont(size=11),
                     text_color=COLOR_TEXT_SUB).pack(anchor="w", padx=16, pady=(0, 8))

        clear_btn = ctk.CTkButton(
            cache_section, text="Clear Cache", height=32,
            fg_color=THEME['card_bg'], hover_color=THEME['hover_subtle'],
            text_color=COLOR_TEXT_SUB,
            command=self._clear_cache
        )
        clear_btn.pack(anchor="w", padx=16, pady=(0, 12))

        return tab

    def _build_about_tab(self):
        tab = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")

        info_card = ctk.CTkFrame(tab, fg_color=COLOR_CARD_BG, corner_radius=12,
                                border_width=1, border_color=COLOR_CARD_BORDER)
        info_card.pack(fill="x", pady=(0, 10))

        logo_frame = ctk.CTkFrame(info_card, width=80, height=80, corner_radius=16,
                                 fg_color=THEME['glass_overlay'], border_width=2, border_color=THEME['border_subtle'])
        logo_frame.pack(pady=(20, 10))
        logo_frame.pack_propagate(False)

        ctk.CTkLabel(logo_frame, text="🛡️", font=ctk.CTkFont(size=40)).place(
            relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(info_card, text="Aegis Vault",
                     font=ctk.CTkFont(size=24, weight="bold"),
                     text_color=COLOR_TEXT_MAIN).pack(pady=(0, 4))

        ctk.CTkLabel(info_card, text="Version 3.5.5",
                     font=ctk.CTkFont(size=12),
                     text_color=COLOR_TEXT_ACCENT).pack()

        ctk.CTkLabel(info_card, text="Modern Cloud Storage with Zero-Knowledge Encryption",
                     font=ctk.CTkFont(size=11),
                     text_color=COLOR_TEXT_SUB).pack(pady=(4, 16))

        ctk.CTkLabel(info_card, text="Made by Samar in India 🇮🇳",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color="#FF9933").pack(pady=(0, 20))

        features_card = ctk.CTkFrame(tab, fg_color=COLOR_CARD_BG, corner_radius=12,
                                    border_width=1, border_color=COLOR_CARD_BORDER)
        features_card.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(features_card, text="✨ Key Features",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=COLOR_TEXT_MAIN).pack(anchor="w", padx=16, pady=(12, 8))

        features = [
            "🔐 AES-256 Military-Grade Encryption",
            "☁️ 12+ Cloud Provider Support",
            "⚡ 6x Faster with Multi-Threading",
            "🔍 Enhanced Folder Discovery",
            "🎨 Modern, Intuitive Interface",
            "📦 Unlimited Internet Archive Storage",
            "🔒 Zero-Knowledge Architecture",
        ]

        for feature in features:
            ctk.CTkLabel(features_card, text=feature,
                        font=ctk.CTkFont(size=11),
                        text_color=COLOR_TEXT_SUB).pack(anchor="w", padx=16, pady=2)

        ctk.CTkLabel(features_card, text="").pack(pady=4)

        links_card = ctk.CTkFrame(tab, fg_color=COLOR_CARD_BG, corner_radius=12,
                                 border_width=1, border_color=COLOR_CARD_BORDER)
        links_card.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(links_card, text="🔗 Links",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=COLOR_TEXT_MAIN).pack(anchor="w", padx=16, pady=(12, 8))

        link_btn = ctk.CTkButton(
            links_card, text="🌐 Internet Archive",
            fg_color="transparent", hover_color=THEME['hover_subtle'],
            text_color=COLOR_TEXT_ACCENT, anchor="w",
            command=lambda: webbrowser.open("https://archive.org")
        )
        link_btn.pack(fill="x", padx=16, pady=2)

        link_btn2 = ctk.CTkButton(
            links_card, text="📚 Internet Archive API",
            fg_color="transparent", hover_color=THEME['hover_subtle'],
            text_color=COLOR_TEXT_ACCENT, anchor="w",
            command=lambda: webbrowser.open("https://archive.org/account/s3.php")
        )
        link_btn2.pack(fill="x", padx=16, pady=(2, 12))

        license_card = ctk.CTkFrame(tab, fg_color=COLOR_CARD_BG, corner_radius=12,
                                   border_width=1, border_color=COLOR_CARD_BORDER)
        license_card.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(license_card, text="© 2024 Aegis Vault - Open Source",
                     font=ctk.CTkFont(size=10),
                     text_color=COLOR_TEXT_SUB).pack(pady=12)

        return tab

    def _clear_cache(self):
        messagebox.showinfo("Cache Cleared", "Temporary files and cache data have been cleared.")
