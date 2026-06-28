import sys
import os

_here = os.path.dirname(os.path.abspath(__file__))
_parent = os.path.dirname(_here)

if getattr(sys, 'frozen', False):
    _exe = os.path.dirname(sys.executable)
    _mei = getattr(sys, '_MEIPASS', _exe)
    _int = os.path.join(_exe, '_internal')
    for _p in [_mei, _int, _exe]:
        if os.path.isdir(_p) and _p not in sys.path:
            sys.path.insert(0, _p)
elif _parent not in sys.path:
    sys.path.insert(0, _parent)

from aegis_vault.gui.app import AppGUI
from version import print_version_info

if __name__ == "__main__":
    print("\n" + "="*50)
    print_version_info()
    print("="*50 + "\n")

    app = AppGUI()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
