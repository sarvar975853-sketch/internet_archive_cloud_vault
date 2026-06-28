import customtkinter as ctk
from aegis_vault.gui.theme import THEME

class Toast(ctk.CTkFrame):
    def __init__(self, parent, message, duration=3000, toast_type="info"):
        super().__init__(parent, fg_color=THEME['glass_overlay'], corner_radius=10,
                        border_width=1, border_color=THEME['border_subtle'])

        self.duration = duration

        icons = {
            "info": "ℹ️",
            "success": "✅",
            "error": "❌",
            "warning": "⚠️"
        }

        colors = {
            "info": THEME['accent_cyan'],
            "success": THEME['success'],
            "error": THEME['error'],
            "warning": THEME['warning']
        }

        icon = icons.get(toast_type, "ℹ️")
        color = colors.get(toast_type, THEME['accent_cyan'])

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=12, pady=8)

        ctk.CTkLabel(content, text=icon, font=ctk.CTkFont(size=16)).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(content, text=message, font=ctk.CTkFont(size=11),
                    text_color=color, wraplength=300).pack(side="left", fill="x", expand=True)

        self.place(relx=0.5, rely=0.95, anchor="s")

        self.after(duration, self.hide)

    def hide(self):
        self.place_forget()
        self.destroy()


def show_toast(parent, message, duration=3000, toast_type="info"):
    return Toast(parent, message, duration, toast_type)
