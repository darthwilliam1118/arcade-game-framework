"""Unit tests for effect category base classes — no display required."""

from __future__ import annotations

from typing import Any

import pytest

from agf.powerups.effect_categories import (
    BehaviorEffect,
    ConstraintEffect,
    InstantEffect,
    OverlayEffect,
    StatModifierEffect,
)


class _Ship:
    """Minimal stand-in for a ship with arbitrary attributes."""

    def __init__(self, **attrs: Any) -> None:
        for k, v in attrs.items():
            setattr(self, k, v)


# ----------------------------------------------------------------------
# StatModifierEffect
# ----------------------------------------------------------------------


class TestStatModifier:
    def test_apply_multiplies_attribute(self) -> None:
        ship = _Ship(fire_cooldown=0.5)
        effect = StatModifierEffect("fire_cooldown", duration=8.0, multiplier=0.4)
        effect.apply(ship, {})
        assert ship.fire_cooldown == pytest.approx(0.2)

    def test_apply_preserves_int_type(self) -> None:
        ship = _Ship(damage=3)
        effect = StatModifierEffect("damage", duration=8.0, multiplier=2.0)
        effect.apply(ship, {})
        assert ship.damage == 6
        assert isinstance(ship.damage, int)

    def test_additive_applies_after_multiplier(self) -> None:
        ship = _Ship(speed=10.0)
        effect = StatModifierEffect("speed", duration=5.0, multiplier=2.0, additive=1.0)
        effect.apply(ship, {})
        # 10 * 2 + 1 = 21
        assert ship.speed == pytest.approx(21.0)

    def test_update_active_before_duration(self) -> None:
        ship = _Ship(x=1.0)
        effect = StatModifierEffect("x", duration=2.0, multiplier=2.0)
        effect.apply(ship, {})
        assert effect.update(1.0, ship) is True

    def test_update_expires_after_duration(self) -> None:
        ship = _Ship(x=1.0)
        effect = StatModifierEffect("x", duration=2.0, multiplier=2.0)
        effect.apply(ship, {})
        effect.update(1.5, ship)
        assert effect.update(1.0, ship) is False

    def test_remove_restores_original(self) -> None:
        ship = _Ship(fire_cooldown=0.5)
        effect = StatModifierEffect("fire_cooldown", duration=8.0, multiplier=0.4)
        effect.apply(ship, {})
        effect.remove(ship, {})
        assert ship.fire_cooldown == pytest.approx(0.5)

    def test_stacked_modifiers_restore_in_reverse(self) -> None:
        """Two modifiers on the same attribute should each capture the
        value they saw on apply() and restore it on remove()."""
        ship = _Ship(speed=10.0)
        first = StatModifierEffect("speed", duration=5.0, multiplier=2.0)
        second = StatModifierEffect("speed", duration=5.0, multiplier=1.5)
        first.apply(ship, {})
        second.apply(ship, {})
        assert ship.speed == pytest.approx(30.0)
        second.remove(ship, {})
        assert ship.speed == pytest.approx(20.0)
        first.remove(ship, {})
        assert ship.speed == pytest.approx(10.0)

    def test_remaining_duration(self) -> None:
        ship = _Ship(x=1.0)
        effect = StatModifierEffect("x", duration=3.0, multiplier=2.0)
        effect.apply(ship, {})
        effect.update(1.0, ship)
        assert effect.remaining_duration == pytest.approx(2.0)


# ----------------------------------------------------------------------
# BehaviorEffect
# ----------------------------------------------------------------------


class _FakeBehavior(BehaviorEffect):
    @property
    def effect_type(self) -> str:
        return "fake_behavior"

    def get_bullets(self, ship: Any) -> list[Any]:
        return []


class TestBehaviorEffect:
    def test_update_expires_after_duration(self) -> None:
        effect = _FakeBehavior(duration=1.0)
        assert effect.update(0.5, None) is True
        assert effect.update(0.6, None) is False

    def test_is_instant_false(self) -> None:
        assert _FakeBehavior(1.0).is_instant is False

    def test_remaining_duration_decreases(self) -> None:
        effect = _FakeBehavior(duration=2.0)
        effect.update(0.5, None)
        assert effect.remaining_duration == pytest.approx(1.5)


# ----------------------------------------------------------------------
# ConstraintEffect
# ----------------------------------------------------------------------


