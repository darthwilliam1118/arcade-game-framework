"""GameWindowBase - shared arcade.Window scaffold for games built on agf.

Subclasses pass their config objects and window title.  The base handles:
  - window size derived from ``max_window_height`` (4:3 aspect, 1.25 x height)
  - black background color
  - StaticBackground + ProceduralStarField construction
  - MusicPlayer init with config volume

Games override ``_load_fonts()`` to register whichever TTFs they use.  Games
are responsible for wiring their own state manager after ``super().__init__``.
"""

from __future__ import annotations

import arcade

from agf.background import BackgroundConfig, ProceduralStarField, StaticBackground
from agf.config import BaseGameConfig
from agf.music import MusicPlayer


class GameWindowBase(arcade.Window):
    """Arcade window with background, star field, and music pre-wired."""

    def __init__(
        self,
        cfg: BaseGameConfig,
        background_cfg: BackgroundConfig,
        title: str,
    ) -> None:
        h = cfg.max_window_height
        w = int(h * 1.25)
        super().__init__(w, h, title, center_window=True)
        arcade.set_background_color(arcade.color.BLACK)
        self._load_fonts()
        self.background = StaticBackground(background_cfg.background_image, w, h)
        self.star_field = ProceduralStarField(
            w,
            h,
            background_cfg.star_count,
            background_cfg.star_speed_min,
            background_cfg.star_speed_max,
        )
        self.music = MusicPlayer()
        self.music.set_volume(cfg.music_volume)

    def _load_fonts(self) -> None:
        """Override to register any custom fonts.  No-op by default."""
