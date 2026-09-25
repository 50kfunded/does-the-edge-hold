from datetime import datetime, timezone

import pytest

from does_the_edge_hold.ledger import ContractSpec, Costs, Ledger


T = datetime(2024, 1, 1, tzinfo=timezone.utc)


def test_cash_equity_and_costs_reconcile() -> None:
    ledger = Ledger(ContractSpec("TEST", 20, 0.25), Costs(2, 1), 1_000)
    ledger.buy(T, "A", 100)
    ledger.mark("A", 101)
    assert ledger.gross_pnl == 20
    assert ledger.unrealized == 15
    assert ledger.equity == 1_013
    ledger.sell(T, "A", 101)
    assert ledger.gross_pnl == 20
    assert ledger.commission_paid == 4
    assert ledger.slippage_paid == 10
    assert ledger.cash_pnl == 6
    assert ledger.equity == 1_006
    assert ledger.trade_count == 1


def test_negative_prices_use_differences() -> None:
    ledger = Ledger(ContractSpec("CL", 1000, 0.01), Costs(0, 0))
    ledger.buy(T, "CLJ0", -2)
    ledger.mark("CLJ0", 0)
    assert ledger.unrealized == 2_000
    ledger.sell(T, "CLJ0", 1)
    assert ledger.net_pnl == 3_000


def test_roll_gap_is_not_profit() -> None:
    ledger = Ledger(ContractSpec("NQ", 20, 0.25), Costs(2, 1))
    ledger.buy(T, "NQH4", 10_000)
    ledger.roll(T, "NQH4", 10_001, "NQM4", 10_120)
    ledger.mark("NQM4", 10_120)
    assert ledger.gross_pnl == 20
    assert ledger.net_pnl == 20 - 3 * (2 + 5)
    assert len(ledger.fills) == 3
    with pytest.raises(ValueError):
        ledger.mark("NQU4", 10_300)


def test_small_gross_win_can_fail_after_assumed_costs() -> None:
    ledger = Ledger(ContractSpec("NQ", 20, 0.25), Costs(5, 1))
    ledger.buy(T, "NQH4", 100)
    ledger.sell(T, "NQH4", 100.5)
    assert ledger.gross_pnl == 10
    assert ledger.commission_paid == 10
    assert ledger.slippage_paid == 10
    assert ledger.net_pnl == -10
