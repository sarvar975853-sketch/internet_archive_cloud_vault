import sys
import os

from aegis_vault.gui.app import AppGUI
from version import print_version_info

if __name__ == "__main__":
    print("\n" + "="*50)
    print_version_info()
    print("="*50 + "\n")

    app = AppGUI()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
