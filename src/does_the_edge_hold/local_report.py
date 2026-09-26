"""Regenerate the local study status, including a blocked roll decision."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .audit import audit_sources, public_summary, write_audit
from .data import iter_parquet, source_path
from .experiments import run_empirical
from .plan import verify
from .provenance import verify_minute_origin
from .roll_gate import assess
from .daily_clock import DailyClock


def count_splits(path: Path, splits: dict, clock=None) -> dict[str, int]:
    counts = {name: 0 for name in splits}
    boundaries = {name: (pd.to_datetime(start, utc=True), pd.to_datetime(end, utc=True))
                  for name, (start, end) in splits.items()}
    for batch in iter_parquet(path):
        labels = clock.labels(batch["ts"]) if clock is not None else batch["ts"]
        for name, (start, end) in boundaries.items():
            counts[name] += int(((labels >= start) & (labels < end)).sum())
    return counts


def run_local_report(data_root: Path, cache_root: Path, output: Path,
                     plan_path: Path, lock_path: Path,
                     mapping_root: Path | None = None) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    from .plan import validate
    from .roll_gate import universe
    validate(plan)
    # Legacy locks also seal sources outside the active P&L universe.
    locked = lock["source_hashes"]
    markets = [key.removesuffix("_1m") for key in locked if key.endswith("_1m")]
    roles = universe(plan)
    active = list(dict.fromkeys(roles["required"] + roles["optional"]))
    audit = audit_sources(data_root, markets=markets, include_seconds="NQ_1s" in locked)
    audit_path, origin_path = output / "audit-detailed.json", output / "provenance.json"
    write_audit(audit, audit_path)
    write_audit(public_summary(audit), output / "audit-public.json")
    origin = {"markets": [verify_minute_origin(data_root, cache_root, market)
                          for market in active if market in markets]}
    origin_path.write_text(json.dumps(origin, indent=2) + "\n", encoding="utf-8")
    verify(plan, audit, lock)
    gate = assess(audit, origin, mapping_root, plan=plan)
    (output / "roll-gate.json").write_text(json.dumps(gate, indent=2) + "\n", encoding="utf-8")
    status = {"status": "blocked" if gate["status"] != "ready" else "historical_evaluation",
              "plan_sha256": lock["plan_sha256"], "roll_gate": gate,
              "empirical_pnl_calculated": gate["status"] == "ready"}
    status["split_counts"] = {market: count_splits(source_path(data_root, market), plan["splits_utc"], DailyClock.from_plan(plan))
                              for market in markets}
    lines = ["# local study", "", f"i checked {len(audit['files'])} locked files and compared {len(origin['markets'])} declared minute exports with their source cache. the primary is {roles['primary']}.", ""]
    if gate["status"] != "ready":
        lines += ["**the roll gate is unresolved, so i haven't run the empirical P&L grid.** it needs verified contract mapping and causal execution timing. the public example uses synthetic contracts and stays separate.", ""]
        lines += ["each included market also needs independently supported advance roll instructions. a historical switch date alone isn't enough, including for calendar rolls.", ""]
    else:
        status["results"] = run_empirical(data_root, mapping_root, audit_path, origin_path,
                                          plan_path, lock_path, output / "empirical")
        lines += [f"the roll gate passed. i kept the {roles['primary']} development pick for the other markets; their reports are in `empirical/`.", ""]
    lines += ["| file | rows | first UTC bar | last UTC bar |", "| --- | ---: | --- | --- |"]
    for source in audit["files"]:
        lines.append(f"| {source['market']} {source['resolution']} | {source['row_count']:,} | {source['first_utc']} | {source['last_utc']} |")
    lines += ["", "## minute rows in each part", "",
              "| market | development | validation | historical final |", "| --- | ---: | ---: | ---: |"]
    for source in audit["files"]:
        if source["resolution"] != "1m":
            continue
        counts = [status["split_counts"][source["market"]][name]
                  for name in ("development", "validation", "historical_final")]
        lines.append(f"| {source['market']} | {' | '.join(f'{value:,}' for value in counts)} |")
    lines += ["", f"included: {gate['included']}. excluded: {gate['excluded']}. source rules are in the provenance receipt. second bars, if locked, aren't used for fill claims.", "",
              "i'd already seen results through 2026 in an older project. the final period is a historical check, not an untouched holdout. detailed bar samples stay in the local run folder; the public audit contains aggregate metadata.", ""]
    (output / "report.md").write_text("\n".join(lines), encoding="utf-8")
    (output / "status.json").write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
    return status
