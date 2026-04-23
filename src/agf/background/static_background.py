"""StaticBackground - single sprite scaled to fill the window, no scrolling."""

from __future__ import annotations

import os
from typing import Optional

import arcade

from agf.paths import resource_path


class StaticBackground:
    """Single arcade.Sprite scaled to fill the window exactly - no scrolling."""

    def __init__(
        self,
        texture_path: str,
        window_width: int,
        window_height: int,
        _sprite: Optional[arcade.Sprite] = None,
    ) -> None:
        if _sprite is not None:
            sprite = _sprite
        else:
            full_path = resource_path(texture_path)
            if os.path.exists(full_path):
                sprite = arcade.Sprite(full_path)
            else:
                sprite = arcade.Sprite()
                sprite.texture = arcade.make_soft_square_texture(
                    max(window_width, window_height), arcade.color.BLACK, 0, 255
                )
            sprite.width = window_width
            sprite.height = window_height
            sprite.center_x = window_width / 2
            sprite.center_y = window_height / 2
        self._sprite_list = arcade.SpriteList()
        self._sprite_list.append(sprite)

    def draw(self) -> None:
        self._sprite_list.draw()
