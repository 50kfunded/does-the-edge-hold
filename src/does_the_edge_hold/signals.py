"""Long-or-flat signals built only from completed bars."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class SignalSpec:
    family: str
    lookback_hours: int
    entry_z: float | None = None

    @property
    def id(self) -> str:
        if self.family == "momentum":
            return f"mom-{self.lookback_hours}"
        return f"revert-{self.lookback_hours}-{self.entry_z:g}"

    @property
    def config_hash(self) -> str:
        payload = json.dumps(self.__dict__, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode()).hexdigest()


def grid_from_plan(plan: dict) -> list[SignalSpec]:
    families = plan["signal_families"]
    grid = [SignalSpec("momentum", int(length))
            for length in families["momentum"]["lookback_hours"]]
    grid += [SignalSpec("mean_reversion", int(length), float(entry))
             for length in families["mean_reversion"]["lookback_hours"]
             for entry in families["mean_reversion"]["entry_z"]]
    if len(grid) != plan["configuration_count"] or len({item.id for item in grid}) != len(grid):
        raise ValueError("grid does not match the frozen research plan")
    return grid


def decisions(hourly: pd.DataFrame, spec: SignalSpec) -> pd.DataFrame:
    """A decision at `known_at` may use that bar's close, never later bars."""
    required = {"known_at", "close", "contract"}
    if not required.issubset(hourly):
        raise ValueError(f"signal bars need {sorted(required)}")
    if not hourly["known_at"].is_monotonic_increasing:
        raise ValueError("signal bars must be time ordered")
    target = np.zeros(len(hourly), dtype=np.int8)
    for _, group in hourly.groupby("contract", sort=False, observed=True):
        indices = group.index.to_numpy()
        close = group["close"].astype(float).reset_index(drop=True)
        if spec.family == "momentum":
            past = close.shift(spec.lookback_hours)
            target[indices] = (close > past).fillna(False).to_numpy(dtype=np.int8)
        elif spec.family == "mean_reversion":
            if spec.entry_z is None or spec.entry_z <= 0:
                raise ValueError("mean reversion needs positive entry_z")
            prior = close.shift(1)
            mean = prior.rolling(spec.lookback_hours, min_periods=spec.lookback_hours).mean()
            stdev = prior.rolling(spec.lookback_hours, min_periods=spec.lookback_hours).std()
            z = (close - mean) / stdev.replace(0, np.nan)
            holding = 0
            for local, value in enumerate(z.to_numpy()):
                if not np.isfinite(value):
                    holding = 0
                elif holding and value >= 0:
                    holding = 0
                elif not holding and value <= -spec.entry_z:
                    holding = 1
                target[indices[local]] = holding
        else:
            raise ValueError(f"unknown signal family {spec.family}")
    return pd.DataFrame({"known_at": pd.to_datetime(hourly["known_at"], utc=True),
                         "target": target})
