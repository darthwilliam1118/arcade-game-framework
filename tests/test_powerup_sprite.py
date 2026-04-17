"""Unit tests for PowerUpSprite — no display required."""

from __future__ import annotations

import math

import arcade
import pytest

from agf.powerups.powerup_sprite import PowerUpSprite


def _texture() -> arcade.Texture:
    return arcade.Texture.create_empty("pu", (32, 32))


def _sprite(**overrides) -> PowerUpSprite:
    defaults = dict(
        x=100.0,
        y=700.0,
        effect_type="shield",
        fall_speed=100.0,
        angle_deg=0.0,
        spin_rpm=10.0,
        scale=1.0,
        texture=_texture(),
    )
    defaults.update(overrides)
    return PowerUpSprite(**defaults)


class TestMotion:
    def test_straight_down_at_zero_angle(self) -> None:
        sprite = _sprite(angle_deg=0.0, fall_speed=100.0)
        assert sprite._vx == pytest.approx(0.0)
        assert sprite._vy == pytest.approx(-100.0)

    def test_positive_angle_drifts_right(self) -> None:
        sprite = _sprite(angle_deg=20.0, fall_speed=100.0)
        assert sprite._vx > 0
        assert sprite._vx == pytest.approx(math.sin(math.radians(20.0)) * 100.0)

    def test_negative_angle_drifts_left(self) -> None:
        sprite = _sprite(angle_deg=-20.0, fall_speed=100.0)
        assert sprite._vx < 0

    def test_update_moves_y_downward(self) -> None:
        sprite = _sprite(angle_deg=0.0, fall_speed=100.0, y=500.0)
        sprite.update(0.5)
        assert sprite.center_y == pytest.approx(450.0)

    def test_update_moves_x_by_vx(self) -> None:
        sprite = _sprite(angle_deg=20.0, fall_speed=100.0, x=100.0)
        start_vx = sprite._vx
        sprite.update(0.5)
        assert sprite.center_x == pytest.approx(100.0 + start_vx * 0.5)


class TestSpin:
    def test_spin_rate_derived_from_rpm(self) -> None:
        # 1 RPM = 6 deg/s
        sprite = _sprite(spin_rpm=10.0)
        assert sprite._spin_rate == pytest.approx(60.0)

    def test_angle_increments_each_frame(self) -> None:
        sprite = _sprite(spin_rpm=10.0)
        sprite.update(1.0)
        assert sprite.angle == pytest.approx(60.0)


class TestLifecycle:
    def test_removes_itself_below_threshold(self) -> None:
        # Put the sprite in a list, let it fall past -height*2
        sprite = _sprite(y=50.0, fall_speed=1000.0)
        sprites = arcade.SpriteList()
        sprites.append(sprite)
        # At height=32, threshold is -64. Fall from y=50 with 1000 px/s,
        # 1 frame of 1 second overshoots comfortably.
        sprite.update(1.0)
        assert sprite not in sprites

    def test_stays_alive_above_threshold(self) -> None:
        sprite = _sprite(y=500.0, fall_speed=100.0)
        sprites = arcade.SpriteList()
        sprites.append(sprite)
        sprite.update(0.1)
        assert sprite in sprites

    def test_effect_type_accessible(self) -> None:
        sprite = _sprite(effect_type="rapid_fire")
        assert sprite.effect_type == "rapid_fire"
