import numpy as np
import pandas as pd
import pytest

from does_the_edge_hold.uncertainty import paired_block_bootstrap


def test_paired_bootstrap_is_repeatable_and_uses_daily_differences() -> None:
    days = pd.date_range("2024-01-01", periods=30, freq="D", tz="UTC")
    baseline = pd.Series(np.arange(30, dtype=float), index=days)
    strategy = baseline + 10
    a = paired_block_bootstrap(strategy, baseline, "2024-01-01", "2024-02-01", 100_000, periods_per_year=252)
    b = paired_block_bootstrap(strategy, baseline, "2024-01-01", "2024-02-01", 100_000, periods_per_year=252)
    assert a == b
    assert a["observed_annual_return_difference"] == pytest.approx(0.0252)
    assert a["ci95_annual_return_difference"] == pytest.approx([0.0252, 0.0252])
    assert a["bootstrap_fraction_nonpositive"] == 0


def test_paired_bootstrap_rejects_misaligned_days() -> None:
    days = pd.date_range("2024-01-01", periods=10, freq="D", tz="UTC")
    with pytest.raises(ValueError, match="same days"):
        paired_block_bootstrap(pd.Series(1, index=days), pd.Series(0, index=days[1:]),
                               "2024-01-01", "2024-02-01", 100_000)
