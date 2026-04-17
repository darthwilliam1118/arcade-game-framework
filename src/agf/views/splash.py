"""Splash screen base — title card with background music preload."""

from __future__ import annotations

import threading
from typing import Callable, Optional

import arcade

from agf.ui.text_utils import FONT_MAIN, FONT_THIN, centered_text


class SplashView(arcade.View):
    """Generic title-card view.

    Renders a two-line title and a "press any key" prompt over the window's
    background + star field.  A background thread runs ``_preload_tracks``
    while the splash animates; subclasses override that hook to load
    game-specific audio.  When the auto-advance timer elapses or any key is
    pressed (after preload), ``on_complete`` is invoked.
    """

    TITLE_LINE1: str = "My"
    TITLE_LINE2: str = "Game"
    PROMPT: str = "Press any key to continue..."
    AUTO_ADVANCE: float = 5.0
    TITLE_COLOR: tuple[int, int, int] = arcade.color.YELLOW
    PROMPT_COLOR: tuple[int, int, int] = arcade.color.WHITE
    TITLE_FONT_SIZE: int = 64
    PROMPT_FONT_SIZE: int = 18

    def __init__(self, on_complete: Callable[[], None]) -> None:
        super().__init__()
        self._on_complete = on_complete
        self._elapsed: float = 0.0
        self._assets_ready: bool = False
        self._title_line1: Optional[arcade.Text] = None
        self._title_line2: Optional[arcade.Text] = None
        self._prompt_text: Optional[arcade.Text] = None

    def on_show_view(self) -> None:
        w, h = self.window.width, self.window.height
        self._title_line1 = centered_text(
            self.TITLE_LINE1,
            w,
            h // 2 + 44,
            font_size=self.TITLE_FONT_SIZE,
            color=self.TITLE_COLOR,
            font_name=FONT_MAIN,
        )
        self._title_line2 = centered_text(
            self.TITLE_LINE2,
            w,
            h // 2 - 36,
            font_size=self.TITLE_FONT_SIZE,
            color=self.TITLE_COLOR,
            font_name=FONT_MAIN,
        )
        self._prompt_text = centered_text(
            self.PROMPT,
            w,
            int(h * 0.05),
            font_size=self.PROMPT_FONT_SIZE,
            color=self.PROMPT_COLOR,
            font_name=FONT_THIN,
        )
        # Preload off the main thread so splash appears with no audio delay.
        # arcade.load_sound() is audio-only and safe from a worker thread.
        threading.Thread(target=self._preload_tracks, daemon=True).start()

    def _preload_tracks(self) -> None:
        """Override to preload game-specific audio. Must set _assets_ready."""
        self._assets_ready = True

    def on_update(self, delta_time: float) -> None:
        star_field = getattr(self.window, "star_field", None)
        if star_field is not None:
            star_field.update(delta_time)
        if not self._assets_ready:
            return
        self._elapsed += delta_time
        if self._elapsed >= self.AUTO_ADVANCE:
            self._on_complete()

    def on_draw(self) -> None:
        self.clear()
        background = getattr(self.window, "background", None)
        if background is not None:
            background.draw()
        star_field = getattr(self.window, "star_field", None)
        if star_field is not None:
            star_field.draw()
        if self._title_line1:
            self._title_line1.draw()
        if self._title_line2:
            self._title_line2.draw()
        if self._assets_ready and self._prompt_text:
            self._prompt_text.draw()

    def on_key_press(self, key: int, modifiers: int) -> None:
        if not self._assets_ready:
            return
        self._on_complete()
