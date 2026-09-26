import copy
import io
import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from does_the_edge_hold.public_data import fetch, audit_snapshot
from does_the_edge_hold.public_study import run_public
from does_the_edge_hold.plan import freeze

def test_wholly_synthetic_public_snapshot_through_sealed_study(tmp_path, monkeypatch):
    import urllib.request
    import urllib.parse
    dates = pd.date_range("2017-01-01", periods=60, freq="D", tz="UTC")
    prices = 100 + np.sin(np.arange(60) / 3) * 10
    rows = [[int(ts.timestamp()), float(p - 2), float(p + 2), float(p), float(p + 1), 10.] for ts, p in zip(dates, prices)]
    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **k: io.BytesIO(json.dumps(rows).encode()))
    monkeypatch.setattr("does_the_edge_hold.public_data.time.sleep", lambda _: None)
    snapshot = tmp_path / "snapshot"
    audit = fetch(snapshot, start="2017-01-01", end="2017-03-02")
    assert all(f["exact_response_replay"] for f in audit["files"])
    plan = json.loads((Path(__file__).parents[1] / "research/public-spot/plan.json").read_text())
    plan["signal_families"] = {"momentum": {"lookback_bars": [2, 3]}}
    plan["configuration_count"] = 2
    plan["selection"]["minimum_entry_trades"] = 2
    plan["statistics"]["replicates"] = 50
    plan["splits_utc"] = {"development": ["2017-01-01", "2017-01-21"],
                         "validation": ["2017-01-21", "2017-02-10"],
                         "historical_final": ["2017-02-10", "2017-03-02"]}
    paths = [tmp_path / n for n in ("plan.json", "audit.json", "lock.json")]
    paths[0].write_text(json.dumps(plan))
    paths[1].write_text(json.dumps(audit))
    freeze(*paths)
    output = tmp_path / "study"
    result = run_public(snapshot, paths[0], paths[2], output)
    assert result["included"] == ["BTC-USD", "ETH-USD"]
    assert all(r["failed_runs"] == 0 and r["run_count"] == 24 for r in result["markets"].values())
    assert (output / "BTC-USD/report.md").is_file()
    with pytest.raises(FileExistsError):
        run_public(snapshot, paths[0], paths[2], output)
    file = snapshot / "BTC-USD.parquet"
    bars = pd.read_parquet(file)
    bars.loc[0, "open"] += 1
    bars.to_parquet(file, index=False)
    with pytest.raises(ValueError, match="changed"):
        audit_snapshot(snapshot)
