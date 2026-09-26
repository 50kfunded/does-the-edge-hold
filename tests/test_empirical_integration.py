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
from does_the_edge_hold.semantic import semantic_file

@pytest.mark.parametrize("primary", ["NQ", "ES"])
def test_reader_cache_lock_gate_evaluator_report_and_blocked_primary(tmp_path, primary):
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
    optional = [m for m in ("NQ", "ES", "GC") if m != primary]
    plan.update(version=3, prior_exposure="synthetic software fixture", universe={"primary": primary, "required": [primary],
        "optional": optional, "allowed_exclusions": optional})
    plan["execution"]["starting_capital_usd_per_market"] = 123456
    plan["execution"]["scenarios"][1]["commission_usd_per_side"] = 3.25
    plan["signal_families"] = {"momentum": {"lookback_bars": [2]}}
    plan["configuration_count"] = 1
    if primary == "ES":
        plan["data_identity"] = "ohlcv-utc-ns-f64-v1"
        for row in audit["files"]:
            row["semantic"] = semantic_file(bars_root / f"{row['market']}_1m.parquet")
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
    saved = json.loads((output / f"{primary}_results.json").read_text())
    assert saved["primary"] == primary and saved["protocol"] == plan
    assert "selected_config_from_primary" in saved and "selected_config_from_NQ" not in saved
    assert "3.25" in (output / f"{primary}/report.md").read_text()
    universe = json.loads((output / "universe.json").read_text())
    assert "GC" in universe["excluded"]
    assert json.loads((output / "NQ_execution.json").read_text())["identity"]["evidence"]["additional"]
    if primary == "ES":
        path = bars_root / "ES_1m.parquet"
        pd.read_parquet(path).to_parquet(path, compression="gzip", row_group_size=113)
        second = tmp_path / "another-writer"
        run_empirical(bars_root, mapping, *files, second)
        after = json.loads((second / "ES_results.json").read_text())
        assert saved["runs"] == after["runs"]
        assert json.loads((output / "ES_execution.json").read_text())["artifact_sha256"] != json.loads((second / "ES_execution.json").read_text())["artifact_sha256"]
    (mapping / f"{primary}_policy-source.json").unlink()
    with pytest.raises(RuntimeError, match="blocked by roll gate"):
        run_empirical(bars_root, mapping, *files, tmp_path / "blocked")
    assert not (tmp_path / "blocked").exists()
