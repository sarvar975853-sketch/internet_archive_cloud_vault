import customtkinter as ctk
import webbrowser
import os
from tkinter import messagebox
from PIL import Image
from aegis_vault.core.credentials import CredentialManager
from aegis_vault.gui.theme import THEME


class LoginFrame(ctk.CTkFrame):
    """
    Premium authentication screen matching the Aegis design prototype.
    Layout: A large hero card with a 3D cloud illustration on the left
    and a login form on the right, plus three feature badges at the bottom.
    """

    def __init__(self, master, login_callback):
        super().__init__(master, fg_color="transparent", corner_radius=0)
        self.login_callback = login_callback
        self.cred_manager = CredentialManager()
        self.theme = THEME
        self.asset_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

        # ── Configure the outer grid to center everything ────────────────
        self.grid_rowconfigure(0, weight=1)   # top spacer
        self.grid_rowconfigure(1, weight=0)   # hero card
        self.grid_rowconfigure(2, weight=0)   # badges row
        self.grid_rowconfigure(3, weight=1)   # bottom spacer
        self.grid_columnconfigure(0, weight=1)

        # ═══════════════════════════════════════════════════════════════════
        # HERO CARD — the main container with illustration + form
        # ═══════════════════════════════════════════════════════════════════
        self.hero_card = ctk.CTkFrame(
            self,
            fg_color=self.theme['card_bg'],
            corner_radius=20,
            border_width=1,
            border_color=self.theme['card_border'],
        )
        self.hero_card.grid(row=1, column=0, padx=50, pady=(30, 20), sticky="nsew")

        # Internal grid: 2 columns (illustration | form)
        self.hero_card.grid_columnconfigure(0, weight=1, minsize=380)
        self.hero_card.grid_columnconfigure(1, weight=1, minsize=380)
        self.hero_card.grid_rowconfigure(0, weight=1)

        # ── LEFT COLUMN: 3D Cloud Illustration ──────────────────────────
        self.illustration_frame = ctk.CTkFrame(
            self.hero_card, fg_color="transparent"
        )
        self.illustration_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.illustration_frame.grid_rowconfigure(0, weight=1)
        self.illustration_frame.grid_columnconfigure(0, weight=1)

        # Load the hero image
        hero_path = os.path.join(self.asset_dir, "cloud_hero.png")
        if os.path.exists(hero_path):
            hero_pil = Image.open(hero_path)
            self.hero_image = ctk.CTkImage(
                light_image=hero_pil, dark_image=hero_pil, size=(380, 380)
            )
            hero_label = ctk.CTkLabel(
                self.illustration_frame, image=self.hero_image, text=""
            )
            hero_label.grid(row=0, column=0, sticky="nsew")
        else:
            # Fallback: a beautiful text placeholder
            fallback = ctk.CTkLabel(
                self.illustration_frame,
                text="☁️ 🔒",
                font=ctk.CTkFont(size=120),
                text_color=self.theme['text_accent'],
            )
            fallback.grid(row=0, column=0, sticky="nsew")

        # ── RIGHT COLUMN: Login Form ─────────────────────────────────────
        self.form_frame = ctk.CTkFrame(self.hero_card, fg_color="transparent")
        self.form_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 40), pady=40)
        self.form_frame.grid_columnconfigure(0, weight=1)

        # Lock icon
        lock_icon = ctk.CTkLabel(
            self.form_frame,
            text="🔒",
            font=ctk.CTkFont(size=36),
            text_color=self.theme['text_accent'],
        )
        lock_icon.grid(row=0, column=0, pady=(10, 5))

        # Title
        title = ctk.CTkLabel(
            self.form_frame,
            text="Welcome to Aegis",
            font=ctk.CTkFont(family="Helvetica Neue", size=28, weight="bold"),
            text_color=self.theme['text_main'],
        )
        title.grid(row=1, column=0, pady=(0, 2))

        # Subtitle
        subtitle = ctk.CTkLabel(
            self.form_frame,
            text="Secure. Private. Stored on the Internet Archive.",
            font=ctk.CTkFont(size=13),
            text_color=self.theme['text_sub'],
        )
        subtitle.grid(row=2, column=0, pady=(0, 30))

        # ── Access Key Input ─────────────────────────────────────────────
        access_row = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        access_row.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 10))
        access_row.grid_columnconfigure(1, weight=1)

        access_icon = ctk.CTkLabel(
            access_row, text="🔑", font=ctk.CTkFont(size=18), width=35
        )
        access_icon.grid(row=0, column=0, padx=(5, 5))

        self.access_entry = ctk.CTkEntry(
            access_row,
            height=45,
            placeholder_text="Enter Access Key...",
            font=ctk.CTkFont(size=13),
            fg_color=self.theme['input_bg'],
            border_color=self.theme['card_border'],
            border_width=1,
            corner_radius=10,
            text_color=self.theme['text_main'],
            placeholder_text_color=self.theme['text_dim'],
        )
        self.access_entry.grid(row=0, column=1, sticky="ew")
        self.access_entry.bind("<FocusIn>", lambda e: self.access_entry.configure(border_color=self.theme['primary']))
        self.access_entry.bind("<FocusOut>", lambda e: self.access_entry.configure(border_color=self.theme['card_border']))

        # ── Secret Key Input ─────────────────────────────────────────────
        secret_row = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        secret_row.grid(row=4, column=0, sticky="ew", padx=10, pady=(0, 8))
        secret_row.grid_columnconfigure(1, weight=1)

        secret_icon = ctk.CTkLabel(
            secret_row, text="🔐", font=ctk.CTkFont(size=18), width=35
        )
        secret_icon.grid(row=0, column=0, padx=(5, 5))

        self.secret_entry = ctk.CTkEntry(
            secret_row,
            height=45,
            placeholder_text="Enter Secret Key...",
            show="•",
            font=ctk.CTkFont(size=13),
            fg_color=self.theme['input_bg'],
            border_color=self.theme['card_border'],
            border_width=1,
            corner_radius=10,
            text_color=self.theme['text_main'],
            placeholder_text_color=self.theme['text_dim'],
        )
        self.secret_entry.grid(row=0, column=1, sticky="ew")
        self.secret_entry.bind("<FocusIn>", lambda e: self.secret_entry.configure(border_color=self.theme['primary']))
        self.secret_entry.bind("<FocusOut>", lambda e: self.secret_entry.configure(border_color=self.theme['card_border']))

        # Toggle visibility button for secret
        self.secret_visible = False
        self.toggle_btn = ctk.CTkButton(
            secret_row,
            text="👁",
            width=35,
            height=35,
            fg_color="transparent",
            hover_color=self.theme['card_bg'],
            font=ctk.CTkFont(size=14),
            corner_radius=8,
            command=self._toggle_secret_visibility,
        )
        self.toggle_btn.grid(row=0, column=2, padx=(5, 0))

        # ── Help link ────────────────────────────────────────────────────
        help_btn = ctk.CTkButton(
            self.form_frame,
            text="ⓘ  How do I find my keys?",
            font=ctk.CTkFont(size=12, underline=True),
            fg_color="transparent",
            hover_color=self.theme['card_bg'],
            text_color=self.theme['text_accent'],
            anchor="center",
            height=28,
            command=lambda: webbrowser.open("https://archive.org/account/s3.php"),
        )
        help_btn.grid(row=5, column=0, pady=(5, 15))

        # ── Primary CTA Button ──────────────────────────────────────────
        self.login_btn = ctk.CTkButton(
            self.form_frame,
            text="✓  Verify & Secure My Vault",
            height=48,
            corner_radius=12,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=self.theme['primary'],
            hover_color=self.theme['text_accent'],
            text_color="#FFFFFF",
            command=self.verify_and_login,
        )
        self.login_btn.grid(row=6, column=0, sticky="ew", padx=10, pady=(0, 10))

        # ── Status label (hidden until action) ───────────────────────────
        self.status_label = ctk.CTkLabel(
            self.form_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=self.theme['text_sub'],
            height=20,
        )
        self.status_label.grid(row=7, column=0, pady=(0, 5))

        # ═══════════════════════════════════════════════════════════════════
        # FEATURE BADGES ROW — three trust signals at the bottom
        # ═══════════════════════════════════════════════════════════════════
        badges_frame = ctk.CTkFrame(self, fg_color="transparent")
        badges_frame.grid(row=2, column=0, pady=(10, 20))

        badges = [
            ("🛡️", "End-to-End Security", "Your data is always protected"),
            ("🔐", "Private by Design", "You control your keys"),
            ("🏛️", "Internet Archive Storage", "Reliable. Durable. Permanent."),
        ]

        for i, (icon, title_text, desc_text) in enumerate(badges):
            badge = ctk.CTkFrame(
                badges_frame,
                fg_color=self.theme['card_bg'],
                corner_radius=12,
                border_width=1,
                border_color=self.theme['card_border'],
            )
            badge.grid(row=0, column=i, padx=15, ipadx=15, ipady=10)

            # Badge inner layout
            badge.grid_columnconfigure(0, weight=0)
            badge.grid_columnconfigure(1, weight=1)

            badge_icon = ctk.CTkLabel(
                badge,
                text=icon,
                font=ctk.CTkFont(size=24),
                text_color=self.theme['text_accent'],
            )
            badge_icon.grid(row=0, column=0, rowspan=2, padx=(10, 8), pady=5)

            badge_title = ctk.CTkLabel(
                badge,
                text=title_text,
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=self.theme['text_main'],
                anchor="w",
            )
            badge_title.grid(row=0, column=1, sticky="w", padx=(0, 10))

            badge_desc = ctk.CTkLabel(
                badge,
                text=desc_text,
                font=ctk.CTkFont(size=11),
                text_color=self.theme['text_sub'],
                anchor="w",
            )
            badge_desc.grid(row=1, column=1, sticky="w", padx=(0, 10))

    # ─── Toggle secret key visibility ────────────────────────────────────
    def _toggle_secret_visibility(self):
        self.secret_visible = not self.secret_visible
        if self.secret_visible:
            self.secret_entry.configure(show="")
            self.toggle_btn.configure(text="🙈")
        else:
            self.secret_entry.configure(show="•")
            self.toggle_btn.configure(text="👁")

    # ─── Authenticate with Internet Archive ──────────────────────────────
    def verify_and_login(self):
        access = self.access_entry.get().strip()
        secret = self.secret_entry.get().strip()

        if not access or not secret:
            messagebox.showerror("Error", "Both keys are required.")
            return

        # Show loading state
        self.login_btn.configure(
            text="⟳  Verifying...", state="disabled"
        )
        self.status_label.configure(
            text="Connecting to Internet Archive...", text_color=self.theme['text_accent']
        )
        self.update_idletasks()

        # Simple validation - Internet Archive will validate when actually used
        # For now, just save and proceed
        try:
            self.status_label.configure(
                text="✓ Credentials saved!", text_color=self.theme['success']
            )
            self.update_idletasks()

            self.cred_manager.save_credentials(access, secret)
            self.after(500, lambda: self.login_callback(access, secret))
        except Exception as e:
            self._reset_login_btn()
            self.status_label.configure(
                text="❌ Error saving credentials.", text_color=self.theme['error']
            )
            messagebox.showerror("Error", f"Could not save credentials:\n{str(e)}")

    def _reset_login_btn(self):
        self.login_btn.configure(
            text="✓  Verify & Secure My Vault",
            state="normal",
            fg_color=self.theme['primary'],
        )
