"""Level-complete screen base — awards bonus, shows lives, advances."""

from __future__ import annotations

from typing import Callable, Optional

import arcade

from agf.ui.text_utils import FONT_MAIN, FONT_THIN, centered_text


class LevelCompleteView(arcade.View):
    """Generic level-complete screen.

    Renders a title, a bonus line, a list of surviving player rows, and a
    delayed "GET READY" prompt.  Subclasses populate ``build_bonus_text`` /
    ``build_player_rows`` with game-specific content and override
    ``apply_bonus`` if the base logic does not fit.  After
    ``DISPLAY_DURATION`` seconds, ``on_complete`` is invoked.
    """

    TITLE: str = "LEVEL COMPLETE!"
    GET_READY: str = "GET READY..."
    TITLE_COLOR: tuple[int, int, int] = arcade.color.GREEN
    BONUS_COLOR: tuple[int, int, int] = arcade.color.YELLOW
    ROW_COLOR: tuple[int, int, int] = arcade.color.WHITE
    READY_COLOR: tuple[int, int, int] = arcade.color.WHITE
    DISPLAY_DURATION: float = 3.0
    GET_READY_DELAY: float = 1.0
    MUSIC_TRACK: Optional[str] = "ending"

    def __init__(self, on_complete: Callable[[], None]) -> None:
        super().__init__()
        self._on_complete = on_complete
        self._elapsed: float = 0.0
        self._title_text: Optional[arcade.Text] = None
        self._bonus_text: Optional[arcade.Text] = None
        self._player_texts: list[arcade.Text] = []
        self._get_ready_text: Optional[arcade.Text] = None
        self.apply_bonus()

    def apply_bonus(self) -> None:
        """Override to mutate game state (award bonus, bump level, etc.)."""

    def build_bonus_text(self) -> str:
        """Override to return the bonus line (e.g. 'LEVEL 2    Bonus: +1000')."""
        return ""

    def build_player_rows(self) -> list[str]:
        """Override to return one line per surviving player."""
        return []

    def on_show_view(self) -> None:
        if self.MUSIC_TRACK is not None:
            music = getattr(self.window, "music", None)
            if music is not None:
                music.play(self.MUSIC_TRACK)

        w, h = self.window.width, self.window.height
        self._title_text = centered_text(
            self.TITLE,
            w,
            h // 2 + 100,
            font_size=48,
            color=self.TITLE_COLOR,
            font_name=FONT_MAIN,
        )
        self._bonus_text = centered_text(
            self.build_bonus_text(),
            w,
            h // 2 + 40,
            font_size=24,
            color=self.BONUS_COLOR,
            font_name=FONT_MAIN,
        )
        self._player_texts = [
            centered_text(
                line,
                w,
                h // 2 - 10 - i * 32,
                font_size=18,
                color=self.ROW_COLOR,
                font_name=FONT_THIN,
            )
            for i, line in enumerate(self.build_player_rows())
        ]
        self._get_ready_text = centered_text(
            self.GET_READY,
            w,
            h // 2 - 90,
            font_size=16,
            color=(self.READY_COLOR[0], self.READY_COLOR[1], self.READY_COLOR[2], 0),
            font_name=FONT_MAIN,
        )

    def on_update(self, delta_time: float) -> None:
        star_field = getattr(self.window, "star_field", None)
        if star_field is not None:
            star_field.update(delta_time)
        self._elapsed += delta_time

        if self._get_ready_text is not None and self._elapsed >= self.GET_READY_DELAY:
            self._get_ready_text.color = self.READY_COLOR

        if self._elapsed >= self.DISPLAY_DURATION:
            self._on_complete()

    def on_draw(self) -> None:
        self.clear()
        background = getattr(self.window, "background", None)
        if background is not None:
            background.draw()
        star_field = getattr(self.window, "star_field", None)
        if star_field is not None:
            star_field.draw()
        if self._title_text:
            self._title_text.draw()
        if self._bonus_text:
            self._bonus_text.draw()
        for t in self._player_texts:
            t.draw()
        if self._get_ready_text:
            self._get_ready_text.draw()
