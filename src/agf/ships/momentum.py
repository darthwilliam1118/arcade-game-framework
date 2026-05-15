"""MomentumShipMixin - reusable momentum/friction ship physics.

Mix into any sprite subclass that needs inertia-based movement.
The mixin owns velocity only; position is managed by the host class
(typically arcade.Sprite via self.center_x / self.center_y).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MomentumConfig:
    accel: float  # px/s^2 applied per unit of input (-1.0 to 1.0)
    friction: float  # velocity multiplier per second (0.0-1.0; 0.85 = decay)
    max_speed_x: float  # px/s horizontal clamp
    max_speed_y: float  # px/s vertical clamp


class MomentumShipMixin:
    """Mixin providing velocity_x / velocity_y with acceleration and friction.

    Host class must call apply_momentum(delta_time) each frame after
    setting input_x and input_y (-1.0, 0.0, or 1.0).

    The mixin does NOT update center_x / center_y - the host class does
    that after calling apply_momentum(), so it can apply its own clamping
    (world bounds, camera left edge, etc.) before committing the position.
    """

    def __init__(self, momentum_config: MomentumConfig) -> None:
        self._mcfg = momentum_config
        self.velocity_x: float = 0.0
        self.velocity_y: float = 0.0
        self.input_x: float = 0.0  # set by host before apply_momentum()
        self.input_y: float = 0.0

    def apply_momentum(self, delta_time: float) -> tuple[float, float]:
        """Update velocity from input and friction.

        Returns (delta_x, delta_y) - the position delta to apply this frame.
        The caller applies it to center_x / center_y after clamping.
        """
        cfg = self._mcfg
        self.velocity_x += self.input_x * cfg.accel * delta_time
        self.velocity_y += self.input_y * cfg.accel * delta_time

        # Friction: exponential decay independent of frame rate.
        decay = cfg.friction**delta_time
        self.velocity_x *= decay
        self.velocity_y *= decay

        # Speed clamp.
        self.velocity_x = max(-cfg.max_speed_x, min(cfg.max_speed_x, self.velocity_x))
        self.velocity_y = max(-cfg.max_speed_y, min(cfg.max_speed_y, self.velocity_y))

        return self.velocity_x * delta_time, self.velocity_y * delta_time
