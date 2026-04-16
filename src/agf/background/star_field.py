"""ProceduralStarField - scrolling parallax star field backed by arcade.SpriteList."""

from __future__ import annotations

import random
from typing import Any, Optional

import arcade


class ProceduralStarField:
    """Procedural scrolling star field rendered via arcade.SpriteList.

    Stars scroll downward at independent speeds (parallax). Stars that exit the
    bottom wrap to the top with a new random x position. Positions are updated
    in-place every frame - no GPU buffer rebuild required.

    Pass *_sprites* (any non-None value) to skip OpenGL initialisation in tests.
    Parallel lists (_x, _y, _speed_list) are always maintained and are used
    directly in test mode.
    """

    def __init__(
        self,
        window_width: int,
        window_height: int,
        star_count: int = 300,
        speed_min: float = 20.0,
        speed_max: float = 120.0,
        _sprites: Optional[Any] = None,
    ) -> None:
        self._width = window_width
        self._height = window_height
        self._count = star_count
        self._speed_min = speed_min
        self._speed_max = speed_max

        self._x: list[float] = [random.uniform(0, window_width) for _ in range(star_count)]
        self._y: list[float] = [random.uniform(0, window_height) for _ in range(star_count)]
        self._speed_list: list[float] = [
            random.uniform(speed_min, speed_max) for _ in range(star_count)
        ]
        self._brightness: list[int] = [random.randint(120, 255) for _ in range(star_count)]

        self._stars: Optional[arcade.SpriteList] = None
        if _sprites is None:
            _textures = [
                arcade.make_circle_texture(2, (255, 255, 255, 255)),
                arcade.make_circle_texture(3, (255, 255, 255, 255)),
                arcade.make_circle_texture(4, (220, 220, 255, 255)),
            ]
            self._stars = arcade.SpriteList()
            for i in range(star_count):
                star = arcade.Sprite()
                star.texture = random.choice(_textures)
                star.center_x = self._x[i]
                star.center_y = self._y[i]
                b = self._brightness[i]
                star.color = (b, b, b, 255)
                self._stars.append(star)

    def update(self, delta_time: float) -> None:
        """Scroll all stars downward; wrap any that exit the bottom."""
        for i in range(self._count):
            self._y[i] -= self._speed_list[i] * delta_time
            if self._y[i] < 0:
                self._y[i] = float(self._height)
                self._x[i] = random.uniform(0, self._width)
            if self._stars is not None:
                self._stars[i].center_x = self._x[i]
                self._stars[i].center_y = self._y[i]

    def draw(self) -> None:
        """Draw the star field - single batched GPU call."""
        if self._stars is not None:
            self._stars.draw()
