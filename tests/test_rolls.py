import pandas as pd
import pytest

from does_the_edge_hold.ledger import ContractSpec, Costs
from does_the_edge_hold.rolls import RollGateError, attach_contracts
from does_the_edge_hold.timing import simulate, scheduled_instructions


def test_schedule_and_ledger_ignore_roll_price_gap() -> None:
    ts = pd.date_range("2024-01-08", periods=4, freq="min", tz="UTC")
    bars = pd.DataFrame({"ts": ts, "open": [100, 101, 201, 202],
                         "close": [100, 101, 201, 202]})
    schedule = pd.DataFrame({"effective_at": [ts[0], ts[2]],
                             "contract": ["A", "B"]})
    bars = attach_contracts(bars, schedule)
    decision = pd.DataFrame({"known_at": [ts[0]], "target": [1]})
    result = simulate(bars, decision, ContractSpec("SYN", 1, 1), Costs(0, 0),
                      roll_instructions=scheduled_instructions(schedule, lead_minutes=1))
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


def test_future_observation_cannot_move_an_executed_exit_backwards():
    ts = pd.date_range("2024-01-01", periods=7, freq="min", tz="UTC")
    bars = pd.DataFrame({"ts": ts, "open": [100, 110, 120, 130, 140, 250, 260],
                         "close": [100, 110, 120, 130, 140, 250, 260],
                         "contract": ["A"] * 5 + ["B"] * 2})
    schedule = pd.DataFrame({"effective_at": [ts[0], ts[5]], "contract": ["A", "B"]})
    instructions = scheduled_instructions(schedule, lead_minutes=2)
    targets = pd.DataFrame({"known_at": [ts[0]], "target": [1]})
    def run(frame, delay=0):
        return simulate(frame, targets, ContractSpec("SYN", 1, 1), Costs(1, 1),
                        roll_instructions=instructions, delay_minutes=delay)
    a, b = run(bars), run(bars.drop(index=4))
    assert a.ledger.fills[1] == b.ledger.fills[1]
    assert pd.Timestamp(a.ledger.fills[1].ts) == ts[3]
    delayed = run(bars, 1)
    assert pd.Timestamp(delayed.ledger.fills[1].ts) == ts[4]
    assert delayed.ledger.net_pnl == pytest.approx(delayed.ledger.gross_pnl - delayed.ledger.commission_paid - delayed.ledger.slippage_paid)
    with pytest.raises(ValueError, match="no permitted"):
        run(bars.drop(index=[3, 4]))
    with pytest.raises(ValueError, match="advance"):
        simulate(bars, targets, ContractSpec("SYN", 1, 1), Costs())
