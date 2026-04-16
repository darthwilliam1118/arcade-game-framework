"""Unit tests for BaseGameStateManager - no display required."""

from __future__ import annotations

from enum import Enum, auto
from typing import Any

import pytest

from agf.state import BaseGameStateManager


class _State(Enum):
    A = auto()
    B = auto()
    C = auto()


class _FakeWindow:
    pass


class _Manager(BaseGameStateManager):
    def __init__(self, window: Any) -> None:
        super().__init__(window, _State.A)
        self.visited: list[_State] = []

    def _enter_state(self, state: Enum) -> None:  # type: ignore[override]
        assert isinstance(state, _State)
        self.visited.append(state)


class TestTransition:
    def test_initial_state_set(self) -> None:
        m = _Manager(_FakeWindow())
        assert m.state == _State.A

    def test_transition_updates_state(self) -> None:
        m = _Manager(_FakeWindow())
        m.transition(_State.B)
        assert m.state == _State.B

    def test_transition_merges_context(self) -> None:
        m = _Manager(_FakeWindow())
        m.transition(_State.B, score=10)
        m.transition(_State.C, player=1)
        assert m.context == {"score": 10, "player": 1}

    def test_transition_calls_enter_state(self) -> None:
        m = _Manager(_FakeWindow())
        m.transition(_State.B)
        m.transition(_State.C)
        assert m.visited == [_State.B, _State.C]

    def test_abstract_enter_state_raises(self) -> None:
        base = BaseGameStateManager(_FakeWindow(), _State.A)
        with pytest.raises(NotImplementedError):
            base._enter_state(_State.B)
