"""Unit tests for HUDBase."""

from __future__ import annotations

from agf.ui.hud_base import HUDBase


class _FakeText:
    def __init__(self) -> None:
        self.draw_calls = 0

    def draw(self) -> None:
        self.draw_calls += 1


class TestHUDBase:
    def test_stores_window_dims(self) -> None:
        hud = HUDBase(800, 600)
        assert hud.window_width == 800
        assert hud.window_height == 600

    def test_texts_starts_empty(self) -> None:
        hud = HUDBase(800, 600)
        assert hud._texts == []

    def test_draw_iterates_texts(self) -> None:
        hud = HUDBase(800, 600)
        t1, t2 = _FakeText(), _FakeText()
        hud._texts = [t1, t2]  # type: ignore[list-item]
        hud.draw()
        assert t1.draw_calls == 1
        assert t2.draw_calls == 1
