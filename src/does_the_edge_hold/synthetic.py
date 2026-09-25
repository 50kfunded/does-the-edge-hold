"""Small, deterministic bars for the public example and accounting tests."""

from __future__ import annotations

import numpy as np
import pandas as pd


def make_bars(seed: int = 7, minutes: int = 3_600) -> pd.DataFrame:
    """Make two synthetic contracts with a visible, non-tradable roll gap."""
    if minutes < 240:
        raise ValueError("at least 240 minutes are needed")
    rng = np.random.default_rng(seed)
    ts = pd.date_range("2024-01-08 00:00", periods=minutes, freq="min", tz="UTC")
    roll_at = minutes // 2
    change = rng.normal(0, 0.35, minutes)
    change[: roll_at // 2] += 0.035
    change[roll_at // 2 : roll_at] -= 0.025
    change[roll_at:] += 0.01
    close = 10_000 + np.cumsum(change)
    close[roll_at:] += 120  # This is a different contract, not a trading gain.
    opened = np.r_[close[0], close[:-1]]
    opened[roll_at] = close[roll_at] - change[roll_at]
    spread = rng.uniform(0.02, 0.25, minutes)
    bars = pd.DataFrame(
        {
            "ts": ts,
            "open": opened,
            "high": np.maximum(opened, close) + spread,
            "low": np.minimum(opened, close) - spread,
            "close": close,
            "volume": rng.integers(1, 100, minutes),
            "contract": np.where(np.arange(minutes) < roll_at, "SYN-A", "SYN-B"),
        }
    )
    return bars
