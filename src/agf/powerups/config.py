"""PowerUpConfigBase — spawning + pickup-sprite timing for power-ups.

Games subclass and add their own effect-specific fields (durations,
magnitudes, per-type weights, etc.). All spawning and sprite-motion
fields live here so the base spawner and sprite need no game input.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PowerUpConfigBase:
    """Base config for the power-up system."""

    # Spawn timing
    spawn_interval_base: float = 20.0
    spawn_interval_min: float = 6.0
    spawn_interval_jitter: float = 2.0
    spawn_interval_decay: float = 0.85

    # Pickup sprite motion
    fall_speed_min: float = 60.0
    fall_speed_max: float = 120.0
    fall_angle_max: float = 20.0
    spin_rpm: float = 10.0
    spawn_height_offset: float = 60.0
