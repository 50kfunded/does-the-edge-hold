from does_the_edge_hold import experiments
from does_the_edge_hold.example import example_plan
from does_the_edge_hold.synthetic import make_bars
from does_the_edge_hold.timing import scheduled_instructions
from does_the_edge_hold.execution import seal
from does_the_edge_hold.adapters import MarketAdapter
from does_the_edge_hold.specs import SPECS
import pytest

def test_runtime_signal_change_cannot_reuse_run_identity(monkeypatch):
    bars = make_bars(minutes=3600)
    schedule = bars.loc[bars.contract.ne(bars.contract.shift()), ["ts", "contract"]].rename(columns={"ts": "effective_at"})
    args = (bars, "SYN", example_plan(), "plan", "source")
    prior = experiments.market_manifest("SYN", "plan", "source", MarketAdapter(SPECS["SYN"]), scheduled_instructions(schedule))
    a, _ = experiments.run_market(*args, roll_instructions=scheduled_instructions(schedule))
    original = experiments.decisions
    def flat(hourly, spec):
        result = original(hourly, spec)
        result["target"] = 0
        return result
    monkeypatch.setattr(experiments, "decisions", flat)
    with pytest.raises(ValueError, match="actual runtime"):
        experiments.run_market(*args, roll_instructions=scheduled_instructions(schedule), execution_manifest=prior)
    b, _ = experiments.run_market(*args, roll_instructions=scheduled_instructions(schedule))
    assert a[0]["run_id"] != b[0]["run_id"]
    assert a[0]["execution_sha256"] != b[0]["execution_sha256"]
    assert a[0]["net_pnl_usd"] != b[0]["net_pnl_usd"]

def test_seal_is_stable_and_records_environment():
    a = seal("p", {"SYN": "data"}, callables={"run_market": experiments.run_market})
    b = seal("p", {"SYN": "data"}, callables={"run_market": experiments.run_market})
    assert a["execution_sha256"] == b["execution_sha256"]
    assert "pandas" in a["identity"]["environment"]["packages"]
