"""Resource path helper — works in both dev and PyInstaller bundles.

Games must call ``set_project_root(Path)`` once at startup (before any
resource is loaded) so that dev-mode path resolution locates the game's
asset tree rather than the agf install location.  In a frozen bundle the
hint is ignored; ``sys._MEIPASS`` is authoritative.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

_project_root: Optional[Path] = None


def set_project_root(path: Path) -> None:
    """Record the game's project root for dev-mode resource resolution.

    Call once at startup, before any resource is loaded.  Tests should
    call this from a conftest.py fixture.  In a frozen bundle the value
    is ignored.
    """
    global _project_root
    _project_root = Path(path)


def resource_path(relative: str) -> str:
    """Return absolute path to *relative*, compatible with PyInstaller bundles."""
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass is not None:
        return os.path.join(meipass, relative)
    if _project_root is None:
        raise RuntimeError(
            "agf.paths.set_project_root() must be called before resource_path() "
            "in dev mode.  Games should call it from their entry point; tests "
            "should call it from a conftest.py fixture."
        )
    return str(_project_root / relative)


def writable_root() -> Path:
    """Return the directory for game-writable files (high scores, config, saves).

    In a frozen bundle this is the directory containing the exe so files
    persist between runs.  In dev, it is the project root set via
    ``set_project_root()``.  Callers should append their own filename.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    if _project_root is None:
        raise RuntimeError(
            "agf.paths.set_project_root() must be called before writable_root() "
            "in dev mode.  Games should call it from their entry point; tests "
            "should call it from a conftest.py fixture."
        )
    return _project_root
