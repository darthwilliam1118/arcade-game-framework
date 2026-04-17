"""PowerUpManager — owns falling pickup sprites and active effects.

Lives on BaseLevel subclasses. Level calls update() and draw() each
frame. RunLevelView queries typed getters for effect-category-specific
behaviour (firing override, damage interception, etc.).

Games subclass and override:
  create_spawner() — return a game-specific PowerUpSpawner subclass
  create_sprite()  — return a PowerUpSprite with game asset texture
  create_effect()  — map effect_type string to PowerUpEffect instance

No arcade imports at module level — arcade is imported inside methods
that need it so tests can import this module without triggering arcade
initialisation.
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Any

from agf.powerups.config import PowerUpConfigBase
from agf.powerups.effect_base import PowerUpEffect
from agf.powerups.effect_categories import (
    BehaviorEffect,
    ConstraintEffect,
    OverlayEffect,
)
from agf.powerups.powerup_sprite import PowerUpSprite
from agf.powerups.spawner import PowerUpSpawner

if TYPE_CHECKING:
    import arcade


class PowerUpManager:
    """Owns the falling pickup sprites and the list of active effects."""

    def __init__(
        self,
        config: PowerUpConfigBase,
        window_width: int,
        window_height: int,
        sprite_scale: float = 1.0,
    ):
        import arcade

        self._config = config
        self._window_width = window_width
        self._window_height = window_height
        self._scale = sprite_scale
        self._spawner: PowerUpSpawner = self.create_spawner()
        self._sprites: "arcade.SpriteList" = arcade.SpriteList()
        self._active_effects: list[PowerUpEffect] = []

    # ------------------------------------------------------------------
    # Overridable factory methods
    # ------------------------------------------------------------------

    def create_spawner(self) -> PowerUpSpawner:
        """Return a PowerUpSpawner instance.

        Override to return a game-specific subclass.
        """
        return PowerUpSpawner(self._config)

    def create_sprite(self, effect_type: str, x: float, y: float) -> PowerUpSprite:
        """Return a PowerUpSprite for the given effect_type.

        The `y` parameter is ignored — sprites always spawn above the
        window at window_height + spawn_height_offset. Override to load
        game-specific textures per type.
        """
        cfg = self._config
        fall_speed = random.uniform(cfg.fall_speed_min, cfg.fall_speed_max)
        angle_deg = random.uniform(-cfg.fall_angle_max, cfg.fall_angle_max)
        spawn_y = self._window_height + cfg.spawn_height_offset
        return PowerUpSprite(
            x=x,
            y=spawn_y,
            effect_type=effect_type,
            fall_speed=fall_speed,
            angle_deg=angle_deg,
            spin_rpm=cfg.spin_rpm,
            scale=self._scale,
            texture=None,
        )

    def create_effect(self, effect_type: str) -> PowerUpEffect:
        """Map effect_type string to a PowerUpEffect instance.

        Games MUST override. Raising here is a deliberate contract.
        """
        raise NotImplementedError(
            f"PowerUpManager.create_effect() not implemented "
            f"for effect_type={effect_type!r}. "
            f"Override create_effect() in your game's PowerUpManager subclass."
        )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def setup(self, level_number: int, level_type: str) -> None:
        self._spawner.setup(level_number, level_type)

    # ------------------------------------------------------------------
    # Per-frame
    # ------------------------------------------------------------------

    def update(
        self,
        delta_time: float,
        player_ship: Any,
        context: dict,
        enemy_x_positions: list[float],
    ) -> list[str]:
        """Tick spawner, move sprites, detect collection, tick effects.

        Returns effect_type strings for effects collected this frame
        (for GameEvent generation in RunLevelView). player_ship may be
        None during the death sequence — all ship accesses are guarded.
        """
        import arcade

        collected: list[str] = []

        spawn_type = self._spawner.update(delta_time)
        if spawn_type is not None:
            x = self._pick_spawn_x(enemy_x_positions)
            sprite = self.create_sprite(spawn_type, x, self._window_height - 10)
            self._sprites.append(sprite)

        for sprite in list(self._sprites):
            sprite.update(delta_time)

        if player_ship is not None and not player_ship.is_invincible():
            hits = arcade.check_for_collision_with_list(player_ship, self._sprites)
            for hit in hits:
                hit.remove_from_sprite_lists()
                effect = self.create_effect(hit.effect_type)
                self._add_effect(effect, player_ship, context)
                collected.append(hit.effect_type)

        expired: list[PowerUpEffect] = []
        for effect in self._active_effects:
            if not effect.update(delta_time, player_ship):
                expired.append(effect)
        for effect in expired:
            self.remove_effect(effect, player_ship, context)

        return collected

    def draw(self) -> None:
        """Draw falling pickup sprites.

        Overlay sprites are drawn by RunLevelView via get_active_overlay().
        """
        self._sprites.draw()

    # ------------------------------------------------------------------
    # Effect management
    # ------------------------------------------------------------------

    def _add_effect(self, effect: PowerUpEffect, ship: Any, context: dict) -> None:
        """Add effect, enforcing one-per-category rules."""
        if effect.is_instant:
            effect.apply(ship, context)
            return

        if isinstance(effect, BehaviorEffect):
            for existing in list(self._active_effects):
                if isinstance(existing, BehaviorEffect):
                    self.remove_effect(existing, ship, context)

        if isinstance(effect, ConstraintEffect):
            for existing in list(self._active_effects):
                if isinstance(existing, ConstraintEffect):
                    self.remove_effect(existing, ship, context)

        if isinstance(effect, OverlayEffect):
            for existing in list(self._active_effects):
                if isinstance(existing, OverlayEffect):
                    self.remove_effect(existing, ship, context)

        effect.apply(ship, context)
        self._active_effects.append(effect)

    def remove_effect(
        self,
        effect: PowerUpEffect,
        ship: Any = None,
        context: dict | None = None,
    ) -> None:
        """Force-remove an effect (e.g. overlay depleted by hit)."""
        if effect in self._active_effects:
            if ship is not None:
                effect.remove(ship, context or {})
            self._active_effects.remove(effect)

    def clear_all(self, ship: Any = None, context: dict | None = None) -> None:
        """Remove all sprites and cancel all active effects.

        Call on player death.
        """
        self._sprites.clear()
        for effect in list(self._active_effects):
            if ship is not None:
                effect.remove(ship, context or {})
        self._active_effects.clear()

    # ------------------------------------------------------------------
    # Typed getters — used by RunLevelView
    # ------------------------------------------------------------------

    def get_active_behavior(self) -> BehaviorEffect | None:
        for e in self._active_effects:
            if isinstance(e, BehaviorEffect):
                return e
        return None

    def get_active_overlay(self) -> OverlayEffect | None:
        for e in self._active_effects:
            if isinstance(e, OverlayEffect):
                return e
        return None

    def get_active_constraint(self) -> ConstraintEffect | None:
        for e in self._active_effects:
            if isinstance(e, ConstraintEffect):
                return e
        return None

    def get_active_effects(self) -> list[PowerUpEffect]:
        """All active effects. Used by HUD for display."""
        return list(self._active_effects)

    # ------------------------------------------------------------------
    # Snapshot
    # ------------------------------------------------------------------

    def to_snapshot(self) -> dict:
        """Serialise spawner timer state for 2P switching.

        Active effects are NOT preserved across player switches.
        """
        return {
            "spawner_timer": self._spawner.timer,
            "spawner_interval": self._spawner.current_interval,
        }

    @classmethod
    def from_snapshot(
        cls,
        snapshot: dict,
        config: PowerUpConfigBase,
        window_width: int,
        window_height: int,
        sprite_scale: float = 1.0,
        level_number: int = 1,
        level_type: str = "standard",
    ) -> "PowerUpManager":
        manager = cls(config, window_width, window_height, sprite_scale)
        manager.setup(level_number, level_type)
        manager._spawner.timer = snapshot.get("spawner_timer", 0.0)
        manager._spawner._interval = snapshot.get(
            "spawner_interval", manager._spawner.current_interval
        )
        return manager

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _pick_spawn_x(self, enemy_positions: list[float]) -> float:
        """Spawn beneath a random living enemy if any, else random x."""
        if enemy_positions:
            return random.choice(enemy_positions)
        margin = 40
        return random.uniform(margin, self._window_width - margin)
