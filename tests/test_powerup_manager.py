"""Unit tests for PowerUpManager — no display required."""

from __future__ import annotations

from typing import Any

import arcade
import pytest

from agf.powerups.config import PowerUpConfigBase
from agf.powerups.effect_base import PowerUpEffect
from agf.powerups.effect_categories import (
    BehaviorEffect,
    ConstraintEffect,
    InstantEffect,
    OverlayEffect,
    StatModifierEffect,
)
from agf.powerups.manager import PowerUpManager

# ----------------------------------------------------------------------
# Fakes
# ----------------------------------------------------------------------


class _FakeBehavior(BehaviorEffect):
    def __init__(self, duration: float = 5.0) -> None:
        super().__init__(duration)
        self.applied = False
        self.removed = False

    @property
    def effect_type(self) -> str:
        return "fake_behavior"

    def get_bullets(self, ship: Any) -> list[Any]:
        return []

    def apply(self, ship: Any, context: dict) -> None:
        self.applied = True

    def remove(self, ship: Any, context: dict) -> None:
        self.removed = True


class _FakeConstraint(ConstraintEffect):
    def __init__(self, duration: float = 5.0) -> None:
        super().__init__(duration)
        self.removed = False

    @property
    def effect_type(self) -> str:
        return "fake_constraint"

    def apply_constraints(self, ship: Any, window_width: int, window_height: int) -> None:
        pass

    def restore_constraints(self, ship: Any) -> None:
        self.removed = True


class _FakeOverlay(OverlayEffect):
    def __init__(self, duration: float = 5.0) -> None:
        super().__init__(duration)

    @property
    def effect_type(self) -> str:
        return "fake_overlay"

    def create_overlay_sprite(self, scale: float) -> Any:
        return object()

    def on_hit_absorbed(self) -> bool:
        return False

    def update_overlay_sprite(self, ship_x: float, ship_y: float) -> None:
        pass


class _FakeInstant(InstantEffect):
    def __init__(self) -> None:
        self.applied = False

    @property
    def effect_type(self) -> str:
        return "fake_instant"

    def apply(self, ship: Any, context: dict) -> None:
        self.applied = True


class _Ship(arcade.Sprite):
    """Real arcade.Sprite so collision-list checks accept it."""

    def __init__(self) -> None:
        texture = arcade.Texture.create_empty("ship", (16, 16))
        super().__init__(path_or_texture=texture)
        self.center_x = 400.0
        self.center_y = 300.0

    def is_invincible(self) -> bool:
        return False


