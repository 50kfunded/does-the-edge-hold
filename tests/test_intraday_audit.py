import pandas as pd
from does_the_edge_hold.intraday_plan import default_plan
from does_the_edge_hold.intraday_audit import coverage, assess_source_day, SOURCE_DOCS
from does_the_edge_hold.intraday_audit import run_audit
import json
import numpy as np

def test_fixed_candidates_include_absent_start_and_partial_warmup():
    plan = default_plan()
    plan["splits_utc"] = {"development": ["2024-01-05", "2024-01-08"], "validation": ["2024-01-08", "2024-01-09"], "historical_final": ["2024-01-09", "2024-01-10"]}
    ts = pd.date_range("2024-01-08T08:00Z", periods=240, freq="min")
    table = coverage(pd.DataFrame({"ts": ts}), plan, "NQ", "NQ.c.0")
    assert table.date.to_list() == ["2024-01-05", "2024-01-08", "2024-01-09"]
    assert table.eligible.to_list() == [False, True, False]
    assert table.iloc[0].reason == "empty_candidate" and table.iloc[0].missing_warmup_minutes == 60
    short = coverage(pd.DataFrame({"ts": ts.delete(15)}), plan, "NQ", "NQ.c.0")
    assert not short.iloc[1].eligible and short.iloc[1].missing_warmup_minutes == 1

def test_no_documented_continuity_no_empirical_pnl():
    source = [{"market": "NQ", "quality_ready": True}]
    origin = [{"market": "NQ", "verified_match": True, "selected_root": "NQc0", "comparison": "exact values and dtypes; no precision cast"}]
    assert assess_source_day(source, origin, default_plan(), {"historical_semantics_reviewed": False})["status"] == "blocked"
    ready = assess_source_day(source, origin, default_plan(), SOURCE_DOCS)
    assert ready["included"] == ["NQ"] and "GC" in ready["excluded"]

def test_absent_optional_sources_are_recorded_without_blocking_nq(tmp_path):
    plan = default_plan()
    plan["splits_utc"] = {"development": ["2024-01-05", "2024-01-08"], "validation": ["2024-01-08", "2024-01-09"], "historical_final": ["2024-01-09", "2024-01-10"]}
    bars, cache = tmp_path / "bars", tmp_path / "cache"
    bars.mkdir(); cache.mkdir()
    frame = pd.DataFrame({"ts": pd.date_range("2024-01-08T08:00Z", periods=240, freq="min"),
                          "open": 100., "high": 101., "low": 99., "close": 100., "volume": np.full(240, 10, dtype="int64")}).set_index("ts")
    frame.to_parquet(bars / "NQ_1m.parquet")
    frame.to_parquet(cache / "databento_NQc0_ohlcv-1m_fixture_ctx.parquet")
    path = tmp_path / "plan.json"; path.write_text(json.dumps(plan))
    audit = run_audit(bars, cache, path, tmp_path / "audit")
    assert audit["readiness"]["primary_ready"] and audit["readiness"]["included"] == ["NQ"]
    assert "ES" in audit["readiness"]["excluded"] and audit["splits"]["ES"]["validation"]["empty"] == 1
