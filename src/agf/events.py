"""GameEvent — base event enum for agf state managers and levels.

Games extend this either by re-exporting it from their own module or by
defining their own enum that includes the same values.
"""

from __future__ import annotations

from enum import Enum, auto


class GameEvent(Enum):
    PLAYER_KILLED = auto()
    LEVEL_COMPLETE = auto()
    ENEMY_DESTROYED = auto()
    POWERUP_COLLECTED = auto()
