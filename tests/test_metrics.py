import pandas as pd

from does_the_edge_hold.ledger import ContractSpec, Costs
from does_the_edge_hold.metrics import daily_pnl, summarize
from does_the_edge_hold.timing import simulate


def test_return_is_on_account_capital_not_futures_price() -> None:
    minute = pd.DataFrame({"ts": pd.date_range("2024-01-01", periods=3, freq="h", tz="UTC"),
                           "open": [-2, 0, 1], "close": [-2, 0, 1], "contract": "A"})
    decision = pd.DataFrame({"known_at": [minute["ts"].iloc[0]], "target": [1]})
    result = simulate(minute, decision, ContractSpec("TEST", 1000, 0.01),
                      Costs(0, 0), starting_capital=10_000)
    report = summarize(result)
    assert report["net_pnl_usd"] == 3_000
    assert report["account_return"] == 0.3


def test_midnight_mark_belongs_to_the_day_that_just_finished() -> None:
    minute = pd.DataFrame({"ts": pd.to_datetime(["2023-12-31T23:58Z", "2023-12-31T23:59Z",
                                                  "2024-01-01T00:00Z"]),
                           "open": [100, 100, 102], "close": [100, 102, 103], "contract": "A"})
    decision = pd.DataFrame({"known_at": [minute["ts"].iloc[0]], "target": [1]})
    result = simulate(minute, decision, ContractSpec("TEST", 10, 1), Costs(0, 0))
    daily = daily_pnl(result)
    assert daily.loc["2023-12-31"] == 20
    assert daily.loc["2024-01-01"] == 10
    assert summarize(result, "2023-01-01", "2024-01-01")["net_pnl_usd"] == 20
    assert summarize(result, "2024-01-01", "2025-01-01")["net_pnl_usd"] == 10
