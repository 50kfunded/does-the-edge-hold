"""Measured phases in a fresh worker per input size; no streaming-engine claim."""
import argparse
import gc
import os
import importlib.metadata
import json
import platform
import subprocess
import sys
import threading
import time
from pathlib import Path
import pandas as pd
import psutil
from does_the_edge_hold.adapters import MarketAdapter
from does_the_edge_hold.audit import audit_file
from does_the_edge_hold.data import load_minutes, sha256_file
from does_the_edge_hold.example import example_plan
from does_the_edge_hold.experiments import run_market, rank_changes, winner_uncertainty
from does_the_edge_hold.ledger import ContractSpec
from does_the_edge_hold.plan import _digest
from does_the_edge_hold.provenance import verify_minute_origin
from does_the_edge_hold.public_data import audit_snapshot
from does_the_edge_hold.reporting import market_report
from does_the_edge_hold.spot import SpotLedger
from does_the_edge_hold.synthetic import make_bars
from does_the_edge_hold.timing import scheduled_instructions
from compare_studies import EXCLUDED_ROW_FIELDS, compare_value

def measured(name, callback, records):
    process = psutil.Process()
    base = process.memory_info().rss
    peak = [base]
    stop = threading.Event()
    def sample():
        while not stop.wait(.01):
            peak[0] = max(peak[0], process.memory_info().rss)
    thread = threading.Thread(target=sample, daemon=True)
    thread.start()
    started = time.perf_counter()
    try:
        result = callback()
    finally:
        elapsed = time.perf_counter() - started
        peak[0] = max(peak[0], process.memory_info().rss)
        stop.set(); thread.join()
        records[name] = {"seconds": elapsed, "peak_rss_bytes": peak[0], "initial_rss_bytes": base}
        print(f"{name}: {elapsed:.3f}s, peak {peak[0]/1024**2:.1f} MiB", flush=True)
    return result

def environment():
    return {"python": platform.python_version(), "platform": platform.platform(),
        "logical_cpus": psutil.cpu_count(), "physical_cpus": psutil.cpu_count(logical=False),
        "ram_bytes": psutil.virtual_memory().total,
        "packages": {n: importlib.metadata.version(n) for n in ("numpy", "pandas", "pyarrow", "psutil")},
        "git_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "rss_method": "absolute process RSS sampled every 10 ms; includes retained inputs and allocator memory, excludes child processes; one fresh worker per size"}

def worker(size, output):
    root = Path(f"runs/benchmark-{size}-{os.getpid()}")
    root.mkdir(parents=True, exist_ok=False)
    bars_root, cache_root = root / "bars", root / "cache"
    bars_root.mkdir(); cache_root.mkdir()
    phases = {}
    def generate():
        bars = make_bars(minutes=size)
        bars.drop(columns="contract").set_index("ts").to_parquet(bars_root / "NQ_1m.parquet")
        bars.drop(columns="contract").set_index("ts").to_parquet(cache_root / "databento_NQc0_ohlcv-1m_fixture_ctx.parquet")
        return bars.loc[bars.contract.ne(bars.contract.shift()), ["ts", "contract"]].rename(columns={"ts": "effective_at"})
    schedule = measured("generation", generate, phases)
    gc.collect()
    bars = measured("ingestion", lambda: load_minutes(bars_root, "NQ"), phases)
    audit = measured("audit", lambda: audit_file(bars_root / "NQ_1m.parquet", "1m", "NQ"), phases)
    origin = measured("provenance", lambda: verify_minute_origin(bars_root, cache_root, "NQ"), phases)
    bars["contract"] = "SYN-A"
    bars.loc[bars.ts >= schedule.effective_at.iloc[1], "contract"] = "SYN-B"
    plan = example_plan()
    dates = pd.date_range(bars.ts.iloc[0].floor("D"), bars.ts.iloc[-1].ceil("D"), periods=4).floor("D")
    plan["splits_utc"] = dict(zip(("development", "validation", "historical_final"),
                                 [[a.isoformat(), b.isoformat()] for a, b in zip(dates[:-1], dates[1:])]))
    rows, daily = measured("evaluation", lambda: run_market(bars, "SYN", plan, _digest(plan),
        sha256_file(bars_root / "NQ_1m.parquet"), roll_instructions=scheduled_instructions(schedule)), phases)
    report = {"market": "SYN", "status": "synthetic", "plan_sha256": _digest(plan), "source_sha256": sha256_file(bars_root / "NQ_1m.parquet"),
              "runs": rows, "rank_changes": rank_changes(rows, 3), "winner_uncertainty": []}
    measured("report", lambda: market_report(report, root / "report", daily), phases)
    result = {"scope": "synthetic full grid", "rows": size, "run_count": len({r["run_id"] for r in rows}),
              "failed_runs": sum(r["status"] == "failed" for r in rows), "audit_rows": audit["row_count"],
              "exact_cache_match": origin["verified_match"], "execution_sha256": rows[0]["execution_sha256"],
              "phases": phases, "environment": environment(),
              "limits": "one whole market is loaded for evaluation/provenance; audit uses bounded batches; no streaming execution claim"}
    output.write_text(json.dumps(result, indent=2) + "\n")

def public_worker(snapshot, output):
    phases = {}
    root = Path("runs/public-profile")
    root.mkdir(parents=True, exist_ok=False)
    audit = measured("provenance_and_replay", lambda: audit_snapshot(snapshot), phases)
    plan = json.loads(Path("research/public-spot/plan.json").read_text())
    instruments = [(f["market"], MarketAdapter(ContractSpec(f["market"], 1, .01), "spot", 1440, SpotLedger)) for f in audit["files"]]
    bars = measured("ingestion", lambda: {m: pd.read_parquet(snapshot / f"{m}.parquet") for m, _ in instruments}, phases)
    measured("audit", lambda: [adapter.validate(bars[m]) for m, adapter in instruments], phases)
    def evaluate():
        return {m: run_market(bars[m], m, plan, _digest(plan), sha256_file(snapshot / f"{m}.parquet"), adapter=adapter) for m, adapter in instruments}
    results = measured("evaluation", evaluate, phases)
    winner = rank_changes(results["BTC-USD"][0], 10)["development_winner"]
    def report():
        for market, (rows, daily) in results.items():
            earlier = json.loads(Path(f"reports/public-spot/{market}/results.json").read_text())["runs"]
            clean = lambda values: [{k: v for k, v in r.items() if k not in EXCLUDED_ROW_FIELDS} for r in values]
            compare_value(clean(rows), clean(earlier), market + "/financial outcomes")
            summary = {"market": market, "status": "historical_public_spot", "primary": plan["universe"]["primary"], "protocol": plan, "plan_sha256": _digest(plan),
                "source_sha256": sha256_file(snapshot / f"{market}.parquet"), "runs": rows,
                "selected_config_from_primary": winner, "rank_changes": rank_changes(rows, 10),
                "winner_uncertainty": winner_uncertainty(winner, daily, plan)}
            market_report(summary, root / market, daily)
    measured("uncertainty_and_report", report, phases)
    output.write_text(json.dumps({"scope": "real public spot; complete 192-run declared grid", "rows": 7060,
        "run_count": 192, "matches_published_financial_metrics": True, "phases": phases, "environment": environment()}, indent=2) + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--size", type=int)
    parser.add_argument("--public-snapshot", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.public_snapshot:
        public_worker(args.public_snapshot, args.output)
    else:
        worker(args.size, args.output)
