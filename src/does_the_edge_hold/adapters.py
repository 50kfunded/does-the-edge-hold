"""Canonical bars and execution metadata for independent inputs."""
from dataclasses import dataclass
import numpy as np
import pandas as pd
from .ledger import ContractSpec, Ledger
from .timing import hourly_from_minutes

@dataclass(frozen=True)
class MarketAdapter:
    spec: ContractSpec
    kind: str = "futures"
    bar_minutes: int = 1
    ledger_factory: object = Ledger

    def signal_bars(self, bars):
        self.validate(bars)
        if self.bar_minutes == 1:
            return hourly_from_minutes(bars)
        out = bars.reset_index(drop=True).copy()
        out["bar_start"] = out.ts
        out["known_at"] = out.ts + pd.Timedelta(minutes=self.bar_minutes)
        return out

    def validate(self, bars):
        required = ["ts", "open", "high", "low", "close", "volume", "contract"]
        if not set(required).issubset(bars) or bars.empty:
            raise ValueError("canonical OHLCV bars and explicit instrument identity are required")
        ts = pd.DatetimeIndex(pd.to_datetime(bars.ts, utc=True))
        values = bars[["open", "high", "low", "close", "volume"]].to_numpy(dtype=float)
        if ts.hasnans or not ts.is_monotonic_increasing or ts.duplicated().any() or not np.isfinite(values).all():
            raise ValueError("input has invalid timestamps, order, duplicates or values")
        if (bars.high < bars[["open", "close", "low"]].max(axis=1)).any() or (bars.low > bars[["open", "close", "high"]].min(axis=1)).any() or (bars.volume <= 0).any():
            raise ValueError("invalid OHLC or volume")
        if self.kind == "spot" and (bars[["open", "high", "low", "close"]] <= 0).any().any():
            raise ValueError("spot prices must be positive")
