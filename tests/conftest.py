import sys
import os
from pathlib import Path

# Ensure project root, src, and gui_components are on sys.path for all tests
ROOT = Path(__file__).resolve().parent.parent
for rel in ('', 'src', 'gui_components', 'core', 'gui', 'utils'):
    p = str(ROOT / rel)
    if p not in sys.path:
        sys.path.insert(0, p)
