"""Game-over screen base — shows final scores then routes via callback."""

from __future__ import annotations

from typing import Callable, Optional, Sequence

import arcade

from agf.ui.text_utils import FONT_MAIN, FONT_THIN, centered_text


class GameOverView(arcade.View):
    """Generic game-over screen.

    Renders a title, per-player score lines, and a flashing prompt.  After
    ``DISPLAY_DURATION`` seconds, ``on_complete`` is invoked with no args;
    the subclass decides where to route next.

    Players are supplied via ``get_players()`` — override to pull from a
    state manager or other source.  Each player object must expose
    ``player_num`` and ``score`` attributes.
    """

    TITLE: str = "GAME OVER"
    PROMPT: str = "PRESS ANY KEY"
    TITLE_COLOR: tuple[int, int, int] = arcade.color.RED
    SCORE_COLOR: tuple[int, int, int] = arcade.color.WHITE
    PROMPT_COLOR: tuple[int, int, int] = arcade.color.WHITE
    DISPLAY_DURATION: float = 4.0
    MUSIC_TRACK: Optional[str] = "ending"

    def __init__(self, on_complete: Callable[[], None]) -> None:
        super().__init__()
        self._on_complete = on_complete
        self._elapsed: float = 0.0
        self._flash_elapsed: float = 0.0
        self._title_text: Optional[arcade.Text] = None
        self._score_texts: list[arcade.Text] = []
        self._press_key_text: Optional[arcade.Text] = None

    def get_players(self) -> Sequence:
        """Override to return the list of players to display."""
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
        players = self.get_players()
        self._score_texts = [
            centered_text(
                f"Player {p.player_num}:  {p.score}",
                w,
                h // 2 + 20 - i * 36,
                font_size=24,
                color=self.SCORE_COLOR,
                font_name=FONT_MAIN,
            )
            for i, p in enumerate(players)
        ]
        self._press_key_text = centered_text(
            self.PROMPT,
            w,
            h // 2 - 80,
            font_size=14,
            color=self.PROMPT_COLOR,
            font_name=FONT_THIN,
        )

    def on_update(self, delta_time: float) -> None:
        star_field = getattr(self.window, "star_field", None)
        if star_field is not None:
            star_field.update(delta_time)

        self._flash_elapsed += delta_time
        if self._press_key_text is not None:
            visible = int(self._flash_elapsed / 0.5) % 2 == 0
            r, g, b = self.PROMPT_COLOR[:3]
            self._press_key_text.color = (r, g, b, 255 if visible else 0)

        self._elapsed += delta_time
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
        for t in self._score_texts:
            t.draw()
        if self._press_key_text:
            self._press_key_text.draw()
