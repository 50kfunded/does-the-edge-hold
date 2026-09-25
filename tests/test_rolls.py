import pandas as pd
import pytest

from does_the_edge_hold.ledger import ContractSpec, Costs
from does_the_edge_hold.rolls import RollGateError, attach_contracts
from does_the_edge_hold.timing import simulate


def test_schedule_and_ledger_ignore_roll_price_gap() -> None:
    ts = pd.date_range("2024-01-08", periods=4, freq="min", tz="UTC")
    bars = pd.DataFrame({"ts": ts, "open": [100, 101, 201, 202],
                         "close": [100, 101, 201, 202]})
    schedule = pd.DataFrame({"effective_at": [ts[0], ts[2]],
                             "contract": ["A", "B"]})
    bars = attach_contracts(bars, schedule)
    decision = pd.DataFrame({"known_at": [ts[0]], "target": [1]})
    result = simulate(bars, decision, ContractSpec("SYN", 1, 1), Costs(0, 0))
    assert result.ledger.gross_pnl == 2
    assert result.ledger.net_pnl == 2
    assert [(f.side, f.reason) for f in result.ledger.fills] == [
        ("buy", "signal"), ("sell", "scheduled roll exit"),
        ("buy", "scheduled roll entry")]


def test_missing_mapping_blocks_pnl() -> None:
    bars = pd.DataFrame({"ts": [pd.Timestamp("2024-01-08", tz="UTC")],
                         "open": [100], "close": [100], "contract": [None]})
    with pytest.raises(ValueError, match="gated"):
        simulate(bars, pd.DataFrame({"known_at": [], "target": []}),
                 ContractSpec("SYN", 1, 1), Costs())
    with pytest.raises(RollGateError, match="first bar"):
        attach_contracts(bars, pd.DataFrame({"effective_at": [pd.Timestamp("2024-01-09", tz="UTC")],
                                             "contract": ["A"]}))
