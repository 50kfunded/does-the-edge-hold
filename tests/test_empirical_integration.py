"""Entire licensed-source command path on wholly synthetic fixtures."""
import json
import pandas as pd
import pytest
from does_the_edge_hold.audit import audit_file
from does_the_edge_hold.data import sha256_file
from does_the_edge_hold.example import example_plan
from does_the_edge_hold.experiments import run_empirical
from does_the_edge_hold.plan import freeze
from does_the_edge_hold.provenance import verify_minute_origin
from does_the_edge_hold.resolve import write_resolution
from does_the_edge_hold.roll_gate import ROLL_POLICY
from does_the_edge_hold.rolls import read_schedule
from does_the_edge_hold.synthetic import make_bars
from does_the_edge_hold.timing import scheduled_instructions

def test_reader_cache_lock_gate_evaluator_report_and_blocked_primary(tmp_path):
    bars_root, cache_root = tmp_path / "bars", tmp_path / "cache"
    bars_root.mkdir(); cache_root.mkdir()
    bars = make_bars(minutes=5760)
    # This source fixture declares a midnight boundary with synthetic IDs.
    bars.loc[:2879, "contract"] = "123"
    bars.loc[2880:, "contract"] = "456"
    export = bars.drop(columns="contract").set_index("ts")
    for market in ("NQ", "ES"):
        export.to_parquet(bars_root / f"{market}_1m.parquet")
        export.to_parquet(cache_root / f"databento_{market}c0_ohlcv-1m_fixture_ctx.parquet")
    audit = {"files": [audit_file(bars_root / f"{m}_1m.parquet", "1m", m) for m in ("NQ", "ES")]}
    origins = {"markets": [verify_minute_origin(bars_root, cache_root, m) for m in ("NQ", "ES")]}
    assert all(m["verified_match"] for m in origins["markets"])
    response = {"status": 0, "partial": [], "not_found": [], "stype_in": "continuous", "stype_out": "instrument_id",
                "result": {m + ".c.0": [{"d0": "2024-01-08", "d1": "2024-01-10", "s": "123"},
                    {"d0": "2024-01-10", "d1": "2024-01-12", "s": "456"}] for m in ("NQ", "ES")}}
    mapping = tmp_path / "mapping"
    evidence_path = write_resolution(response, audit, origins, mapping)
    evidence = json.loads(evidence_path.read_text())
    evidence["roll_policy"] = ROLL_POLICY
    for m in ("NQ", "ES"):
        instructions = scheduled_instructions(read_schedule(mapping / f"{m}_rolls.csv"))
        file = mapping / f"{m}_instructions.csv"
        instructions.to_csv(file, index=False)
        source = mapping / f"{m}_policy-source.json"
        source.write_text('{"scope": "synthetic offline fixture", "advance_availability": true}')
        evidence["markets"][m].update(instructions_sha256=sha256_file(file),
            policy_evidence={"kind": "advance_schedule", "reviewed": True, "sha256": sha256_file(source)})
    evidence_path.write_text(json.dumps(evidence))
    plan = example_plan()
    plan.update(version=3, prior_exposure="synthetic software fixture", universe={"primary": "NQ", "required": ["NQ"],
        "optional": ["ES", "GC"], "allowed_exclusions": ["ES", "GC"]})
    plan["signal_families"] = {"momentum": {"lookback_bars": [2]}}
    plan["configuration_count"] = 1
    plan["splits_utc"] = {"development": ["2024-01-08", "2024-01-10"], "validation": ["2024-01-10", "2024-01-11"],
                         "historical_final": ["2024-01-11", "2024-01-12"]}
    plan["statistics"] = {"clock": {"name": "new_york_futures_session", "periods_per_year": 252}, "replicates": 50}
    files = [tmp_path / name for name in ("audit.json", "origin.json", "plan.json", "lock.json")]
    for path, value in zip(files, (audit, origins, plan)):
        path.write_text(json.dumps(value))
    freeze(files[2], files[0], files[3])
    output = tmp_path / "success"
    result = run_empirical(bars_root, mapping, *files, output)
    assert set(result["markets"]) == {"NQ", "ES"}
    assert all(v["failed_runs"] == 0 for v in result["markets"].values())
    assert (output / "NQ/report.md").is_file()
    universe = json.loads((output / "universe.json").read_text())
    assert "GC" in universe["excluded"]
    assert json.loads((output / "NQ_execution.json").read_text())["identity"]["evidence"]["additional"]
    (mapping / "NQ_policy-source.json").unlink()
    with pytest.raises(RuntimeError, match="blocked by roll gate"):
        run_empirical(bars_root, mapping, *files, tmp_path / "blocked")
    assert not (tmp_path / "blocked").exists()
