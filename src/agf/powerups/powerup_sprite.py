"""PowerUpSprite — falling pickup sprite.

Spawns above the visible window and drifts downward at a configurable
angle and speed, rotating slowly while falling. Removes itself when it
scrolls off the bottom.

Games pass a pre-loaded texture so the sprite has no knowledge of
asset paths.
"""

from __future__ import annotations

import math
from typing import Optional

import arcade


class PowerUpSprite(arcade.Sprite):
    """Falling power-up pickup sprite."""

    def __init__(
        self,
        x: float,
        y: float,
        effect_type: str,
        fall_speed: float = 80.0,
        angle_deg: float = 0.0,
        spin_rpm: float = 10.0,
        scale: float = 1.0,
        texture: Optional[arcade.Texture] = None,
    ):
        """Initialise a falling pickup.

        x, y        spawn position. y should be above window top
                    (e.g. window_height + sprite_height / 2).
        fall_speed  pixels/second along the fall direction.
        angle_deg   drift angle in degrees. 0 = straight down.
                    Positive drifts right, negative drifts left.
                    Recommended range: -20 to +20.
        spin_rpm    sprite rotation speed in RPM while falling.
                    10 RPM = one full rotation every 6 seconds.
        """
        if texture is not None:
            super().__init__(path_or_texture=texture)
        else:
            super().__init__()
        self.scale = scale
        self.effect_type = effect_type

        self._fall_speed = fall_speed
        self._spin_rpm = spin_rpm

        rad = math.radians(angle_deg)
        self._vx = math.sin(rad) * fall_speed
        self._vy = -math.cos(rad) * fall_speed

        self._spin_rate = spin_rpm * 6.0  # 1 RPM = 6 deg/s

        self.center_x = x
        self.center_y = y
        self.angle = 0.0

    def update(self, delta_time: float) -> None:  # type: ignore[override]
        self.center_x += self._vx * delta_time
        self.center_y += self._vy * delta_time
        self.angle += self._spin_rate * delta_time

        if self.center_y < -(self.height * 2):
            self.remove_from_sprite_lists()
