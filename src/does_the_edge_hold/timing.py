"""Bar timing and simulated order scheduling."""

from __future__ import annotations

from dataclasses import dataclass, replace

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
    events: pd.DataFrame | None = None


def scheduled_instructions(schedule: pd.DataFrame, *, lead_minutes: int = 120) -> pd.DataFrame:
    """Only for schedules whose advance availability is independently established."""
    rows = []
    for i in range(1, len(schedule)):
        boundary = pd.to_datetime(schedule.effective_at.iloc[i], utc=True)
        rows.append({"known_at": boundary - pd.Timedelta(minutes=lead_minutes),
                     "executable_at": boundary - pd.Timedelta(minutes=lead_minutes),
                     "deadline": boundary, "effective_at": boundary,
                     "old_contract": str(schedule.contract.iloc[i - 1]),
                     "new_contract": str(schedule.contract.iloc[i])})
    return pd.DataFrame(rows, columns=["known_at", "executable_at", "deadline", "effective_at", "old_contract", "new_contract"])


def simulate(minutes: pd.DataFrame, decisions: pd.DataFrame, spec: ContractSpec,
             costs: Costs, *, delay_minutes: int = 0,
             starting_capital: float = 100_000,
             roll_instructions: pd.DataFrame | None = None,
             bar_minutes: int = 1, ledger_factory=None) -> BacktestResult:
    """Execute targets at the first observed minute open after they are known.

    Roll instructions must be known before their executable time. No price is
    selected by looking backwards from a future boundary or observation.
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
    target_known = {}
    for index, target, known in zip(trade_indices, trade_targets, decision.loc[valid, "known_at"]):
        latest_target[int(index)] = int(target)
        target_known[int(index)] = known

    transitions = np.flatnonzero(contracts[1:] != contracts[:-1]) + 1
    roll_exit_indices = set()
    roll_entry_indices = set()
    suspended = []
    instructions = roll_instructions if roll_instructions is not None else pd.DataFrame()
    covered = set()
    roll_known = {}
    for instruction in instructions.to_dict("records"):
        known, executable, deadline, boundary = [pd.to_datetime(instruction[k], utc=True) for k in
                                                   ("known_at", "executable_at", "deadline", "effective_at")]
        if pd.isna(known) or not known <= executable < deadline <= boundary:
            raise ValueError("roll instruction must be known before execution and deadline")
        old, new = str(instruction["old_contract"]), str(instruction["new_contract"])
        eligible = np.flatnonzero((ts >= executable + pd.Timedelta(minutes=delay_minutes)) &
                                   (ts < deadline) & (contracts.astype(str) == old))
        entries = np.flatnonzero((ts >= boundary + pd.Timedelta(minutes=delay_minutes)) &
                                (contracts.astype(str) == new))
        if not len(eligible) and ts.iloc[0] < boundary <= ts.iloc[-1]:
            raise ValueError("no permitted old-contract open before roll deadline")
        if len(eligible):
            roll_exit_indices.add(int(eligible[0]))
            roll_known[int(eligible[0])] = known
        if len(entries):
            roll_entry_indices.add(int(entries[0]))
            roll_known[int(entries[0])] = known
        suspended.append((executable + pd.Timedelta(minutes=delay_minutes),
                          boundary + pd.Timedelta(minutes=delay_minutes)))
        for index in transitions:
            if str(contracts[index - 1]) == old and str(contracts[index]) == new and ts.iloc[index - 1] < boundary <= ts.iloc[index]:
                covered.add(int(index))
    if set(transitions.tolist()) - covered:
        raise ValueError("contract change has no advance roll instruction")
    # Sample one close per observed hour, plus each trade/roll minute.
    hour = ts.dt.floor("h").to_numpy()
    hour_ends = np.r_[np.flatnonzero(hour[1:] != hour[:-1]), len(frame) - 1]
    hour_end_set = set(hour_ends.tolist())
    events = sorted(set(hour_ends.tolist()) | set(latest_target) |
                    roll_exit_indices | roll_entry_indices | set(transitions.tolist()))
    ledger = (ledger_factory or Ledger)(spec, costs, starting_capital)
    target = 0
    records = []
    changes = []
    previous_net = previous_gross = 0.0
    known_target = ts.iloc[0]
    def record_change(stamp, attribution_at, kind):
        nonlocal previous_net, previous_gross
        changes.append({"ts": stamp, "attribution_at": attribution_at, "kind": kind,
                        "step_net": ledger.net_pnl - previous_net,
                        "step_gross": ledger.gross_pnl - previous_gross})
        previous_net, previous_gross = ledger.net_pnl, ledger.gross_pnl
    for i in events:
        if i in latest_target:
            target = latest_target[i]
            known_target = target_known[i]
        stamp = ts.iloc[i].to_pydatetime()
        contract = str(contracts[i])
        if ledger.position and ledger.contract != contract:
            raise ValueError("position crossed a roll without an exit")
        if ledger.position:
            ledger.mark(contract, float(opens[i]))
        prior_fills = len(ledger.fills)
        if i in roll_exit_indices:
            if ledger.position:
                ledger.sell(stamp, contract, float(opens[i]), "scheduled roll exit")
        elif target and not ledger.position and not any(a <= ts.iloc[i] < b for a, b in suspended):
            ledger.buy(stamp, contract, float(opens[i]),
                       "scheduled roll entry" if i in roll_entry_indices else "signal")
        elif not target and ledger.position:
            ledger.sell(stamp, contract, float(opens[i]))
        for fill_index in range(prior_fills, len(ledger.fills)):
            known_fill = roll_known.get(i, known_target)
            if known_fill > ts.iloc[i]:
                raise ValueError("fill preceded its instruction")
            ledger.fills[fill_index] = replace(ledger.fills[fill_index], known_at=known_fill.to_pydatetime())
        record_change(ts.iloc[i], ts.iloc[i], "open and fills")
        if ledger.position:
            ledger.mark(contract, float(closes[i]))
        close_at = ts.iloc[i] + pd.Timedelta(minutes=bar_minutes)
        record_change(close_at, close_at - pd.Timedelta(nanoseconds=1), "interval close")
        if i in hour_end_set:
            records.append({"ts": close_at if bar_minutes >= 60 else ts.iloc[i].floor("h") + pd.Timedelta(hours=1),
                            "equity": ledger.equity, "gross_pnl": ledger.gross_pnl,
                            "net_pnl": ledger.net_pnl, "position": ledger.position,
                            "contract": contract})
    return BacktestResult(ledger, pd.DataFrame.from_records(records), pd.DataFrame(changes))
