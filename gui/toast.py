import customtkinter as ctk

class Toast(ctk.CTkFrame):
    """Simple toast notification that appears at the bottom of the screen"""
    
    def __init__(self, parent, message, duration=3000, toast_type="info"):
        super().__init__(parent, fg_color="#1E293B", corner_radius=10,
                        border_width=1, border_color="#334155")
        
        self.duration = duration
        
        # Icon based on type
        icons = {
            "info": "ℹ️",
            "success": "✅",
            "error": "❌",
            "warning": "⚠️"
        }
        
        colors = {
            "info": "#60A5FA",
            "success": "#22C55E",
            "error": "#EF4444",
            "warning": "#F59E0B"
        }
        
        icon = icons.get(toast_type, "ℹ️")
        color = colors.get(toast_type, "#60A5FA")
        
        # Build toast
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=12, pady=8)
        
        ctk.CTkLabel(content, text=icon, font=ctk.CTkFont(size=16)).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(content, text=message, font=ctk.CTkFont(size=11),
                    text_color=color, wraplength=300).pack(side="left", fill="x", expand=True)
        
        # Position at bottom center
        self.place(relx=0.5, rely=0.95, anchor="s")
        
        # Auto-hide after duration
        self.after(duration, self.hide)
    
    def hide(self):
        """Fade out and destroy"""
        self.place_forget()
        self.destroy()


def show_toast(parent, message, duration=3000, toast_type="info"):
    """Helper function to show a toast notification"""
    return Toast(parent, message, duration, toast_type)
