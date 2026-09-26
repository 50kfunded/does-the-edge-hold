"""Coverage and historical source-rule gate, without strategy performance."""
import json
import time
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from .data import load_minutes, source_path, sha256_file
from .semantic import semantic_digest
from .provenance import verify_minute_origin
from .intraday_plan import validate, candidate_dates, read
from .plan import _digest

SOURCE_DOCS = {
    "schema": 1, "reviewed_utc_date": "2026-09-27",
    "symbology_url": "https://databento.com/docs/standards-and-conventions/symbology",
    "historical_url": "https://databento.com/docs/api-reference-historical/symbology/symbology-resolve",
    "basis": "Historical continuous symbols select an unadjusted tradable instrument for a date. Historical resolver validity uses inclusive/exclusive UTC dates. Calendar rank zero selects the front expiry. These support within-UTC-date continuity as an inference; they do not recover the actual instrument ID.",
    "decision": "allow conditional within-date accounting for exact-matched calendar NQ/ES/YM; no cross-date holdings or return marks",
    "excluded_volume_rule": "GC/CL descriptive only; this protocol does not establish operational as-of availability of their volume mapping",
    "limitations": "local files and filename/source-code chain are not authenticated vendor delivery; no contract names, quotes, tick-time fills or signed mappings supplied",
    "historical_semantics_reviewed": True,
}

def coverage(bars, plan, market, source_rule):
    dates = candidate_dates(plan)
    ts = bars.ts
    selected = bars.loc[(ts.dt.dayofweek < 5) & (ts.dt.hour >= 8) & (ts.dt.hour < 12)]
    groups = {date: part for date, part in selected.groupby(selected.ts.dt.floor("D"), sort=False)}
    rows = []
    for date in dates:
        part = groups.get(date)
        observed = pd.DatetimeIndex([] if part is None else part.ts, tz="UTC")
        expected = pd.date_range(date + pd.Timedelta(hours=8), periods=240, freq="min")
        complete = observed.equals(expected)
        row = {"market": market, "date": date.date().isoformat(), "observed_minutes": len(observed), "eligible": complete,
               "reason": "complete" if complete else "empty_candidate" if not len(observed) else "missing_minutes",
               "missing_warmup_minutes": len(expected[:60].difference(observed)),
               "missing_window_minutes": len(expected.difference(observed)),
               "terminal_1m_observed": date + pd.Timedelta(hours=11, minutes=51) in observed,
               "terminal_5m_observed": date + pd.Timedelta(hours=11, minutes=55) in observed,
               "source_segment_id": f"{source_rule}|{date.date()}", "contract_identity": "unknown"}
        rows.append(row)
    table = pd.DataFrame(rows)
    return table

def assess_source_day(sources, origins, plan, docs):
    allowed = plan["universe"]["required"] + plan["universe"]["optional"]
    by_market = {s["market"]: s for s in sources}
    origin_by = {s["market"]: s for s in origins}
    included, excluded = [], {}
    for market in allowed:
        source, origin = by_market.get(market), origin_by.get(market, {})
        reasons = []
        if not source or not source["quality_ready"]: reasons.append("source quality or precision evidence missing")
        if not origin.get("verified_match") or origin.get("comparison") != "exact values and dtypes; no precision cast": reasons.append("original-precision cache match missing")
        if origin.get("selected_root") != market + "c0": reasons.append("calendar rank-zero source not established")
        if not docs.get("historical_semantics_reviewed"): reasons.append("within-UTC-date source rule insufficient")
        if reasons: excluded[market] = reasons
        else: included.append(market)
    excluded.update({m: ["descriptive only; volume mapping as-of availability not established in this protocol"] for m in plan["descriptive_markets"]})
    return {"status": "conditional_source_day_ready" if "NQ" in included else "blocked", "primary_ready": "NQ" in included,
            "included": included, "excluded": excluded, "contract_identity": "unknown", "basis": "historical source-rule inference within UTC date only",
            "original_roll_aware_study": "blocked independently; this decision cannot authorize it"}

def run_audit(data_root, cache_root, plan_path, output, *, docs=None, local_code_paths=()):
    started = time.perf_counter()
    plan = read(plan_path); validate(plan)
    output = Path(output); output.mkdir(parents=True, exist_ok=False)
    sources, origins, tables = [], [], []
    for market in plan["audit_markets"]:
        print(f"checking original-precision {market} windows", flush=True)
        path = source_path(data_root, market)
        bars = load_minutes(data_root, market)
        identity = semantic_digest([bars])
        precise = all(str(bars[c].dtype) == "float64" for c in ("open", "high", "low", "close")) and str(bars.volume.dtype) == "int64"
        aligned = bool((bars.ts.astype("int64") % 60_000_000_000 == 0).all())
        volume_ok = bool((bars.volume > 0).all())
        source = {"market": market, "artifact_sha256": sha256_file(path), "semantic": identity, "rows": len(bars),
                  "schema": {f.name: str(f.type) for f in pq.ParquetFile(path).schema_arrow},
                  "first_utc": bars.ts.iloc[0].isoformat(), "last_utc": bars.ts.iloc[-1].isoformat(),
                  "quality_ready": precise and aligned and volume_ok,
                  "quality": {"original_float64_int64": precise, "minute_aligned": aligned, "positive_volume": volume_ok,
                              "semantic_checks": "finite OHLCV, valid OHLC, unique ordered UTC timestamps"}}
        origin = verify_minute_origin(data_root, cache_root, market, original_precision=True)
        rule = market + "." + origin.get("selected_root", "unknown")[-2:-1] + ".0"
        table = coverage(bars, plan, market, rule)
        table.to_csv(output / f"{market}-coverage.csv", index=False)
        tables.append(table); sources.append(source); origins.append(origin)
        del bars
    docs = docs or SOURCE_DOCS
    readiness = assess_source_day(sources, origins, plan, docs)
    masks, splits = {}, {}
    for table in tables:
        market = table.market.iloc[0]
        masks[market] = _digest(table[["date", "eligible"]].to_dict("records"))
        splits[market] = {}
        for name, (start, end) in plan["splits_utc"].items():
            part = table.loc[(table.date >= start[:10]) & (table.date < end[:10])]
            splits[market][name] = {"candidate_weekdays": len(part), "complete": int(part.eligible.sum()),
                                    "partial": int(((part.observed_minutes > 0) & ~part.eligible).sum()), "empty": int((part.observed_minutes == 0).sum())}
    audit = {"schema": 1, "plan_sha256": _digest(plan), "sources": sources, "origins": origins,
             "source_docs": docs, "readiness": readiness, "splits": splits, "mask_hashes": masks,
             "coverage_table_hashes": {t.market.iloc[0]: sha256_file(output / f"{t.market.iloc[0]}-coverage.csv") for t in tables},
             "local_source_code": [{"name": Path(p).name, "sha256": sha256_file(p)} for p in local_code_paths],
             "eligibility": plan["eligibility"], "runtime_seconds": time.perf_counter() - started}
    (output / "audit.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    return audit
