"""Long-or-flat signals built only from completed bars."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

import numpy as np
import pandas as pd

REGISTRY = {}

def register_signal(name, callback):
    if name in ("momentum", "mean_reversion") or name in REGISTRY:
        raise ValueError("signal name is already registered")
    REGISTRY[name] = callback


@dataclass(frozen=True)
class SignalSpec:
    family: str
    lookback_hours: int
    entry_z: float | None = None

    @property
    def id(self) -> str:
        if self.family == "momentum":
            return f"mom-{self.lookback_hours}"
        if self.family == "mean_reversion":
            return f"revert-{self.lookback_hours}-{self.entry_z:g}"
        return f"{self.family}-{self.lookback_hours}"

    @property
    def config_hash(self) -> str:
        payload = json.dumps(self.__dict__, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode()).hexdigest()


def grid_from_plan(plan: dict) -> list[SignalSpec]:
    count = plan["configuration_count"]
    if isinstance(count, bool) or not isinstance(count, int) or count < 1:
        raise ValueError("configuration count must be a positive integer")
    families = plan["signal_families"]
    grid = []
    for family, params in families.items():
        if "lookback_hours" in params and "lookback_bars" in params:
            raise ValueError("declare one lookback unit")
        if family == "mean_reversion" and params.get("exit_z", 0) != 0:
            raise ValueError("this mean-reversion implementation exits at zero")
        if family not in ("momentum", "mean_reversion") and family not in REGISTRY:
            raise ValueError(f"unregistered family: {family}")
        lengths = params.get("lookback_bars", params.get("lookback_hours", []))
        if not lengths or any(isinstance(n, bool) or not isinstance(n, int) or n <= 0 for n in lengths):
            raise ValueError("lookbacks must be positive finite integers")
        entries = params.get("entry_z", []) if family == "mean_reversion" else [None]
        if not entries or any(z is not None and (not np.isfinite(z) or z <= 0) for z in entries):
            raise ValueError("entry thresholds must be positive and finite")
        grid.extend(SignalSpec(family, n, z) for n in lengths for z in entries)
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
    if spec.family in REGISTRY:
        out = REGISTRY[spec.family](hourly.copy(), spec)
        if not out.known_at.equals(hourly.known_at) or not out.target.isin([0, 1]).all():
            raise ValueError("extension must return aligned long/flat decisions")
        return out
    target = np.zeros(len(hourly), dtype=np.int8)
    segments = hourly["contract"].ne(hourly["contract"].shift()).cumsum()
    for _, group in hourly.groupby(segments, sort=False, observed=True):
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
