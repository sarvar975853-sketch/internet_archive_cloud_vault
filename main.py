import sys
import os

if getattr(sys, 'frozen', False):
    _base = sys._MEIPASS
else:
    _base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, _base)

from aegis_vault.gui.app import AppGUI

from version import print_version_info

if __name__ == "__main__":
    # Print version info to console
    print("\n" + "="*50)
    print_version_info()
    print("="*50 + "\n")
    
    # Start the GUI application
    app = AppGUI()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
