"""WorldSpacePowerUpSpawner - spawns power-up sprites at world coordinates.

Unlike the base PowerUpSpawner (which spawns at screen-top in screen
space), this spawner places sprites within the current camera view
window at world coordinates. Sprites drift downward at a randomised
speed and are culled when they contact the floor terrain or exit the
left edge of the camera view.

This class is intentionally agf-generic - it knows nothing about any
specific game's terrain, enemies, or game state. The game passes in:
  - a weight table (effect_type -> weight) built per-level
  - a camera_rect callback returning (cam_left, cam_bottom, cam_right, cam_top)
    in world coordinates each frame
  - a floor_y_at(world_x) callback for terrain floor lookup
  - spawn_interval computed externally (level-keyed)

Design notes:
  - Spawning is time-based; spawn_interval is set by the game per level.
  - Sprites spawn at a random world X within the camera view and at
    cam_top + a small offset so they appear to fall from the sky.
  - Sprites drift straight downward at a per-sprite fall_speed (px/s).
    The spawner owns vertical motion - PowerUpSprite is constructed
    with fall_speed=0 so its internal velocity does not double-move it.
  - Sprites are culled when center_y <= floor_y_at(center_x) OR when
    center_x < cam_left - cull_margin (scrolled off left edge).
  - SpriteList does NOT use spatial hashing - power-ups move every frame.
  - Parallel lists track per-sprite fall speed and effect type, in the
    same pattern as agf.background.star_field.ProceduralStarField.
"""
from __future__ import annotations

import random
from collections.abc import Callable

import arcade


class WorldSpacePowerUpSpawner:
    """Manages timed spawning and lifetime of world-space power-up sprites.

    Parameters
    ----------
    weight_table:
        Dict mapping power-up effect type (str) to spawn weight (int).
        Empty dict = no spawns (used for level 1).
    camera_rect:
        Callable returning (cam_left, cam_bottom, cam_right, cam_top)
        in world coordinates. Called each frame during update.
    floor_y_at:
        Callable(world_x: float) -> float returning the terrain floor Y
        at a given world X. Used for floor-contact culling.
    spawn_interval:
        Seconds between spawn attempts. Set by game per level.
    fall_speed_min / fall_speed_max:
        Randomised downward drift speed range (px/s).
    sprite_scale:
        Arcade sprite scale passed to PowerUpSprite.
    spin_rpm:
        Sprite rotation speed in RPM. Only takes effect if the game
        calls sprite_list.update() each frame; the spawner does not.
    cull_margin:
        Extra px past cam_left before a sprite is culled (default 64).
    """

    def __init__(
        self,
        weight_table: dict[str, int],
        camera_rect: Callable[[], tuple[float, float, float, float]],
        floor_y_at: Callable[[float], float],
        spawn_interval: float,
        fall_speed_min: float = 40.0,
        fall_speed_max: float = 100.0,
        sprite_scale: float = 1.0,
        spin_rpm: float = 10.0,
        cull_margin: float = 64.0,
    ) -> None:
        self._weights = weight_table
        self._camera_rect = camera_rect
        self._floor_y_at = floor_y_at
        self.spawn_interval: float = spawn_interval
        self._fall_speed_min = fall_speed_min
        self._fall_speed_max = fall_speed_max
        self._sprite_scale = sprite_scale
        self._spin_rpm = spin_rpm
        self._cull_margin = cull_margin

        # Start at a random offset so reloads don't all spawn at t=0.
        self._timer: float = random.uniform(0.0, spawn_interval)

        self.sprite_list: arcade.SpriteList = arcade.SpriteList()
        # Parallel lists - SpriteList has no per-sprite metadata.
        # Same pattern as agf.background.star_field.ProceduralStarField.
        self._fall_speeds: list[float] = []
        self._type_names: list[str] = []

    # ---- public API ------------------------------------------------

    def update(self, delta_time: float) -> None:
        """Tick the spawn timer and move/cull active sprites."""
        if not self._weights:
            return

        cam_left, _, _, _ = self._camera_rect()

        # Move sprites downward and cull. Iterate by index in reverse so
        # in-place removal stays consistent with the parallel lists.
        for i in range(len(self.sprite_list) - 1, -1, -1):
            sprite = self.sprite_list[i]
            speed = self._fall_speeds[i]
            sprite.center_y -= speed * delta_time

            floor_y = self._floor_y_at(sprite.center_x)
            if sprite.center_y <= floor_y:
                self._remove_at(i)
                continue
            if sprite.center_x < cam_left - self._cull_margin:
                self._remove_at(i)

        # Spawn timer.
        self._timer -= delta_time
        if self._timer <= 0.0:
            self._timer = self.spawn_interval
            self._try_spawn()

    def collect(self, sprite: arcade.Sprite) -> str | None:
        """Remove sprite from the list and return its effect type, or None
        if it is not managed by this spawner. Called by the game on
        collision with the player ship.
        """
        for i, managed in enumerate(self.sprite_list):
            if managed is sprite:
                type_name = self._type_names[i]
                self._remove_at(i)
                return type_name
        return None

    def clear(self) -> None:
        """Remove all active sprites - call on level end or game over."""
        for sprite in list(self.sprite_list):
            sprite.remove_from_sprite_lists()
        self._fall_speeds.clear()
        self._type_names.clear()

    # ---- internals -------------------------------------------------

    def _try_spawn(self) -> None:
        """Pick a type by weight and spawn one sprite within the camera view."""
        type_name = self._weighted_choice()
        if type_name is None:
            return
        cam_left, _cam_bottom, cam_right, cam_top = self._camera_rect()
        if cam_right - cam_left < 64.0:
            return
        spawn_x = random.uniform(cam_left + 32.0, cam_right - 32.0)
        spawn_y = cam_top + 16.0
        self._spawn_sprite(type_name, spawn_x, spawn_y)

    def _spawn_sprite(self, type_name: str, x: float, y: float) -> None:
        """Instantiate a PowerUpSprite and add it to the managed list."""
        from agf.powerups.powerup_sprite import PowerUpSprite

        sprite = PowerUpSprite(
            x=x,
            y=y,
            effect_type=type_name,
            fall_speed=0.0,
            angle_deg=0.0,
            spin_rpm=self._spin_rpm,
            scale=self._sprite_scale,
        )
        speed = random.uniform(self._fall_speed_min, self._fall_speed_max)
        self.sprite_list.append(sprite)
        self._fall_speeds.append(speed)
        self._type_names.append(type_name)

    def _remove_at(self, index: int) -> None:
        """Remove the sprite at index from the sprite list and metadata lists."""
        sprite = self.sprite_list[index]
        sprite.remove_from_sprite_lists()
        del self._fall_speeds[index]
        del self._type_names[index]

    def _weighted_choice(self) -> str | None:
        """Return an effect type sampled by weight, or None if table is empty."""
        if not self._weights:
            return None
        names = list(self._weights.keys())
        weights = list(self._weights.values())
        return random.choices(names, weights=weights, k=1)[0]
