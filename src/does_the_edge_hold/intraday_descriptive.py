"""Unscored price-variation diagnostics, including excluded volume sources."""
import numpy as np
import pandas as pd
from .data import iter_parquet, source_path

def describe_sources(data_root, plan):
    out = {}
    for market in plan["audit_markets"]:
        parts = []
        for batch in iter_parquet(source_path(data_root, market)):
            ts = batch.ts
            keep = (ts.dt.dayofweek < 5) & (ts.dt.hour >= 8) & (ts.dt.hour < 12)
            keep &= (ts >= pd.Timestamp(plan["splits_utc"]["development"][0], tz="UTC")) & (ts < pd.Timestamp(plan["splits_utc"]["historical_final"][1], tz="UTC"))
            if keep.any(): parts.append(batch.loc[keep, ["ts", "close"]])
        if not parts:
            out[market] = {"status": "no_observations"}; continue
        frame = pd.concat(parts, ignore_index=True)
        same_minute = frame.ts.diff().eq(pd.Timedelta(minutes=1)) & frame.ts.dt.floor("D").eq(frame.ts.shift().dt.floor("D"))
        frame["adjacent_observed_price_change_points"] = frame.close.diff().where(same_minute)
        parts_summary = {}
        for name, (start, end) in plan["splits_utc"].items():
            part = frame.loc[(frame.ts >= pd.Timestamp(start, tz="UTC")) & (frame.ts < pd.Timestamp(end, tz="UTC"))]
            diff = part.adjacent_observed_price_change_points.dropna()
            parts_summary[name] = {"observed_window_minutes": len(part), "adjacent_same_date_pairs": len(diff),
                                  "price_change_std_points": float(diff.std(ddof=1)) if len(diff) > 1 else None,
                                  "absolute_price_change_median_points": float(diff.abs().median()) if len(diff) else None,
                                  "absolute_price_change_95pct_points": float(diff.abs().quantile(.95)) if len(diff) else None,
                                  "observed_dates": int(part.ts.dt.floor("D").nunique())}
        out[market] = {"status": "descriptive_only", "parts": parts_summary,
                       "note": "observed source price variation in points; excludes cross-date and missing-minute changes; not instrument returns, tradable P&L or annualized investment volatility"}
    return out
