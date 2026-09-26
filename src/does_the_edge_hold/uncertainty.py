"""Paired uncertainty estimates for daily strategy and baseline P&L."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd


def paired_block_bootstrap(strategy: pd.Series, baseline: pd.Series,
                           start: str, end: str, capital: float,
                           *, block_days: int = 5, replicates: int = 2_000,
                           seed: int = 1_729, periods_per_year: int = 365) -> dict:
    """Resample paired calendar days in circular blocks; report a descriptive CI."""
    if capital <= 0 or block_days < 1 or replicates < 1:
        raise ValueError("capital, block_days and replicates must be positive")
    lower, upper = pd.to_datetime(start, utc=True), pd.to_datetime(end, utc=True)
    left = strategy.loc[(strategy.index >= lower) & (strategy.index < upper)]
    right = baseline.loc[(baseline.index >= lower) & (baseline.index < upper)]
    if not left.index.equals(right.index):
        raise ValueError("strategy and baseline must cover the same days")
    difference = (left - right).to_numpy(dtype=float)
    if not np.isfinite(difference).all():
        raise ValueError("daily P&L must be finite")
    n = len(difference)
    if n < block_days:
        return {"status": "too_few_days", "days": n, "block_days": block_days}
    rng = np.random.default_rng(seed)
    draws = np.empty(replicates, dtype=float)
    block_count = math.ceil(n / block_days)
    offsets = np.arange(block_days)
    for index in range(replicates):
        starts = rng.integers(0, n, size=block_count)
        sampled = (starts[:, None] + offsets[None, :]) % n
        draws[index] = difference[sampled.ravel()[:n]].mean() * periods_per_year / capital
    observed = float(difference.mean() * periods_per_year / capital)
    return {"status": "ok", "days": n, "block_days": block_days,
            "replicates": replicates, "seed": seed,
            "observed_annual_return_difference": observed,
            "ci95_annual_return_difference": [float(v) for v in np.quantile(draws, [0.025, 0.975])],
            "bootstrap_fraction_nonpositive": float(np.mean(draws <= 0)),
            "periods_per_year": periods_per_year,
            "note": "paired circular block bootstrap of declared daily observations; descriptive, not a correction for selection or proof of future returns"}
