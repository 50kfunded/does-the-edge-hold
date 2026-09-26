"""P&L attributed from execution events and interval-close marks."""
from __future__ import annotations
import math
import numpy as np
import pandas as pd
from .daily_clock import DailyClock
from .timing import BacktestResult

def curve_with_changes(curve):
    out = curve.copy()
    out["step_net"] = out.net_pnl.diff().fillna(out.net_pnl)
    out["step_gross"] = out.gross_pnl.diff().fillna(out.gross_pnl)
    return out

def _events(result):
    if result.events is None:
        raise ValueError("event-level attribution is required; rerun legacy results")
    return result.events.copy()

def _mask(labels, start, end):
    return ((labels >= pd.to_datetime(start, utc=True)) if start is not None else np.ones(len(labels), bool)) & (
           (labels < pd.to_datetime(end, utc=True)) if end is not None else np.ones(len(labels), bool))

def daily_pnl(result, clock=None, start=None, end=None):
    clock = clock or DailyClock()
    events = _events(result)
    labels = clock.labels(events.attribution_at)
    mask = _mask(labels, start, end)
    return events.loc[mask].groupby(labels[mask])["step_net"].sum()

def summarize(result: BacktestResult, start=None, end=None, *, clock=None):
    clock = clock or DailyClock()
    events = _events(result)
    labels = clock.labels(events.attribution_at)
    events = events.loc[_mask(labels, start, end)]
    daily = daily_pnl(result, clock, start, end)
    capital = result.ledger.starting_capital
    curve = result.curve
    curve = curve.loc[_mask(clock.labels(curve.ts - pd.Timedelta(nanoseconds=1)), start, end)]
    fill_labels = clock.labels([f.ts for f in result.ledger.fills])
    fills = [f for f, keep in zip(result.ledger.fills, _mask(fill_labels, start, end)) if keep]
    gross, net = float(events.step_gross.sum()), float(events.step_net.sum())
    returns = daily / capital
    std = float(returns.std(ddof=1)) if len(daily) > 1 else 0
    path = capital + np.r_[0, daily.cumsum().to_numpy()]
    peaks = np.maximum.accumulate(path)
    return {"status": "ok" if len(daily) else "no_bars", "gross_pnl_usd": gross,
        "net_pnl_usd": net, "account_return": net / capital,
        "annual_mean_return": float(returns.mean() * clock.periods_per_year) if len(daily) else None,
        "mean_session_pnl_usd": float(daily.mean()) if len(daily) else None,
        "volatility": std * math.sqrt(clock.periods_per_year) if len(daily) > 1 else None,
        "sharpe": float(returns.mean() / std * math.sqrt(clock.periods_per_year)) if std > 0 else None,
        "max_drawdown": float(((path - peaks) / peaks).min()),
        "exposure": float(curve.position.mean()) if len(curve) else None,
        "exposure_note": "fraction of observed sampled marks; not wall-clock exposure",
        "fills": len(fills), "turnover_contracts": len(fills),
        "commission_usd": sum(f.commission for f in fills),
        "slippage_usd": sum(f.slippage for f in fills),
        "entry_trades": sum(f.side == "buy" for f in fills),
        "days": len(daily), "hours": len(curve), "clock": clock.name,
        "periods_per_year": clock.periods_per_year,
        "reconciliation_error_usd": net - (gross - sum(f.commission + f.slippage for f in fills))}

