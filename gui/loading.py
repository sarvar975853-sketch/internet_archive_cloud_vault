"""
Loading screen for Aegis Vault
Shows while app initializes
"""

import customtkinter as ctk
from aegis_vault.gui.theme import THEME


class LoadingScreen(ctk.CTkToplevel):
    """Simple loading screen"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.title("Loading...")
        self.geometry("400x200")
        self.resizable(False, False)
        
        # Center on screen
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.winfo_screenheight() // 2) - (200 // 2)
        self.geometry(f"400x200+{x}+{y}")
        
        self.configure(fg_color=THEME['main_bg'])
        
        # Remove window decorations
        self.overrideredirect(True)
        
        # Make it modal
        self.transient(parent)
        self.grab_set()
        
        # Content
        content = ctk.CTkFrame(self, fg_color=THEME['card_bg'], corner_radius=15,
                              border_width=1, border_color=THEME['card_border'])
        content.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Logo
        ctk.CTkLabel(content, text="🛡️", font=ctk.CTkFont(size=60)).pack(pady=(30, 10))
        
        # Title
        ctk.CTkLabel(content, text="Aegis Vault", 
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=THEME['text_main']).pack()
        
        # Status
        self.status_label = ctk.CTkLabel(content, text="Initializing...",
                                         font=ctk.CTkFont(size=12),
                                         text_color=THEME['text_sub'])
        self.status_label.pack(pady=(10, 0))
        
        # Progress bar
        self.progress = ctk.CTkProgressBar(content, width=300, height=6,
                                          progress_color=THEME['primary'])
        self.progress.pack(pady=(10, 30))
        self.progress.set(0)
        
        # Start animation
        self._animate()
    
    def _animate(self):
        """Animate progress bar"""
        current = self.progress.get()
        if current < 0.9:
            self.progress.set(current + 0.02)
            self.after(50, self._animate)
    
    def update_status(self, text):
        """Update status text"""
        self.status_label.configure(text=text)
        self.update_idletasks()
    
    def close(self):
        """Close loading screen"""
        self.progress.set(1.0)
        self.update_status("Ready!")
        self.after(300, self.destroy)
