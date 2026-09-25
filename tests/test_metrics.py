import pandas as pd

from does_the_edge_hold.ledger import ContractSpec, Costs
from does_the_edge_hold.metrics import summarize
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