class _TestManager(PowerUpManager):
    """PowerUpManager with a create_effect() mapping for tests."""

    def __init__(self, *args, effect_map: dict[str, PowerUpEffect] | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._effect_map = effect_map or {}

    def create_effect(self, effect_type: str) -> PowerUpEffect:
        return self._effect_map[effect_type]


def _manager(**kwargs) -> _TestManager:
    cfg = PowerUpConfigBase(spawn_interval_jitter=0.0)
    return _TestManager(cfg, window_width=800, window_height=600, **kwargs)


# ----------------------------------------------------------------------
# One-per-category enforcement
# ----------------------------------------------------------------------


class TestCategoryReplacement:
    def test_behavior_replaces_existing_behavior(self) -> None:
        mgr = _manager()
        first = _FakeBehavior()
        second = _FakeBehavior()
        ship = _Ship()
        mgr._add_effect(first, ship, {})
        mgr._add_effect(second, ship, {})
        assert first.removed is True
        active = mgr.get_active_effects()
        assert first not in active
        assert second in active

    def test_constraint_replaces_existing_constraint(self) -> None:
        mgr = _manager()
        first = _FakeConstraint()
        second = _FakeConstraint()
        ship = _Ship()
        mgr._add_effect(first, ship, {"window_width": 800, "window_height": 600})
        mgr._add_effect(second, ship, {"window_width": 800, "window_height": 600})
        assert first.removed is True
        assert mgr.get_active_constraint() is second

    def test_overlay_replaces_existing_overlay(self) -> None:
        mgr = _manager()
        first = _FakeOverlay()
        second = _FakeOverlay()
        ship = _Ship()
        mgr._add_effect(first, ship, {"sprite_scale": 1.0})
        mgr._add_effect(second, ship, {"sprite_scale": 1.0})
        assert mgr.get_active_overlay() is second
        assert first not in mgr.get_active_effects()

    def test_multiple_stat_modifiers_coexist(self) -> None:
        mgr = _manager()
        ship = type("S", (), {"a": 1.0, "b": 2.0})()
        first = StatModifierEffect("a", duration=5.0, multiplier=2.0)
        second = StatModifierEffect("b", duration=5.0, multiplier=3.0)
        mgr._add_effect(first, ship, {})
        mgr._add_effect(second, ship, {})
        active = mgr.get_active_effects()
        assert first in active
        assert second in active

    def test_instant_applied_not_tracked(self) -> None:
        mgr = _manager()
        effect = _FakeInstant()
        mgr._add_effect(effect, _Ship(), {})
        assert effect.applied is True
        assert effect not in mgr.get_active_effects()


# ----------------------------------------------------------------------
# Effect lifecycle
# ----------------------------------------------------------------------


class TestEffectLifecycle:
    def test_remove_effect_calls_remove_on_ship(self) -> None:
        mgr = _manager()
        effect = _FakeBehavior()
        ship = _Ship()
        mgr._add_effect(effect, ship, {})
        mgr.remove_effect(effect, ship, {})
        assert effect.removed is True
        assert effect not in mgr.get_active_effects()

    def test_remove_effect_noop_when_not_active(self) -> None:
        mgr = _manager()
        effect = _FakeBehavior()
        mgr.remove_effect(effect, _Ship(), {})  # should not raise

    def test_clear_all_empties_sprites_and_effects(self) -> None:
        mgr = _manager()
        ship = _Ship()
        b = _FakeBehavior()
        c = _FakeConstraint()
        mgr._add_effect(b, ship, {"window_width": 800, "window_height": 600})
        mgr._add_effect(c, ship, {"window_width": 800, "window_height": 600})
        mgr.clear_all(ship, {})
        assert mgr.get_active_effects() == []
        assert b.removed is True
        assert c.removed is True


# ----------------------------------------------------------------------
# Typed getters
# ----------------------------------------------------------------------


class TestTypedGetters:
    def test_get_active_behavior_none_when_absent(self) -> None:
        assert _manager().get_active_behavior() is None

    def test_get_active_overlay_none_when_absent(self) -> None:
        assert _manager().get_active_overlay() is None

    def test_get_active_constraint_none_when_absent(self) -> None:
        assert _manager().get_active_constraint() is None

    def test_returns_active_instance(self) -> None:
        mgr = _manager()
        behavior = _FakeBehavior()
        mgr._add_effect(behavior, _Ship(), {})
        assert mgr.get_active_behavior() is behavior


# ----------------------------------------------------------------------
# create_effect contract
# ----------------------------------------------------------------------


class TestCreateEffectContract:
    def test_base_raises_not_implemented(self) -> None:
        cfg = PowerUpConfigBase()
        mgr = PowerUpManager(cfg, window_width=800, window_height=600)
        with pytest.raises(NotImplementedError):
            mgr.create_effect("anything")


# ----------------------------------------------------------------------
# Snapshot
# ----------------------------------------------------------------------


class TestSnapshot:
    def test_to_snapshot_captures_timer_and_interval(self) -> None:
        mgr = _manager()
        mgr.setup(level_number=3, level_type="standard")
        mgr._spawner.timer = 4.5
        snap = mgr.to_snapshot()
        assert snap["spawner_timer"] == pytest.approx(4.5)
        assert snap["spawner_interval"] == pytest.approx(mgr._spawner.current_interval)

    def test_from_snapshot_restores_timer_and_interval(self) -> None:
        cfg = PowerUpConfigBase(spawn_interval_jitter=0.0)
        snap = {"spawner_timer": 7.25, "spawner_interval": 12.5}
        restored = _TestManager.from_snapshot(
            snap, cfg, window_width=800, window_height=600, level_number=4
        )
        assert restored._spawner.timer == pytest.approx(7.25)
        assert restored._spawner.current_interval == pytest.approx(12.5)


# ----------------------------------------------------------------------
# Update path — effect expiry
# ----------------------------------------------------------------------


class TestEffectExpiry:
    def test_expired_effect_removed(self) -> None:
        mgr = _manager()
        ship = _Ship()
        effect = _FakeBehavior(duration=0.5)
        mgr._add_effect(effect, ship, {})
        mgr.update(delta_time=1.0, player_ship=ship, context={}, enemy_x_positions=[])
        assert effect.removed is True
        assert effect not in mgr.get_active_effects()
