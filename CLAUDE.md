# Arcade Game Framework (agf)

## Purpose
Reusable infrastructure for Arcade-based games. Contains no game-specific
logic — ships, enemies, levels, power-ups etc. all live in the game repos.

## Package name
agf — import as `from agf.paths import resource_path` etc.

## What belongs here
- State machine base classes
- Generic views (splash, menu, game over, score entry, level complete)
- Background rendering (static + procedural star field)
- Visual effects (explosion, particles, shockwave)
- UI utilities (text_utils, score_popup, hud base)
- High score persistence
- Music player
- Config base class and loading pattern
- BaseLevel abstraction
- PlayerState, spawn_safety

## What does NOT belong here
- Game-specific sprites (ships, enemies, bullets)
- Game-specific state transitions
- Game-specific config sections
- Game-specific level implementations

## Code Quality Standards
- Formatter: Black (line length 100). Run `black .` before committing.
- Linter: Ruff. Run `ruff check .` and fix all errors before committing.
- Type hints: Use them on all function signatures.
- No unused imports, no bare `except:` clauses.

## Arcade 3.x
This framework targets Arcade 3.x. Do not use Arcade 2.x APIs (e.g.
`arcade.start_render()` — use `self.clear()` instead). Use
`arcade.Text` objects, not `arcade.draw_text()`. See consuming game
CLAUDE.md files for the full 3.x notes.

## Testing
- Use pytest
- All framework classes must be instantiatable without a game window
- Do not load image/sound assets in `__init__` — lazy load or inject them
- Run tests with: `pytest --cov=src/agf`
