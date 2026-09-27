import json
import pandas as pd
import pytest
from does_the_edge_hold.intraday_example import run_example
from does_the_edge_hold.intraday_study import verify_inputs
from does_the_edge_hold.intraday_plan import read

def test_offline_source_day_audit_lock_evaluate_and_report(tmp_path):
    root = tmp_path / "example"
    result = run_example(root, days=36, replicates=30)
    assert result["status"] == "synthetic_source_day" and result["runtime"]["cases"] == 165
    assert result["readiness"]["included"] == ["NQ", "ES", "YM"] and "GC" in result["readiness"]["excluded"]
    assert all(m["failed_windows"] == 0 for m in result["markets"].values())
    assert (root / "study/report.md").exists()
    for market in result["markets"]:
        report = read(root / f"study/{market}/results.json")
        rows = pd.DataFrame(report["runs"])
        assert rows.run_id.nunique() == 55 and rows.mask_sha256.nunique() == 1
        assert rows.maximum_window_reconciliation_error_usd.max() < 1e-7
        assert rows.terminal_flat_windows.equals(rows.days)
        panel = pd.read_csv(root / f"study/{market}/daily-pnl-all-scenarios.csv")
        assert len(panel) == 35  # one missing warmup excludes that date for every case
        assert panel.shape[1] == 56 and panel.notna().all().all()
    lock = read(root / "plan.lock.json")
    plan = read(root / "plan.json")
    source = root / "bars/NQ_1m.parquet"
    bars = pd.read_parquet(source)
    bars.loc[bars.index[0], "volume"] += 1
    bars.to_parquet(source)
    with pytest.raises(ValueError, match="observations changed"):
        verify_inputs(root / "bars", root / "cache", plan, lock, root / "audit")
