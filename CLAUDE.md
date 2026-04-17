# Arcade Game Framework (agf) — Claude Code Guidelines

## Purpose
agf is a reusable game infrastructure package for Arcade-based Python games.
It contains no game-specific logic. Ships, enemies, levels, power-up effects,
and game-specific assets all live in the game repos that depend on agf.

## Package structure
src/agf/ is the package root. Import as:
  from agf.paths import resource_path
  from agf.powerups.manager import PowerUpManager
  etc.

## What belongs in agf
- State machine base classes (BaseGameStateManager)
- Generic views (splash, main menu, game over, score entry, level complete)
- Background rendering (StaticBackground, ProceduralStarField)
- Visual effects (ExplosionSprite, ParticleEmitter, ShockwaveSprite)
- UI utilities (text_utils, ScorePopup, HUDBase)
- High score persistence (HighScoreTable)
- Music player (MusicPlayer)
- Config base class and TOML loading pattern (BaseGameConfig)
- BaseLevel abstraction
- PlayerState, spawn_safety
- Power-up infrastructure (effect categories, spawner, manager, sprite)

## What does NOT belong in agf
- Game-specific sprites (player ships, enemies, bullets)
- Game-specific state transitions or view logic
- Game-specific config sections (ShipConfig, EnemyConfig, etc.)
- Game-specific level implementations
- Any asset files (no images, sounds, or fonts live here)
- Any hardcoded asset paths

## Architecture principles
- All classes must be instantiatable without a display for unit testing
  Use TYPE_CHECKING guards for arcade type hints at module level
  Accept pre-loaded textures/sounds as optional constructor parameters
- No arcade imports at module level in base classes — import inside
  methods or use TYPE_CHECKING so tests don't trigger arcade init
- Effect base classes define contracts only — no game logic
- PowerUpManager.create_effect() raises NotImplementedError by design
  Games MUST subclass and override it

## Power-up system
See docs/agf-powerups.md and docs/powerups-delta.md for full spec.

Key contracts:
- PowerUpSprite spawns above window top (y = window_height + offset)
- Fall speed is randomised per sprite within fall_speed_min/fall_speed_max
- Fall angle is randomised within +/- fall_angle_max degrees
- Sprites rotate at spin_rpm while falling
- Spawn interval uses exponential decay curve (not linear step)
- Level 1 always produces empty weight table — no spawns
- Types unlock one per level from level 2 onward (game defines order)

Effect category rules enforced by PowerUpManager:
- One BehaviorEffect active at a time (new one replaces old)
- One ConstraintEffect active at a time
- One OverlayEffect active at a time
- Multiple StatModifierEffects allowed simultaneously
- InstantEffects are applied immediately, never tracked

## Arcade version
Arcade 3.3.x — see Space Attackers CLAUDE.md for full 3.x API notes.
Same rules apply here.

## Testing
- All tests must run without a display (no arcade.Window needed)
- pytest with --cov=src
- Tests live in tests/ at project root
- No test should import game-specific code

## Code style
- Python 3.11+
- Type hints on all public methods and properties
- Black formatting, Ruff linting
- Commit via terminal (not VS Code UI) to trigger pre-commit hooks

## CI
GitHub Actions: lint (Black + Ruff) then test — no PyInstaller build
agf is a library, not an executable

## Dependency
Games install agf via:
  pip install -e "arcade-game-framework @ git+https://github.com/darthwilliam1118/arcade-game-framework@main"
Pin to a tag once stable rather than @main

## Adding new features
Before adding anything, ask: is this truly generic?
If it references a specific game mechanic, asset type, or game state
it does not belong in agf. When in doubt, put it in the game repo
and extract later once the pattern is proven reusable.