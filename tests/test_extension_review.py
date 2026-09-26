import pandas as pd
import pytest
from does_the_edge_hold.signals import REGISTRY, DECLARATIONS, register_signal, SignalSpec, decisions
from does_the_edge_hold.experiments import market_manifest, run_market
from does_the_edge_hold.example import example_plan
from does_the_edge_hold.synthetic import make_bars
from does_the_edge_hold.adapters import MarketAdapter
from does_the_edge_hold.specs import SPECS

CONTROL = {"target": 0}

def controlled(bars, spec):
    return pd.DataFrame({"known_at": bars.known_at, "target": CONTROL["target"]})

def future(bars, spec):
    return pd.DataFrame({"known_at": bars.known_at, "target": (bars.close.shift(-1) > bars.close).astype(int)})

@pytest.fixture(autouse=True)
def clean_extensions(monkeypatch):
    monkeypatch.setattr("does_the_edge_hold.signals.REGISTRY", REGISTRY.copy())
    monkeypatch.setattr("does_the_edge_hold.signals.DECLARATIONS", DECLARATIONS.copy())
    # Experiments keeps its registry reference, so restore registrations in place.
    prior, declarations = REGISTRY.copy(), DECLARATIONS.copy()
    yield
    REGISTRY.clear(); REGISTRY.update(prior)
    DECLARATIONS.clear(); DECLARATIONS.update(declarations)

def test_undeclared_mutable_global_is_rejected():
    with pytest.raises(ValueError, match="undeclared extension global: CONTROL"):
        register_signal("controlled", controlled, inputs=["known_at", "contract", "close"])

def test_global_state_changes_identity_and_rejects_old_seal(monkeypatch):
    # Use the actual shared registry, as extensions and the runner must agree.
    monkeypatch.setattr("does_the_edge_hold.signals.REGISTRY", REGISTRY)
    monkeypatch.setattr("does_the_edge_hold.signals.DECLARATIONS", DECLARATIONS)
    register_signal("controlled", controlled, inputs=["known_at", "contract", "close"], state=["CONTROL"])
    plan = example_plan()
    plan["signal_families"] = {"controlled": {"lookback_bars": [1]}}
    plan["configuration_count"] = 1
    old = market_manifest("SYN", "plan", "data", MarketAdapter(SPECS["SYN"]))
    monkeypatch.setitem(CONTROL, "target", 1)
    new = market_manifest("SYN", "plan", "data", MarketAdapter(SPECS["SYN"]))
    assert old["execution_sha256"] != new["execution_sha256"]
    with pytest.raises(ValueError, match="actual runtime"):
        run_market(make_bars(minutes=600), "SYN", plan, "plan", "data", execution_manifest=old)

def test_future_close_callback_cannot_enter_research():
    register_signal("future", future, inputs=["known_at", "contract", "close"])
    frame = pd.DataFrame({"known_at": pd.date_range("2020-01-01", periods=8, freq="h", tz="UTC"),
                          "contract": "x", "close": range(8)})
    with pytest.raises(ValueError, match="causal prefix"):
        decisions(frame, SignalSpec("future", 1))
