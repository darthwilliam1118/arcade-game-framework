"""SoundManager — throttles simultaneous playbacks of one sound.

Tracks active pyglet Players; when the cap is reached the oldest is
stopped before a new one starts. Use a separate instance per sound type.

Example:
    self._sm_explosion = SoundManager(max_simultaneous=2)
    self._sm_explosion.play(self._snd_explosion, volume=0.8)
"""

from __future__ import annotations

import arcade


class SoundManager:
    """Throttles simultaneous playbacks of one sound to reduce audio thread load.

    Tracks active pyglet Players; when the cap is reached the oldest is
    stopped before a new one starts. Use a separate instance per sound type.
    """

    def __init__(self, max_simultaneous: int = 4) -> None:
        self._max = max_simultaneous
        self._active: list[arcade.pyglet.media.Player] = []

    def play(self, sound: arcade.Sound, volume: float = 1.0) -> None:
        """Play *sound* at *volume*, stopping the oldest playback if at cap."""
        self._active = [p for p in self._active if p.playing]
        if len(self._active) >= self._max:
            oldest = self._active.pop(0)
            arcade.stop_sound(oldest)
        player = arcade.play_sound(sound, volume=volume)
        if player is not None:
            self._active.append(player)

    @property
    def active_count(self) -> int:
        """Number of currently playing instances. Useful for debug display."""
        self._active = [p for p in self._active if p.playing]
        return len(self._active)
