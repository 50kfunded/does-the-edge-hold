"""Causal execution within one opaque source-day segment; no roll returns."""
from __future__ import annotations
from dataclasses import dataclass, replace
import math
import numpy as np
import pandas as pd
from .ledger import Ledger, Fill, Costs
from .semantic import semantic_digest

MINUTE = 60_000_000_000

class WindowLedger(Ledger):
    def _fill(self, ts, contract, side, raw, reason):
        direction = 1 if side == "buy" else -1
        scaled = raw / self.spec.tick_size
        nearest = round(scaled)
        rounded = nearest if math.isclose(scaled, nearest, rel_tol=0, abs_tol=1e-9) else math.ceil(scaled) if direction > 0 else math.floor(scaled)
        price = (rounded + direction * self.costs.slippage_ticks_per_side) * self.spec.tick_size
        slip = direction * (price - raw) * self.spec.multiplier
        self.commission_paid += self.costs.commission_per_side
        self.slippage_paid += slip
        self.cash_pnl -= self.costs.commission_per_side
        self.fills.append(Fill(ts, contract, side, raw, price, self.costs.commission_per_side, slip, reason))
        return price

@dataclass
class Window:
    date: pd.Timestamp
    source_segment_id: str
    times: np.ndarray
    opens: np.ndarray
    closes: np.ndarray
    bars: pd.DataFrame

