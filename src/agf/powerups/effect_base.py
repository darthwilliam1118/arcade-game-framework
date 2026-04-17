"""PowerUpEffect — abstract base for all power-up effects.

Subclass one of the effect category classes in effect_categories.py
(StatModifierEffect, BehaviorEffect, ConstraintEffect, OverlayEffect,
InstantEffect) rather than this class directly.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class PowerUpEffect(ABC):
    """Abstract base for all power-up effects."""

    @abstractmethod
    def apply(self, ship: Any, context: dict) -> None:
        """Called once when player collects the pickup.

        Modifies ship state. context provides window size, config, etc.
        """

    @abstractmethod
    def update(self, delta_time: float, ship: Any) -> bool:
        """Called every frame while effect is active.

        Returns True while still active, False when expired.
        Never called for instant effects.
        """

    @abstractmethod
    def remove(self, ship: Any, context: dict) -> None:
        """Called when effect expires or is force-removed.

        Restores original ship state.
        """

    @property
    @abstractmethod
    def effect_type(self) -> str:
        """String identifier matching PowerUpType value."""

    @property
    def is_instant(self) -> bool:
        """True for one-shot effects (health restore, extra life).

        Instant effects: apply() is called, update() and remove() are
        never called. Default False.
        """
        return False

    @property
    def remaining_duration(self) -> float:
        """Seconds remaining for HUD display.

        Override in duration-based effects. Default 0.0.
        """
        return 0.0

    @property
    def display_label(self) -> str:
        """Short label for HUD display. Default uses effect_type."""
        return self.effect_type.replace("_", " ").upper()