class _FakeConstraint(ConstraintEffect):
    def __init__(self, duration: float) -> None:
        super().__init__(duration)
        self.applied_with: tuple[Any, int, int] | None = None
        self.restored = False

    @property
    def effect_type(self) -> str:
        return "fake_constraint"

    def apply_constraints(self, ship: Any, window_width: int, window_height: int) -> None:
        self.applied_with = (ship, window_width, window_height)

    def restore_constraints(self, ship: Any) -> None:
        self.restored = True


class TestConstraintEffect:
    def test_apply_forwards_window_dimensions(self) -> None:
        effect = _FakeConstraint(2.0)
        ship = _Ship()
        effect.apply(ship, {"window_width": 1280, "window_height": 960})
        assert effect.applied_with == (ship, 1280, 960)

    def test_remove_calls_restore(self) -> None:
        effect = _FakeConstraint(2.0)
        ship = _Ship()
        effect.apply(ship, {"window_width": 800, "window_height": 600})
        effect.remove(ship, {})
        assert effect.restored is True

    def test_update_expires_after_duration(self) -> None:
        effect = _FakeConstraint(1.0)
        assert effect.update(0.5, None) is True
        assert effect.update(0.6, None) is False


# ----------------------------------------------------------------------
# OverlayEffect
# ----------------------------------------------------------------------


class _FakeSprite:
    def __init__(self) -> None:
        self.center_x = 0.0
        self.center_y = 0.0


class _FakeOverlay(OverlayEffect):
    def __init__(self, duration: float) -> None:
        super().__init__(duration)
        self.scale_passed: float | None = None
        self.update_calls: list[tuple[float, float]] = []
        self.absorbed_hits = 0

    @property
    def effect_type(self) -> str:
        return "fake_overlay"

    def create_overlay_sprite(self, scale: float) -> Any:
        self.scale_passed = scale
        return _FakeSprite()

    def on_hit_absorbed(self) -> bool:
        self.absorbed_hits += 1
        return True

    def update_overlay_sprite(self, ship_x: float, ship_y: float) -> None:
        self.update_calls.append((ship_x, ship_y))
        if self._overlay_sprite is not None:
            self._overlay_sprite.center_x = ship_x
            self._overlay_sprite.center_y = ship_y


class TestOverlayEffect:
    def test_apply_creates_sprite_with_scale(self) -> None:
        effect = _FakeOverlay(3.0)
        effect.apply(_Ship(), {"sprite_scale": 1.5})
        assert effect.scale_passed == pytest.approx(1.5)
        assert effect.get_overlay_sprite() is not None

    def test_update_forwards_ship_position(self) -> None:
        effect = _FakeOverlay(3.0)
        effect.apply(_Ship(), {"sprite_scale": 1.0})
        ship = _Ship(center_x=123.0, center_y=456.0)
        effect.update(0.1, ship)
        assert effect.update_calls[-1] == (123.0, 456.0)

    def test_remove_clears_sprite(self) -> None:
        effect = _FakeOverlay(3.0)
        effect.apply(_Ship(), {"sprite_scale": 1.0})
        effect.remove(_Ship(), {})
        assert effect.get_overlay_sprite() is None

    def test_update_expires_after_duration(self) -> None:
        effect = _FakeOverlay(1.0)
        effect.apply(_Ship(), {"sprite_scale": 1.0})
        ship = _Ship(center_x=0.0, center_y=0.0)
        assert effect.update(0.5, ship) is True
        assert effect.update(0.6, ship) is False


# ----------------------------------------------------------------------
# InstantEffect
# ----------------------------------------------------------------------


class _FakeInstant(InstantEffect):
    def __init__(self) -> None:
        self.applied = False

    @property
    def effect_type(self) -> str:
        return "fake_instant"

    def apply(self, ship: Any, context: dict) -> None:
        self.applied = True


class TestInstantEffect:
    def test_is_instant_true(self) -> None:
        assert _FakeInstant().is_instant is True

    def test_update_always_returns_false(self) -> None:
        effect = _FakeInstant()
        assert effect.update(0.1, None) is False
        assert effect.update(99.0, None) is False

    def test_remove_is_noop(self) -> None:
        _FakeInstant().remove(None, {})  # should not raise

    def test_apply_runs(self) -> None:
        effect = _FakeInstant()
        effect.apply(_Ship(), {})
        assert effect.applied is True
