import copy
import pytest
from does_the_edge_hold.example import example_plan
from does_the_edge_hold.plan import validate
from does_the_edge_hold.ledger import ContractSpec, Costs

@pytest.mark.parametrize("field", ["count", "duplicate", "lookback", "split", "metric", "cost", "exit"])
def test_invalid_protocol_is_rejected(field):
    plan = example_plan()
    plan.update(version=3, prior_exposure="synthetic test")
    if field == "count": plan["configuration_count"] = True
    elif field == "duplicate": plan["signal_families"]["momentum"]["lookback_hours"][0] = 24
    elif field == "lookback": plan["signal_families"]["momentum"]["lookback_hours"][0] = 0
    elif field == "split": plan["splits_utc"]["validation"][0] = "2025-01-01"
    elif field == "metric": plan["selection"]["metric"] = "choose later P&L"
    elif field == "cost": plan["execution"]["scenarios"][0]["commission_usd_per_side"] = float("nan")
    else: plan["signal_families"]["mean_reversion"]["exit_z"] = 1
    with pytest.raises(ValueError): validate(plan)

def test_nonfinite_specs_and_costs_fail():
    with pytest.raises(ValueError): ContractSpec("bad", float("inf"), .1)
    with pytest.raises(ValueError): Costs(float("nan"), 1)
    with pytest.raises(ValueError): Costs(0, 0, 0, 10000)
