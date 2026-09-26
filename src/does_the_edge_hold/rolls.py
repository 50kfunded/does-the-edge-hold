"""Explicit date-to-contract schedules and the roll gate."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


class RollGateError(ValueError):
    """Raised when real bars have no verified contract mapping."""


def read_schedule(path: str | Path) -> pd.DataFrame:
    """Read a CSV with `effective_at,contract`, sorted in UTC."""
    schedule = pd.read_csv(path)
    if list(schedule.columns) != ["effective_at", "contract"]:
        raise RollGateError("roll CSV needs exactly effective_at,contract")
    schedule["effective_at"] = pd.to_datetime(schedule["effective_at"], utc=True,
                                                errors="raise")
    if schedule.empty or schedule["contract"].isna().any():
        raise RollGateError("roll schedule is empty or has unknown contracts")
    if not schedule["effective_at"].is_monotonic_increasing or schedule["effective_at"].duplicated().any():
        raise RollGateError("roll dates must be strictly increasing")
    if schedule["contract"].astype(str).str.strip().eq("").any():
        raise RollGateError("roll schedule has blank contracts")
    return schedule


def attach_contracts(bars: pd.DataFrame, schedule: pd.DataFrame) -> pd.DataFrame:
    """Assign every start-stamped bar to the supplied contract schedule."""
    if "ts" not in bars or "effective_at" not in schedule or "contract" not in schedule:
        raise RollGateError("bars need ts and the schedule needs effective_at,contract")
    ts = pd.to_datetime(bars["ts"], utc=True)
    starts = pd.to_datetime(schedule["effective_at"], utc=True)
    if not ts.is_monotonic_increasing or ts.duplicated().any():
        raise RollGateError("bar timestamps must be strictly increasing")
    if not starts.is_monotonic_increasing or starts.duplicated().any():
        raise RollGateError("roll dates must be strictly increasing")
    pos = np.searchsorted(starts.to_numpy(), ts.to_numpy(), side="right") - 1
    if (pos < 0).any():
        raise RollGateError("schedule does not cover the first bar")
    out = bars.copy()
    out["contract"] = schedule["contract"].to_numpy()[pos]
    if out["contract"].isna().any():
        raise RollGateError("schedule has unknown contract")
    return out
