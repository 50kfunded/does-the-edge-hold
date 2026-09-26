"""A shared attribution clock for metrics and selection."""
from dataclasses import dataclass
import pandas as pd

@dataclass(frozen=True)
class DailyClock:
    name: str = "utc_calendar"
    periods_per_year: int = 365

    def __post_init__(self):
        if self.name not in ("utc_calendar", "new_york_futures_session") or self.periods_per_year <= 0:
            raise ValueError("unknown daily clock or annualization")

    def labels(self, stamps) -> pd.DatetimeIndex:
        stamps = pd.DatetimeIndex(pd.to_datetime(stamps, utc=True))
        if self.name == "utc_calendar":
            return stamps.floor("D")
        # local calendar arithmetic keeps the 18:00 boundary stable across DST.
        local = stamps.tz_convert("America/New_York").tz_localize(None)
        dates = local.normalize() + pd.to_timedelta((local.hour >= 18).astype(int), unit="D")
        return dates.tz_localize("UTC")

    @classmethod
    def from_plan(cls, plan):
        value = plan.get("statistics", {}).get("clock", {"name": "utc_calendar", "periods_per_year": 365})
        return cls(**value)

