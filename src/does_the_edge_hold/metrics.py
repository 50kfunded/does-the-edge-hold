"""Account-capital metrics, with zero and negative futures prices allowed."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from .timing import BacktestResult


def curve_with_changes(curve: pd.DataFrame) -> pd.DataFrame:
    out = curve.copy()
    out["step_net"] = out["net_pnl"].diff().fillna(out["net_pnl"])
    out["step_gross"] = out["gross_pnl"].diff().fillna(out["gross_pnl"])
    return out


def summarize(result: BacktestResult, start: str | None = None,
              end: str | None = None) -> dict:
    curve = curve_with_changes(result.curve)
    valuation_at = curve["ts"] - pd.Timedelta(nanoseconds=1)
    if start is not None:
        curve = curve.loc[valuation_at >= pd.to_datetime(start, utc=True)]
    if end is not None:
        curve = curve.loc[valuation_at.loc[curve.index] < pd.to_datetime(end, utc=True)]
    capital = result.ledger.starting_capital
    if curve.empty:
        return {"status": "no_bars", "gross_pnl_usd": 0.0, "net_pnl_usd": 0.0,
                "account_return": 0.0, "volatility": None, "sharpe": None,
                "max_drawdown": None, "exposure": None, "fills": 0,
                "turnover_contracts": 0, "commission_usd": 0.0,
                "slippage_usd": 0.0, "entry_trades": 0, "days": 0, "hours": 0}
    daily = curve.groupby((curve["ts"] - pd.Timedelta(nanoseconds=1)).dt.floor("D"))["step_net"].sum() / capital
    volatility = float(daily.std(ddof=1) * math.sqrt(252)) if len(daily) > 1 else None
    sharpe = (float(daily.mean() / daily.std(ddof=1) * math.sqrt(252))
              if len(daily) > 1 and daily.std(ddof=1) > 0 else None)
    path = capital + np.r_[0.0, np.cumsum(daily.to_numpy() * capital)]
    peaks = np.maximum.accumulate(path)
    drawdown = (path - peaks) / peaks
    start_ts = pd.to_datetime(start, utc=True) if start is not None else pd.Timestamp("1900-01-01", tz="UTC")
    end_ts = pd.to_datetime(end, utc=True) if end is not None else curve["ts"].iloc[-1]
    fills = [fill for fill in result.ledger.fills if start_ts <= pd.Timestamp(fill.ts) < end_ts]
    gross = float(curve["step_gross"].sum())
    net = float(curve["step_net"].sum())
    return {"status": "ok", "gross_pnl_usd": gross, "net_pnl_usd": net,
            "account_return": net / capital,
            "volatility": volatility, "sharpe": sharpe,
            "max_drawdown": float(drawdown.min()),
            "exposure": float(curve["position"].mean()),
            "fills": len(fills), "turnover_contracts": len(fills),
            "commission_usd": sum(fill.commission for fill in fills),
            "slippage_usd": sum(fill.slippage for fill in fills),
            "entry_trades": sum(fill.side == "buy" for fill in fills),
            "days": len(daily), "hours": len(curve)}


def daily_pnl(result: BacktestResult) -> pd.Series:
    curve = curve_with_changes(result.curve)
    return curve.groupby((curve["ts"] - pd.Timedelta(nanoseconds=1)).dt.floor("D"))["step_net"].sum()
