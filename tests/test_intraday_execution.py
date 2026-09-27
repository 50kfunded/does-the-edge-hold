import numpy as np
import pandas as pd
import pytest
from does_the_edge_hold.intraday import prepare_window, window_decisions, simulate_window
from does_the_edge_hold.signals import SignalSpec
from does_the_edge_hold.specs import SPECS
from does_the_edge_hold.ledger import Costs

def bars(date="2024-01-08", offset=0):
    ts = pd.date_range(date + "T08:00Z", periods=240, freq="min")
    price = 100 + offset + np.arange(240) * .25
    return pd.DataFrame({"ts": ts, "open": price, "high": price + .25, "low": price - .25, "close": price, "volume": 10})

def targets(stamps, values):
    return pd.DataFrame({"known_at": pd.to_datetime(stamps, utc=True), "target": values})

def run(frame, target=None, delay=1):
    window = prepare_window(frame, "opaque|" + str(frame.ts.iloc[0].date()))
    target = target if target is not None else targets([str(window.date.date()) + "T09:00Z"], [1])
    return simulate_window(window, target, SPECS["NQ"], Costs(2.5, 1), delay)

def test_clock_warmup_and_twelve_bar_definition():
    window = prepare_window(bars(), "source|date")
    assert window.bars.known_at.iloc[0] == pd.Timestamp("2024-01-08T08:05Z")
    signal = window_decisions(window, SignalSpec("momentum", 12))
    assert signal.loc[signal.known_at < pd.Timestamp("2024-01-08T09:00Z"), "target"].eq(0).all()
    assert signal.loc[signal.known_at == pd.Timestamp("2024-01-08T09:00Z"), "target"].iloc[0] == 1
    result = run(bars(), signal)
    assert result["ledger"].fills[0].ts == pd.Timestamp("2024-01-08T09:01Z")
    assert result["ledger"].fills[0].known_at == pd.Timestamp("2024-01-08T09:00Z")

def test_cross_date_jump_has_no_pnl_and_no_state_carry():
    a = run(bars())
    b = run(bars("2024-01-09", 100000))
    assert a["net_pnl_usd"] == b["net_pnl_usd"]
    assert a["position"] == b["position"] == 0
    assert a["pending"] is b["pending"] is None
    with pytest.raises(ValueError, match="one UTC source date"):
        prepare_window(pd.concat([bars(), bars("2024-01-09")]), "bad")

def test_strict_entry_cutoff_and_terminal_priority():
    assert run(bars(), targets(["2024-01-08T11:29Z"], [1]))["fills"] == 0
    assert run(bars(), targets(["2024-01-08T11:28Z"], [1]))["fills"] == 2
    result = run(bars(), targets(["2024-01-08T09:00Z", "2024-01-08T11:49Z", "2024-01-08T11:50Z"], [1, 0, 1]))
    assert result["ledger"].fills[-1].reason == "scheduled terminal exit"
    assert result["ledger"].fills[-1].ts == pd.Timestamp("2024-01-08T11:51Z")
    assert run(bars(), delay=5)["ledger"].fills[-1].ts == pd.Timestamp("2024-01-08T11:55Z")

def test_missing_terminal_cannot_backdate_earlier_fills():
    full = run(bars())
    short = run(bars().loc[lambda x: x.ts < pd.Timestamp("2024-01-08T11:51Z")])
    assert short["status"] == "failed_unresolved" and short["score"] is None
    assert short["ledger"].fills == full["ledger"].fills[:1]
    assert short["position"] == 1 and short["pending"] is None

def test_partial_bucket_zero_variance_and_future_prices():
    frame = bars()
    frame[["open", "high", "low", "close"]] = 100.
    zero = window_decisions(prepare_window(frame, "zero"), SignalSpec("mean_reversion", 12, .5))
    assert zero.target.eq(0).all()
    part = prepare_window(bars().drop(index=15), "partial")
    assert len(part.bars) == 47
    signal = window_decisions(part, SignalSpec("momentum", 12))
    assert signal.loc[signal.known_at == pd.Timestamp("2024-01-08T09:00Z"), "target"].iloc[0] == 0
    original = window_decisions(prepare_window(bars(), "x"), SignalSpec("mean_reversion", 6, .5))
    changed = bars()
    mask = changed.ts >= pd.Timestamp("2024-01-08T10:00Z")
    changed.loc[mask, ["open", "high", "low", "close"]] += 1000
    after = window_decisions(prepare_window(changed, "x"), SignalSpec("mean_reversion", 6, .5))
    pd.testing.assert_frame_equal(original.loc[original.known_at <= pd.Timestamp("2024-01-08T10:00Z")], after.loc[after.known_at <= pd.Timestamp("2024-01-08T10:00Z")])

@pytest.mark.parametrize("market", ["NQ", "ES", "YM"])
def test_multiplier_costs_and_terminal_cash_reconcile(market):
    window = prepare_window(bars(), "opaque")
    result = simulate_window(window, targets(["2024-01-08T09:00Z"], [1]), SPECS[market], Costs(2.5, 1), 1)
    assert result["status"] == "ok" and result["terminal_flat"]
    assert abs(result["reconciliation_error_usd"]) < 1e-8
    assert result["ledger"].cash_pnl == result["net_pnl_usd"]
    assert result["ledger"].unrealized == 0 and result["commission_usd"] == 5
    assert result["slippage_usd"] >= 2 * SPECS[market].tick_size * SPECS[market].multiplier
