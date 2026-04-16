"""Unit tests for BaseGameConfig, apply_argv_overrides, and config_path."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from agf.config.base_config import BaseGameConfig, apply_argv_overrides, config_path


@dataclass
class _SubConfig:
    ship_speed: float = 100.0
    fire_cooldown: float = 0.3


@dataclass
class _Game(BaseGameConfig):
    sub: _SubConfig = field(default_factory=_SubConfig)


class TestApplyArgvOverrides:
    def test_override_top_level_int(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(sys, "argv", ["prog", "-num_lives", "5"])
        cfg = _Game()
        apply_argv_overrides(cfg)
        assert cfg.num_lives == 5

    def test_override_top_level_bool_no_value(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(sys, "argv", ["prog", "-debug"])
        cfg = _Game()
        apply_argv_overrides(cfg)
        assert cfg.debug is True

    def test_override_top_level_bool_explicit_false(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(sys, "argv", ["prog", "-debug", "false"])
        cfg = _Game(debug=True)
        apply_argv_overrides(cfg)
        assert cfg.debug is False

    def test_override_sub_dataclass_float(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(sys, "argv", ["prog", "-ship_speed", "250"])
        cfg = _Game()
        apply_argv_overrides(cfg)
        assert cfg.sub.ship_speed == pytest.approx(250.0)

    def test_unknown_argument_ignored(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setattr(sys, "argv", ["prog", "-totally_bogus", "42"])
        cfg = _Game()
        apply_argv_overrides(cfg)
        out = capsys.readouterr().out
        assert "Unknown argument" in out

    def test_negative_numeric_value_accepted(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(sys, "argv", ["prog", "-starting_level", "-1"])
        cfg = _Game()
        apply_argv_overrides(cfg)
        assert cfg.starting_level == -1

    def test_no_argv_leaves_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(sys, "argv", ["prog"])
        cfg = _Game()
        apply_argv_overrides(cfg)
        assert cfg.num_lives == 3
        assert cfg.sub.ship_speed == pytest.approx(100.0)


class TestConfigPath:
    def test_dev_mode_uses_project_root(self, tmp_path: Path) -> None:
        p = config_path(tmp_path)
        assert p == tmp_path / "game_config.toml"

    def test_custom_filename(self, tmp_path: Path) -> None:
        p = config_path(tmp_path, "custom.toml")
        assert p == tmp_path / "custom.toml"

    def test_frozen_uses_executable_dir(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(sys, "executable", "/fake/exe/game.exe")
        p = config_path(Path("/unused"))
        assert p == Path("/fake/exe") / "game_config.toml"
