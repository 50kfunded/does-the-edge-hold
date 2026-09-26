from datetime import datetime, timezone
import pytest
from does_the_edge_hold.spot import SpotLedger
from does_the_edge_hold.ledger import ContractSpec, Costs

def test_spot_pays_principal_and_reconciles_cash_inventory():
    ledger = SpotLedger(ContractSpec("coin", 2, .01), Costs(0, 0, 10, 5), 1000)
    stamp = datetime(2024, 1, 1, tzinfo=timezone.utc)
    ledger.buy(stamp, "coin", 100)
    assert ledger.cash_balance == pytest.approx(1000 - 2 * 100.05 * 1.001)
    assert ledger.equity == pytest.approx(ledger.cash_balance + 200)
    ledger.mark("coin", 110)
    ledger.sell(stamp, "coin", 110)
    assert ledger.gross_pnl == 20
    assert ledger.net_pnl == pytest.approx(20 - ledger.commission_paid - ledger.slippage_paid)
    assert ledger.cash_balance == ledger.equity
    with pytest.raises(ValueError, match="cash"):
        SpotLedger(ContractSpec("coin", 1, .01), Costs(0, 0), 50).buy(stamp, "coin", 100)
