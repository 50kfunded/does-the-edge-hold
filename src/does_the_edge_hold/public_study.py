"""An explicitly separate historical spot case, using the common evaluator."""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
from .adapters import MarketAdapter
from .data import sha256_file
from .daily_clock import DailyClock
from .execution import write_manifest
from .experiments import run_market, rank_changes, winner_uncertainty, market_manifest
from .ledger import ContractSpec
from .plan import verify, validate
from .public_data import audit_snapshot
from .reporting import market_report
from .spot import SpotLedger
from .walk_forward import evaluate

def run_public(snapshot, plan_path, lock_path, output):
    snapshot, output = Path(snapshot), Path(output)
    plan = json.loads(Path(plan_path).read_text())
    lock = json.loads(Path(lock_path).read_text())
    audit = audit_snapshot(snapshot, semantic=lock.get("identity_version") == 2)
    verify(plan, audit, lock)
    if any(f["quality_status"] != "ready" for f in audit["files"]):
        raise ValueError("public spot quality gate is blocked")
    primary = plan["universe"]["primary"]
    required = plan["universe"]["required"]
    if {f["market"] for f in audit["files"]} != set(required):
        raise ValueError("snapshot universe differs from the protocol")
    output.mkdir(parents=True, exist_ok=False)
    (output / "data-audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    (output / "snapshot-manifest.json").write_bytes((snapshot / "snapshot.json").read_bytes())
    summary = {"status": "historical_public_spot", "primary": primary, "included": required,
               "excluded": {}, "futures_status": "blocked; no mapping or advance-policy evidence", "markets": {}}
    winner = None
    for market in [primary] + [m for m in required if m != primary]:
        bars = pd.read_parquet(snapshot / f"{market}.parquet")
        adapter = MarketAdapter(ContractSpec(market, 1, .01), "spot", 1440, SpotLedger)
        source_hash = lock["source_hashes"][f"{market}_1d"]
        manifest = market_manifest(market, lock["plan_sha256"], source_hash, adapter,
                                   extra_evidence={"snapshot_manifest_sha256": sha256_file(snapshot / "snapshot.json")})
        manifest["artifact_sha256"] = sha256_file(snapshot / f"{market}.parquet")
        folder = output / market
        folder.mkdir()
        write_manifest(manifest, folder / "execution.json")
        rows, daily = run_market(bars, market, plan, lock["plan_sha256"], source_hash,
                                 adapter=adapter, execution_manifest=manifest)
        ranks = rank_changes(rows, plan["selection"]["minimum_entry_trades"])
        if market == primary:
            winner = ranks["development_winner"]
        report = {"market": market, "status": "historical_public_spot", "primary": primary,
                  "minute_rows": None, "source_rows": len(bars), "plan_sha256": lock["plan_sha256"],
                  "source_sha256": source_hash, "execution_sha256": manifest["execution_sha256"],
                  "rank_changes": ranks, "selected_config_from_primary": winner,
                  "winner_uncertainty": winner_uncertainty(winner, daily, plan),
                  "walk_forward": evaluate(daily, rows, plan["execution"]["starting_capital_usd_per_market"],
                      plan["selection"]["minimum_entry_trades"], periods_per_year=DailyClock.from_plan(plan).periods_per_year),
                  "protocol": plan, "audit": next(f for f in audit["files"] if f["market"] == market), "runs": rows}
        (folder / "results.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        pd.DataFrame(daily).to_csv(folder / "daily-pnl.csv", index_label="session_date")
        market_report(report, folder, daily)
        summary["markets"][market] = {"run_count": len({r["run_id"] for r in rows}),
            "failed_runs": sum(r["status"] == "failed" for r in rows),
            "development_winner": ranks["development_winner"], "primary_pick": winner,
            "execution_sha256": manifest["execution_sha256"]}
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary
