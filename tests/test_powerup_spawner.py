"""Unit tests for PowerUpSpawner — no display required."""

from __future__ import annotations

import pytest

from agf.powerups.config import PowerUpConfigBase
from agf.powerups.spawner import PowerUpSpawner


class _FixedWeightSpawner(PowerUpSpawner):
    """Spawner with a fixed non-empty weight table for testing."""

    def _build_weight_table(self) -> dict[str, float]:
        return {"shield": 1.0}


def _config(**overrides) -> PowerUpConfigBase:
    defaults = {
        "spawn_interval_base": 20.0,
        "spawn_interval_min": 6.0,
        "spawn_interval_jitter": 0.0,  # deterministic for tests
        "spawn_interval_decay": 0.85,
    }
    defaults.update(overrides)
    return PowerUpConfigBase(**defaults)


class TestSetup:
    def test_resets_timer(self) -> None:
        cfg = _config()
        spawner = _FixedWeightSpawner(cfg)
        spawner.timer = 50.0
        spawner.setup(level_number=3, level_type="standard")
        assert spawner.timer == pytest.approx(0.0)

    def test_stores_level(self) -> None:
        spawner = _FixedWeightSpawner(_config())
        spawner.setup(level_number=5, level_type="boss")
        assert spawner._level_number == 5
        assert spawner._level_type == "boss"


class TestUpdate:
    def test_returns_none_before_interval(self) -> None:
        spawner = _FixedWeightSpawner(_config())
        spawner.setup(level_number=2, level_type="standard")
        assert spawner.update(1.0) is None

    def test_returns_type_when_interval_elapses(self) -> None:
        spawner = _FixedWeightSpawner(_config())
        spawner.setup(level_number=2, level_type="standard")
        # spawn_interval_base=20, jitter=0 → interval=20
        result = spawner.update(25.0)
        assert result == "shield"

    def test_timer_resets_after_spawn(self) -> None:
        spawner = _FixedWeightSpawner(_config())
        spawner.setup(level_number=2, level_type="standard")
        spawner.update(25.0)
        assert spawner.timer == pytest.approx(0.0)

    def test_returns_none_when_weight_table_empty(self) -> None:
        """Base PowerUpSpawner has no weights — should never spawn."""
        spawner = PowerUpSpawner(_config())
        spawner.setup(level_number=5, level_type="standard")
        result = spawner.update(100.0)
        assert result is None


class TestComputeInterval:
    def test_level_2_equals_base(self) -> None:
        cfg = _config()
        spawner = _FixedWeightSpawner(cfg)
        spawner.setup(level_number=2, level_type="standard")
        # decay^0 = 1 → interval = min + (base - min) * 1 = base
        assert spawner.current_interval == pytest.approx(20.0)

    def test_decreases_with_level(self) -> None:
        cfg = _config()
        s2 = _FixedWeightSpawner(cfg)
        s2.setup(level_number=2, level_type="standard")
        s5 = _FixedWeightSpawner(cfg)
        s5.setup(level_number=5, level_type="standard")
        assert s5.current_interval < s2.current_interval

    def test_decay_formula(self) -> None:
        cfg = _config()  # base=20, min=6, decay=0.85, jitter=0
        spawner = _FixedWeightSpawner(cfg)
        spawner.setup(level_number=5, level_type="standard")
        # level_offset = 3 → 6 + 14 * 0.85^3 = 6 + 14 * 0.614125 = 14.5978
        expected = 6.0 + 14.0 * (0.85**3)
        assert spawner.current_interval == pytest.approx(expected)

    def test_floors_at_minimum(self) -> None:
        cfg = _config()
        spawner = _FixedWeightSpawner(cfg)
        spawner.setup(level_number=1000, level_type="standard")
        # At very high level decay^offset ≈ 0, so interval ≈ minimum
        assert spawner.current_interval >= cfg.spawn_interval_min
        assert spawner.current_interval == pytest.approx(cfg.spawn_interval_min, abs=0.01)

    def test_level_1_and_2_both_equal_base(self) -> None:
        """level_offset is clamped to 0 so levels 1 and 2 match."""
        cfg = _config()
        s1 = _FixedWeightSpawner(cfg)
        s1.setup(level_number=1, level_type="standard")
        s2 = _FixedWeightSpawner(cfg)
        s2.setup(level_number=2, level_type="standard")
        assert s1.current_interval == pytest.approx(s2.current_interval)
