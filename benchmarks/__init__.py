# SPDX-License-Identifier: Apache-2.0
"""Isolated performance and accuracy benchmark suite for Computer Use Lite."""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT / "src", _ROOT / "experiments"):
    if _p.exists() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
