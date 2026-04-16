"""HUDBase - minimal scaffold for game HUDs.

Holds window dimensions and a list of ``arcade.Text`` objects with a
default ``draw()`` that iterates them.  Subclasses populate ``self._texts``
with whatever text elements the game needs.
"""

from __future__ import annotations

import arcade


class HUDBase:
    """Container for window dims and HUD text objects."""

    def __init__(self, window_width: int, window_height: int) -> None:
        self.window_width = window_width
        self.window_height = window_height
        self._texts: list[arcade.Text] = []

    def draw(self) -> None:
        """Draw every text object in ``self._texts``."""
        for t in self._texts:
            t.draw()
