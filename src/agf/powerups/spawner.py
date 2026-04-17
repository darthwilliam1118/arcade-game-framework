"""PowerUpSpawner — decides when to spawn a power-up and which type.

Has no knowledge of sprites or effects — returns an effect_type string
(or None) each frame. PowerUpManager creates the sprite.

Games subclass and override _build_weight_table() to define which
effect types are available and their spawn weights. The weight table
can vary by level_type for level-specific drops.
"""

from __future__ import annotations

import random

from agf.powerups.config import PowerUpConfigBase


class PowerUpSpawner:
    """Tracks spawn cadence and selects pickup types by weight."""

    def __init__(self, config: PowerUpConfigBase):
        self._config = config
        self._timer: float = 0.0
        self._interval: float = config.spawn_interval_base
        self._level_number: int = 1
        self._level_type: str = "standard"

    def setup(self, level_number: int, level_type: str) -> None:
        """Call at level start to configure scaling."""
        self._level_number = level_number
        self._level_type = level_type
        self._interval = self._compute_interval()
        self._timer = 0.0

    def update(self, delta_time: float) -> str | None:
        """Advance timer. Returns effect_type string to spawn, or None."""
        self._timer += delta_time
        if self._timer < self._interval:
            return None
        self._timer = 0.0
        self._interval = self._compute_interval()
        weights = self._build_weight_table()
        if not weights:
            return None
        types = list(weights.keys())
        probs = list(weights.values())
        return random.choices(types, weights=probs, k=1)[0]

    def _compute_interval(self) -> float:
        """Compute spawn interval using an exponential decay curve.

        interval = min + (base - min) * decay ^ (level - 2)

        Drops quickly in early levels and flattens toward the minimum.
        level_offset is clamped to 0 so level 1 and level 2 both land
        at the full base interval.
        """
        cfg = self._config
        base = cfg.spawn_interval_base
        minimum = cfg.spawn_interval_min
        decay_rate = cfg.spawn_interval_decay
        level_offset = max(0, self._level_number - 2)
        interval = minimum + (base - minimum) * (decay_rate**level_offset)
        jitter = random.uniform(-cfg.spawn_interval_jitter, cfg.spawn_interval_jitter)
        return max(minimum, interval + jitter)

    def _build_weight_table(self) -> dict[str, float]:
        """Return {effect_type: weight} for random selection.

        Override in games. Base returns empty — nothing spawns.
        """
        return {}

    @property
    def current_interval(self) -> float:
        return self._interval

    @property
    def timer(self) -> float:
        return self._timer

    @timer.setter
    def timer(self, value: float) -> None:
        self._timer = value
