"""
Interactive UI helpers — glow hover effect for buttons.
Changes border color on hover without resizing (avoids text layout bugs).
"""
from aegis_vault.gui.theme import THEME


def apply_bubble_hover(button, glow_color=None):
    """
    Attach a glow hover effect to a CTkButton.
    On hover: border lights up with accent color.
    On leave: border returns to default.
    No resizing — text stays centered.
    """
    original_border_color = button.cget("border_color") or "#292524"

    if glow_color is None:
        glow_color = THEME.get('border_focus', '#F59E0B')

    def on_enter(event):
        try:
            button.configure(border_width=2, border_color=glow_color)
        except Exception:
            pass

    def on_leave(event):
        try:
            button.configure(border_width=0, border_color=original_border_color)
        except Exception:
            pass

    button.bind("<Enter>", on_enter, add="+")
    button.bind("<Leave>", on_leave, add="+")
