from __future__ import annotations

import os
import sys
from pathlib import Path


base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
tcl_root = base / "tcl"

if tcl_root.exists():
    tcl_dirs = sorted(tcl_root.glob("tcl*"))
    tk_dirs = sorted(tcl_root.glob("tk*"))
    if tcl_dirs:
        os.environ.setdefault("TCL_LIBRARY", str(tcl_dirs[0]))
    if tk_dirs:
        os.environ.setdefault("TK_LIBRARY", str(tk_dirs[0]))
