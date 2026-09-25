"""Bar timing and simulated order scheduling."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .ledger import ContractSpec, Costs, Ledger


def hourly_from_minutes(minutes: pd.DataFrame) -> pd.DataFrame:
    """Group start-stamped minutes; a close is known only at the hour end."""
    needed = {"ts", "open", "high", "low", "close", "volume", "contract"}
    if not needed.issubset(minutes.columns):
        raise ValueError(f"missing columns: {sorted(needed - set(minutes.columns))}")
    if minutes.empty:
        raise ValueError("no minute bars")
    frame = minutes.copy()
    frame["ts"] = pd.to_datetime(frame["ts"], utc=True)
    if not frame["ts"].is_monotonic_increasing or frame["ts"].duplicated().any():
        raise ValueError("minute timestamps must be strictly increasing")
    frame["bar_start"] = frame["ts"].dt.floor("h")
    grouped = frame.groupby(["bar_start", "contract"], sort=True, observed=True)
    hourly = grouped.agg(open=("open", "first"), high=("high", "max"),
                         low=("low", "min"), close=("close", "last"),
                         volume=("volume", "sum"), minute_count=("ts", "size"),
                         last_minute=("ts", "last")).reset_index()
    hourly["known_at"] = hourly["bar_start"] + pd.Timedelta(hours=1)
    # A roll in the middle of an hour makes both fragments unsuitable as
    # ordinary signal bars. The execution ledger still sees the minute bars.
    mixed = hourly["bar_start"].duplicated(keep=False)
    return hourly.loc[~mixed].reset_index(drop=True)


@dataclass
class BacktestResult:
    ledger: Ledger
    curve: pd.DataFrame


def simulate(minutes: pd.DataFrame, decisions: pd.DataFrame, spec: ContractSpec,
             costs: Costs, *, delay_minutes: int = 0,
             starting_capital: float = 100_000) -> BacktestResult:
    """Execute targets at the first observed minute open after they are known.

    Every contract change must be supplied in `contract` before the run. A long
    position exits at the *open* of the final old-contract minute and, if the
    current target remains long, re-enters at the first new-contract open.
    Both are scheduled from the supplied mapping, never inferred from a jump.
    """
    if delay_minutes < 0:
        raise ValueError("delay cannot be negative")
    for col in ("ts", "open", "close", "contract"):
        if col not in minutes:
            raise ValueError(f"minute bars need {col}")
    for col in ("known_at", "target"):
        if col not in decisions:
            raise ValueError(f"decisions need {col}")
    if minutes.empty:
        raise ValueError("no minute bars")
    frame = minutes.reset_index(drop=True).copy()
    frame["ts"] = pd.to_datetime(frame["ts"], utc=True)
    ts = frame["ts"]
    if not ts.is_monotonic_increasing or ts.duplicated().any():
        raise ValueError("minute timestamps must be strictly increasing")
    if frame["contract"].isna().any():
        raise ValueError("unknown contracts: empirical P&L is gated")
    contracts = frame["contract"].to_numpy()
    opens = frame["open"].to_numpy(dtype=float)
    closes = frame["close"].to_numpy(dtype=float)
    if not np.isfinite(opens).all() or not np.isfinite(closes).all():
        raise ValueError("prices must be finite")

    decision = decisions.sort_values("known_at").reset_index(drop=True).copy()
    decision["known_at"] = pd.to_datetime(decision["known_at"], utc=True)
    if not decision["target"].isin([0, 1]).all():
        raise ValueError("target must be zero or one")
    ready = decision["known_at"] + pd.Timedelta(minutes=delay_minutes)
    if len(ready) and ready.duplicated().any():
        raise ValueError("decision times must be distinct")
    trade_at = np.searchsorted(ts.to_numpy(), ready.to_numpy(), side="left")
    valid = trade_at < len(frame)
    trade_indices = trade_at[valid]
    trade_targets = decision.loc[valid, "target"].to_numpy(dtype=int)
    latest_target = {}
    for index, target in zip(trade_indices, trade_targets):
        latest_target[int(index)] = int(target)

    transitions = np.flatnonzero(contracts[1:] != contracts[:-1]) + 1
    roll_exit_indices = set((transitions - 1).tolist())
    roll_entry_indices = set(transitions.tolist())
    # Sample one close per observed hour, plus each trade/roll minute.
    hour = ts.dt.floor("h").to_numpy()
    hour_ends = np.r_[np.flatnonzero(hour[1:] != hour[:-1]), len(frame) - 1]
    hour_end_set = set(hour_ends.tolist())
    events = sorted(set(hour_ends.tolist()) | set(latest_target) |
                    roll_exit_indices | roll_entry_indices)
    ledger = Ledger(spec, costs, starting_capital)
    target = 0
    records = []
    for i in events:
        if i in latest_target:
            target = latest_target[i]
        stamp = ts.iloc[i].to_pydatetime()
        contract = str(contracts[i])
        if i in roll_entry_indices and ledger.position:
            raise ValueError("position crossed a roll without an exit")
        if i in roll_exit_indices:
            if ledger.position:
                ledger.sell(stamp, contract, float(opens[i]), "scheduled roll exit")
        elif target and not ledger.position:
            ledger.buy(stamp, contract, float(opens[i]),
                       "scheduled roll entry" if i in roll_entry_indices else "signal")
        elif not target and ledger.position:
            ledger.sell(stamp, contract, float(opens[i]))
        if ledger.position:
            ledger.mark(contract, float(closes[i]))
        if i in hour_end_set:
            records.append({"ts": ts.iloc[i].floor("h") + pd.Timedelta(hours=1),
                            "equity": ledger.equity, "gross_pnl": ledger.gross_pnl,
                            "net_pnl": ledger.net_pnl, "position": ledger.position,
                            "contract": contract})
    return BacktestResult(ledger, pd.DataFrame.from_records(records))
