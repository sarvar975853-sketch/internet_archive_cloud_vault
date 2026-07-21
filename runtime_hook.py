import sys
import os

if getattr(sys, 'frozen', False):
    _exe = os.path.dirname(sys.executable)
    _mei = getattr(sys, '_MEIPASS', _exe)
    _int = os.path.join(_exe, '_internal')
    for _p in [_mei, _int, _exe]:
        if os.path.isdir(_p) and _p not in sys.path:
            sys.path.insert(0, _p)
