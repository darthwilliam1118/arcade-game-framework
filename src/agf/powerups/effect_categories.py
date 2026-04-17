"""Effect category base classes for the power-up system.

Games subclass these rather than PowerUpEffect directly. Each category
has distinct semantics enforced by PowerUpManager:

- StatModifierEffect: fully concrete, multiple allowed at once
- BehaviorEffect: games implement get_bullets(); one active at a time
- ConstraintEffect: games implement apply/restore; one active at a time
- OverlayEffect: games implement overlay sprite + hit absorption; one
  active at a time
- InstantEffect: games implement apply() only; never tracked

No arcade imports at module level — arcade.Sprite type hints are
quoted so tests can import without triggering arcade initialisation.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Any

from agf.powerups.effect_base import PowerUpEffect

if TYPE_CHECKING:
    import arcade


# ----------------------------------------------------------------------
# StatModifierEffect — fully generic, no subclassing needed
# ----------------------------------------------------------------------


class StatModifierEffect(PowerUpEffect):
    """Multiplies or adds to a numeric ship attribute for a duration.

    Fully implemented — games use this directly via configuration,
    no subclassing required for simple stat changes.

    Stores the original attribute value at apply() time (not at
    construction) so stacking multiple modifiers on the same attribute
    compounds correctly: each one captures the value it saw on entry
    and restores exactly that value on remove.
    """

    def __init__(
        self,
        attribute: str,
        duration: float,
        multiplier: float = 1.0,
        additive: float = 0.0,
        effect_type_name: str = "stat_modifier",
        label: str = "",
    ):
        self._attribute = attribute
        self._duration = duration
        self._multiplier = multiplier
        self._additive = additive
        self._effect_type_name = effect_type_name
        self._label = label or effect_type_name.replace("_", " ").upper()
        self._elapsed = 0.0
        self._original: Any = None
        self._applied = False

    @property
    def effect_type(self) -> str:
        return self._effect_type_name

    @property
    def display_label(self) -> str:
        return self._label

    @property
    def remaining_duration(self) -> float:
        return max(0.0, self._duration - self._elapsed)

    def apply(self, ship: Any, context: dict) -> None:
        self._original = getattr(ship, self._attribute)
        new_value = self._original * self._multiplier + self._additive
        if isinstance(self._original, int):
            new_value = int(round(new_value))
        setattr(ship, self._attribute, new_value)
        self._applied = True

    def update(self, delta_time: float, ship: Any) -> bool:
        self._elapsed += delta_time
        return self._elapsed < self._duration

    def remove(self, ship: Any, context: dict) -> None:
        if self._applied:
            setattr(ship, self._attribute, self._original)


# ----------------------------------------------------------------------
# BehaviorEffect — games implement get_bullets()
# ----------------------------------------------------------------------


class BehaviorEffect(PowerUpEffect):
    """Replaces the ship's firing behavior for a duration.

    While active, RunLevelView calls get_bullets() instead of
    ship.try_fire(). Games subclass this to implement alternate firing
    modes: spread shot, triple shot, guided missiles, laser beam, etc.

    Only one BehaviorEffect can be active at a time — PowerUpManager
    enforces this by replacing any existing one on collection.
    """

    def __init__(self, duration: float):
        self._duration = duration
        self._elapsed = 0.0

    @property
    @abstractmethod
    def effect_type(self) -> str: ...

    @property
    def remaining_duration(self) -> float:
        return max(0.0, self._duration - self._elapsed)

    @abstractmethod
    def get_bullets(self, ship: Any) -> list[Any]:
        """Return list of bullet sprites to fire this frame.

        Called by RunLevelView instead of ship.try_fire() while this
        effect is active. Return empty list if on cooldown.
        """

    def apply(self, ship: Any, context: dict) -> None:
        pass

    def update(self, delta_time: float, ship: Any) -> bool:
        self._elapsed += delta_time
        return self._elapsed < self._duration

    def remove(self, ship: Any, context: dict) -> None:
        pass


# ----------------------------------------------------------------------
# ConstraintEffect — games implement apply/restore constraints
# ----------------------------------------------------------------------


class ConstraintEffect(PowerUpEffect):
    """Modifies player ship movement constraints for a duration.

    Games subclass to implement free movement, full rotation, expanded
    movement zone, etc. Only one ConstraintEffect active at a time.
    """

    def __init__(self, duration: float):
        self._duration = duration
        self._elapsed = 0.0
        self._saved_constraints: dict = {}

    @property
    @abstractmethod
    def effect_type(self) -> str: ...

    @property
    def remaining_duration(self) -> float:
        return max(0.0, self._duration - self._elapsed)

    @abstractmethod
    def apply_constraints(self, ship: Any, window_width: int, window_height: int) -> None:
        """Override ship movement zone, rotation limits, etc.

        Save original values to self._saved_constraints for restore.
        """

    @abstractmethod
    def restore_constraints(self, ship: Any) -> None:
        """Restore original constraints from self._saved_constraints."""

    def apply(self, ship: Any, context: dict) -> None:
        w = context.get("window_width", 800)
        h = context.get("window_height", 600)
        self.apply_constraints(ship, w, h)

    def update(self, delta_time: float, ship: Any) -> bool:
        self._elapsed += delta_time
        return self._elapsed < self._duration

    def remove(self, ship: Any, context: dict) -> None:
        self.restore_constraints(ship)


# ----------------------------------------------------------------------
# OverlayEffect — games implement visual overlay + hit absorption
# ----------------------------------------------------------------------


class OverlayEffect(PowerUpEffect):
    """Effect with a persistent visual overlay and hit absorption.

    While active, RunLevelView intercepts damage via on_hit_absorbed()
    instead of calling ship.take_damage(). The overlay sprite is drawn
    centered on the ship each frame. Only one OverlayEffect active at
    a time.
    """

    def __init__(self, duration: float):
        self._duration = duration
        self._elapsed = 0.0
        self._overlay_sprite: "arcade.Sprite | None" = None

    @property
    @abstractmethod
    def effect_type(self) -> str: ...

    @property
    def remaining_duration(self) -> float:
        return max(0.0, self._duration - self._elapsed)

    @abstractmethod
    def create_overlay_sprite(self, scale: float) -> "arcade.Sprite":
        """Return sprite to draw centered on ship each frame.

        Called once on apply(). Store in self._overlay_sprite.
        """

    @abstractmethod
    def on_hit_absorbed(self) -> bool:
        """Called when a hit is intercepted by this overlay.

        Returns True if the overlay is now depleted (should be removed).
        Returns False if overlay still has capacity.
        """

    @abstractmethod
    def update_overlay_sprite(self, ship_x: float, ship_y: float) -> None:
        """Update overlay sprite position and visual state.

        Called every frame from RunLevelView while active.
        """

    def get_overlay_sprite(self) -> "arcade.Sprite | None":
        """Returns the overlay sprite for RunLevelView to draw."""
        return self._overlay_sprite

    def apply(self, ship: Any, context: dict) -> None:
        scale = context.get("sprite_scale", 1.0)
        self._overlay_sprite = self.create_overlay_sprite(scale)

    def update(self, delta_time: float, ship: Any) -> bool:
        self._elapsed += delta_time
        if self._overlay_sprite is not None:
            self.update_overlay_sprite(ship.center_x, ship.center_y)
        return self._elapsed < self._duration

    def remove(self, ship: Any, context: dict) -> None:
        self._overlay_sprite = None


# ----------------------------------------------------------------------
# InstantEffect — games implement apply() only
# ----------------------------------------------------------------------


class InstantEffect(PowerUpEffect):
    """One-shot effect applied immediately on collection.

    apply() is called once. update() and remove() are never called.
    Games subclass to implement health restore, extra life, etc.
    """

    @property
    def is_instant(self) -> bool:
        return True

    @property
    @abstractmethod
    def effect_type(self) -> str: ...

    @abstractmethod
    def apply(self, ship: Any, context: dict) -> None:
        """Apply the instant effect. No state to restore."""

    def update(self, delta_time: float, ship: Any) -> bool:
        return False

    def remove(self, ship: Any, context: dict) -> None:
        pass
