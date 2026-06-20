import sys
import os

if getattr(sys, 'frozen', False):
    _exe_dir = os.path.dirname(sys.executable)
    _meipass = getattr(sys, '_MEIPASS', _exe_dir)
    _internal = os.path.join(_exe_dir, '_internal')
    for _p in [_meipass, _internal, _exe_dir]:
        if _p not in sys.path:
            sys.path.insert(0, _p)
else:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
