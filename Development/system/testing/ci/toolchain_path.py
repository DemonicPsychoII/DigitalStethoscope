"""Make the production firmware toolchain modules importable from the CI scripts.

Import this module before `build_support`. The toolchain lives with the production
tools, so firmware stays buildable from a checkout without this testing folder.
"""

import sys
from pathlib import Path

TOOLCHAIN_DIRECTORY = Path(__file__).resolve().parents[2] / "coding/tools/toolchain"

if str(TOOLCHAIN_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(TOOLCHAIN_DIRECTORY))
