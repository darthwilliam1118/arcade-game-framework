"""BaseGameConfig - shared top-level config fields, argv overrides, and path helper.

Games subclass BaseGameConfig and add game-specific sub-config dataclasses as
additional fields.  ``apply_argv_overrides`` walks the full dataclass tree so
any scalar field (including fields on nested sub-config dataclasses) can be
overridden with ``-key value`` on the command line.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, fields, is_dataclass
from pathlib import Path
from typing import Any


@dataclass
class BaseGameConfig:
    """Shared top-level fields every game needs.

    Subclass and add game-specific sub-configs as additional fields.  The
    subclass is responsible for load()/save() since those know about the
    game's sub-config sections.
    """

    starting_level: int = 1
    num_lives: int = 3
    music_volume: int = 80  # 0-100
    effects_volume: int = 80  # 0-100
    debug: bool = False
    god_mode: bool = False
    max_window_height: int = 1024  # height in px
    sprite_scale: float = 1.0


def config_path(project_root: Path, filename: str = "game_config.toml") -> Path:
    """Return the path to *filename*.

    When frozen by PyInstaller, look next to the .exe so users can edit it.
    In dev, look in *project_root* (passed by the caller so agf doesn't have
    to guess where the game lives).
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent / filename
    return project_root / filename


def _is_numeric(s: str) -> bool:
    """True if *s* parses as a number (handles negatives like -1)."""
    try:
        float(s)
        return True
    except ValueError:
        return False


def _collect_fields(obj: Any, registry: dict[str, tuple[object, str]]) -> None:
    """Recursively register every scalar field of *obj* and its dataclass fields."""
    for f in fields(obj):
        value = getattr(obj, f.name)
        if is_dataclass(value):
            _collect_fields(value, registry)
        elif not isinstance(value, dict):
            registry[f.name] = (obj, f.name)


def apply_argv_overrides(cfg: Any) -> None:
    """Apply -key value overrides from sys.argv to *cfg* in place.

    Walks every dataclass field on *cfg* (recursing into sub-dataclass fields)
    and matches ``-key`` tokens in ``sys.argv`` against field names.  Matching
    overrides are applied with correct type coercion; unknown tokens print a
    warning and are skipped.  The TOML file is never modified.
    """
    registry: dict[str, tuple[object, str]] = {}
    _collect_fields(cfg, registry)

    argv = sys.argv[1:]
    i = 0
    while i < len(argv):
        token = argv[i]
        if not token.startswith("-"):
            i += 1
            continue

        key = token.lstrip("-")
        if key not in registry:
            print(f"Unknown argument {token}, ignored")
            i += 1
            continue

        owner, attr = registry[key]
        existing = getattr(owner, attr)

        next_token = argv[i + 1] if i + 1 < len(argv) else None
        next_is_value = next_token is not None and (
            not next_token.startswith("-") or _is_numeric(next_token)
        )

        if isinstance(existing, bool) and not next_is_value:
            setattr(owner, attr, True)
        elif next_is_value:
            assert next_token is not None
            i += 1
            try:
                if isinstance(existing, bool):
                    setattr(owner, attr, next_token.lower() not in ("false", "0", "no", "off"))
                elif isinstance(existing, int):
                    setattr(owner, attr, int(next_token))
                elif isinstance(existing, float):
                    setattr(owner, attr, float(next_token))
                else:
                    setattr(owner, attr, next_token)
            except ValueError:
                print(f"Invalid value for {token}: {next_token!r}, ignored")
        else:
            print(f"Missing value for {token}, ignored")

        i += 1
