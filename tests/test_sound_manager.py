"""Tests for SoundManager — no display or audio device required."""
from __future__ import annotations
from unittest.mock import MagicMock, patch
from agf.sound_manager import SoundManager


def _make_player(playing: bool = True):
    p = MagicMock()
    p.playing = playing
    return p


def test_play_adds_to_active() -> None:
    sm = SoundManager(max_simultaneous=3)
    mock_player = _make_player()
    with patch("agf.sound_manager.arcade.play_sound", return_value=mock_player):
        with patch("agf.sound_manager.arcade.stop_sound"):
            sm.play(MagicMock())
    assert len(sm._active) == 1


def test_play_stops_oldest_when_at_cap() -> None:
    sm = SoundManager(max_simultaneous=2)
    oldest = _make_player(playing=True)
    sm._active = [oldest, _make_player(playing=True)]
    new_player = _make_player()
    with patch("agf.sound_manager.arcade.play_sound", return_value=new_player):
        with patch("agf.sound_manager.arcade.stop_sound") as mock_stop:
            sm.play(MagicMock())
    mock_stop.assert_called_once_with(oldest)
    assert new_player in sm._active


def test_play_cleans_up_finished_players() -> None:
    sm = SoundManager(max_simultaneous=3)
    finished = _make_player(playing=False)
    sm._active = [finished]
    new_player = _make_player()
    with patch("agf.sound_manager.arcade.play_sound", return_value=new_player):
        with patch("agf.sound_manager.arcade.stop_sound"):
            sm.play(MagicMock())
    assert finished not in sm._active
    assert new_player in sm._active


def test_active_count_excludes_finished() -> None:
    sm = SoundManager(max_simultaneous=4)
    sm._active = [_make_player(True), _make_player(False), _make_player(True)]
    assert sm.active_count == 2


def test_play_returns_without_error_when_play_sound_returns_none() -> None:
    sm = SoundManager(max_simultaneous=2)
    with patch("agf.sound_manager.arcade.play_sound", return_value=None):
        with patch("agf.sound_manager.arcade.stop_sound"):
            sm.play(MagicMock())  # must not raise
    assert len(sm._active) == 0