def prepare_window(minutes, source_segment_id):
    if minutes.empty: raise ValueError("empty source-day window")
    semantic_digest([minutes])
    dates = minutes.ts.dt.floor("D")
    if dates.nunique() != 1: raise ValueError("one UTC source date only")
    date = dates.iloc[0]
    times = minutes.ts.dt.as_unit("ns").astype("int64").to_numpy()
    offsets = ((times - date.value) // MINUTE).astype(int)
    if ((offsets < 480) | (offsets >= 720)).any() or (times % MINUTE != 0).any():
        raise ValueError("only start-stamped observed window minutes are allowed")
    rows = []
    values = minutes[["open", "high", "low", "close"]].to_numpy(dtype=float)
    for start in range(480, 720, 5):
        indices = np.flatnonzero((offsets >= start) & (offsets < start + 5))
        if len(indices) != 5 or not np.array_equal(offsets[indices], np.arange(start, start + 5)):
            continue
        group = values[indices]
        rows.append({"known_at": date.value + (start + 5) * MINUTE, "bucket_start": date.value + start * MINUTE,
                     "open": float(group[0, 0]), "high": float(group[:, 1].max()), "low": float(group[:, 2].min()),
                     "close": float(group[-1, 3]), "observed_minutes": 5})
    bars = pd.DataFrame(rows, columns=["known_at", "bucket_start", "open", "high", "low", "close", "observed_minutes"])
    for name in ("known_at", "bucket_start"):
        bars[name] = pd.to_datetime(bars[name], unit="ns", utc=True)
    return Window(date, source_segment_id, times, minutes.open.to_numpy(dtype=float), minutes.close.to_numpy(dtype=float), bars)

def window_decisions(window, spec):
    bars = window.bars
    target = np.zeros(len(bars), dtype=np.int8)
    n = spec.lookback_hours
    holding = 0
    stamps = bars.known_at.astype("int64").to_numpy()
    prices, opens = bars.close.to_numpy(dtype=float), bars.open.to_numpy(dtype=float)
    for i in range(len(bars)):
        if stamps[i] < window.date.value + 540 * MINUTE:
            continue
        # A missing bucket cannot shorten the declared elapsed lookback.
        if i + 1 < n or not np.all(np.diff(stamps[i + 1 - n:i + 1]) == 5 * MINUTE):
            holding = 0
        elif spec.family == "momentum":
            holding = int(prices[i] > opens[i + 1 - n])
        elif spec.family == "mean_reversion":
            close = prices[i + 1 - n:i + 1]
            sigma = close.std(ddof=1)
            if not np.isfinite(sigma) or sigma == 0:
                holding = 0
            else:
                z = (close[-1] - close.mean()) / sigma
                if holding and z >= 0: holding = 0
                elif not holding and z <= -spec.entry_z: holding = 1
        else:
            raise ValueError("source-day signals must have the frozen within-window definition")
        target[i] = holding
    return pd.DataFrame({"known_at": bars.known_at, "target": target})

def simulate_window(window, targets, spec, costs, delay_minutes, *, starting_capital=100000):
    """Pending fills use earlier information; the scheduled terminal instruction has priority."""
    if not isinstance(delay_minutes, int) or delay_minutes < 0: raise ValueError("delay must be nonnegative integer minutes")
    if not {"known_at", "target"}.issubset(targets) or not targets.target.isin([0, 1]).all():
        raise ValueError("aligned long/flat targets required")
    known = pd.to_datetime(targets.known_at, utc=True).dt.as_unit("ns")
    if not known.is_monotonic_increasing or known.duplicated().any(): raise ValueError("decisions must be unique and ordered")
    date = window.date
    if len(known) and not known.dt.floor("D").eq(date).all(): raise ValueError("decisions cannot cross source dates")
    ledger = WindowLedger(spec, costs, starting_capital=starting_capital)
    warmup, cutoff, terminal, end = [(date + pd.Timedelta(minutes=m)).value for m in (540, 690, 710, 720)]
    delay = delay_minutes * MINUTE
    decisions = [(int(ts), int(target)) for ts, target in zip(known.astype("int64"), targets.target) if warmup <= ts < terminal]
    pending = None
    exposure_ns, active_since = 0, None
    events = []
    def fill(index, target, known_ns, reason):
        nonlocal active_since, exposure_ns
        ts = pd.Timestamp(int(window.times[index]), tz="UTC")
        if target == ledger.position: return
        if target:
            if ts.value >= cutoff: return
            ledger.buy(ts, window.source_segment_id, float(window.opens[index]), reason)
            active_since = ts.value
        else:
            ledger.sell(ts, window.source_segment_id, float(window.opens[index]), reason)
            exposure_ns += ts.value - active_since
            active_since = None
        ledger.fills[-1] = replace(ledger.fills[-1], known_at=pd.Timestamp(known_ns, tz="UTC"))
        events.append({"at": ts.isoformat(), "known_at": pd.Timestamp(known_ns, tz="UTC").isoformat(), "reason": reason,
                       "position": ledger.position, "net_pnl_usd": ledger.net_pnl})
    def execute_pending(before, *, inclusive):
        nonlocal pending
        if pending is None: return
        at, target, instruction = pending
        index = int(np.searchsorted(window.times, at, side="left"))
        if index < len(window.times):
            stamp = int(window.times[index])
            if stamp < terminal and (stamp <= before if inclusive else stamp < before):
                fill(index, target, instruction, "signal")
                pending = None
    for at, target in decisions:
        # A prior instruction already executable at this open fills before the new close decision.
        execute_pending(at, inclusive=True)
        pending = None if target == ledger.position else (at + delay, target, at)
    execute_pending(terminal, inclusive=False)
    pending = None
    terminal_index = int(np.searchsorted(window.times, terminal + delay, side="left"))
    terminal_available = terminal_index < len(window.times) and int(window.times[terminal_index]) < end
    if ledger.position and terminal_available:
        fill(terminal_index, 0, (date + pd.Timedelta(hours=8)).value, "scheduled terminal exit")
    if ledger.position:
        # Preserve an unresolved open ledger and earlier events, never a completed score.
        ledger.mark(window.source_segment_id, float(window.closes[-1]))
        return {"status": "failed_unresolved", "error": "no permissible terminal observation", "score": None,
                "ledger": ledger, "events": events, "position": ledger.position, "pending": None}
    gross, net = ledger.gross_pnl, ledger.net_pnl
    return {"status": "ok", "ledger": ledger, "events": events, "position": 0, "pending": None,
            "gross_pnl_usd": gross, "net_pnl_usd": net, "commission_usd": ledger.commission_paid,
            "slippage_usd": ledger.slippage_paid, "entry_trades": ledger.trade_count, "fills": len(ledger.fills),
            "exposure_minutes": exposure_ns / MINUTE,
            "notional_entry_mean_usd": float(np.mean([abs(f.raw_price) * spec.multiplier for f in ledger.fills if f.side == "buy"])) if ledger.trade_count else 0.,
            "reconciliation_error_usd": net - (gross - ledger.commission_paid - ledger.slippage_paid),
            "terminal_flat": ledger.position == 0, "terminal_observation_available": terminal_available}
