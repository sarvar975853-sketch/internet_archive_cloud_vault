import sys
import os

# Add parent dir to path so absolute imports like 'aegis_vault.core' work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aegis_vault.gui.app import AppGUI

# Import version from root directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
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
