import pandas as pd
import pytest
from does_the_edge_hold.daily_clock import DailyClock
from does_the_edge_hold.ledger import ContractSpec, Costs
from does_the_edge_hold.metrics import daily_pnl, summarize
from does_the_edge_hold.timing import simulate

def test_sunday_and_dst_use_local_session_boundary():
    clock = DailyClock("new_york_futures_session", 252)
    stamps = pd.to_datetime(["2024-03-10T21:59Z", "2024-03-10T22:00Z", "2024-11-03T22:59Z", "2024-11-03T23:00Z"], utc=True)
    assert list(clock.labels(stamps).strftime("%Y-%m-%d")) == ["2024-03-10", "2024-03-11", "2024-11-03", "2024-11-04"]

def test_fees_at_midnight_are_not_backdated():
    ts = pd.to_datetime(["2023-12-31T23:59Z", "2024-01-01T00:00Z", "2024-01-01T00:01Z"], utc=True)
    bars = pd.DataFrame({"ts": ts, "open": [100, 102, 103], "close": [102, 103, 104], "contract": "A"})
    targets = pd.DataFrame({"known_at": [ts[0], ts[1]], "target": [1, 0]})
    run = simulate(bars, targets, ContractSpec("SYN", 1, 1), Costs(2, 1))
    daily = daily_pnl(run)
    assert daily.iloc[0] == -1 and daily.iloc[1] == -3
    assert daily.sum() == run.ledger.net_pnl
    for start, end in [("2023-01-01", "2024-01-01"), ("2024-01-01", "2025-01-01")]:
        assert summarize(run, start, end)["reconciliation_error_usd"] == pytest.approx(0)
    assert all(f.known_at <= f.ts for f in run.ledger.fills)
