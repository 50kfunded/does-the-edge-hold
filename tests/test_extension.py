from does_the_edge_hold.example import example_plan
from does_the_edge_hold.experiments import run_market
from does_the_edge_hold.adapters import MarketAdapter
from does_the_edge_hold.ledger import ContractSpec
from does_the_edge_hold.signals import REGISTRY, DECLARATIONS, register_signal
from does_the_edge_hold.synthetic import make_bars
from examples.breakout import breakout

def test_independent_signal_and_instrument_without_evaluator_edits(monkeypatch):
    monkeypatch.setitem(REGISTRY, "breakout", breakout)
    monkeypatch.setitem(DECLARATIONS, "breakout", {"inputs": ["known_at", "contract", "close", "high"], "state": [], "dependencies": []})
    bars = make_bars(minutes=600)
    bars["contract"] = "independent-input"
    plan = example_plan()
    plan["signal_families"] = {"breakout": {"lookback_bars": [2, 3]}}
    plan["configuration_count"] = 2
    rows, _ = run_market(bars, "external", plan, "plan", "data",
                         adapter=MarketAdapter(ContractSpec("external", 5, .1)))
    assert len({r["run_id"] for r in rows}) == 20
    assert not any(r["status"] == "failed" for r in rows)
