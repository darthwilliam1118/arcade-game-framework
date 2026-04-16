"""BaseGameStateManager - generic state-machine scaffold.

Games subclass BaseGameStateManager, supply their own GameState ``Enum``
as the initial state, and override ``_enter_state`` with match/case logic
that swaps Arcade views (or runs logic-only handlers).  The base handles
bookkeeping: current state, mutable context dict, transition log line.
"""

from __future__ import annotations

import logging
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import arcade

log = logging.getLogger(__name__)


class BaseGameStateManager:
    """Owns the current state and a mutable context dict.

    Subclasses pass the initial state to ``__init__`` and override
    ``_enter_state`` to handle each state transition.
    """

    def __init__(self, window: "arcade.Window", initial_state: Enum) -> None:
        self.window = window
        self.state: Enum = initial_state
        self.context: dict[str, Any] = {}

    def transition(self, new_state: Enum, **context: Any) -> None:
        """Move to *new_state*, merging any *context* into the existing context."""
        log.debug("State: %s -> %s  ctx=%s", self.state.name, new_state.name, context)
        self.state = new_state
        self.context.update(context)
        self._enter_state(new_state)

    def _enter_state(self, state: Enum) -> None:
        """Handle entering *state*.  Subclasses must override."""
        raise NotImplementedError
