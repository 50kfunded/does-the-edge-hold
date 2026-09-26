"""Locked source-day evaluation, matched samples and measured real workload."""
from __future__ import annotations
import json
import math
from pathlib import Path
import threading
import time
import numpy as np
import pandas as pd
import psutil
from .data import iter_parquet, source_path, sha256_file
from .semantic import semantic_file
from .intraday_plan import read, validate
from .intraday_audit import coverage
from .intraday import prepare_window, window_decisions, simulate_window, compile_targets, WindowLedger
from .signals import grid_from_plan
from .specs import SPECS
from .ledger import Costs
from .execution import seal, write_manifest
from .plan import _digest
from .experiments import _run_id, rank_changes, winner_uncertainty

def summarize_windows(frame, capital, *, periods_per_year=252):
    if frame.empty: return {"status": "no_windows", "days": 0}
    failed = frame.status.ne("ok")
    if failed.any(): return {"status": "failed", "failed_windows": int(failed.sum()), "days": len(frame), "error": "unresolved windows; no complete-case score"}
    daily = frame.net_pnl_usd.astype(float)
    sd = float(daily.std(ddof=1)) if len(daily) > 1 else 0.
    net, gross = float(daily.sum()), float(frame.gross_pnl_usd.sum())
    fees, slip = float(frame.commission_usd.sum()), float(frame.slippage_usd.sum())
    path = capital + np.r_[0., daily.cumsum()]
    peak = np.maximum.accumulate(path)
    return {"status": "ok", "days": len(frame), "gross_pnl_usd": gross, "net_pnl_usd": net,
            "commission_usd": fees, "slippage_usd": slip, "entry_trades": int(frame.entry_trades.sum()), "fills": int(frame.fills.sum()),
            "account_return": net / capital, "mean_session_pnl_usd": float(daily.mean()),
            "annual_mean_return": float(daily.mean() / capital * periods_per_year),
            "volatility": sd / capital * math.sqrt(periods_per_year),
            "sharpe": float(daily.mean() / sd * math.sqrt(periods_per_year)) if sd > 0 else None,
            "max_drawdown": float(((path - peak) / peak).min()),
            "drawdown_scope": "conditional complete-window sum on stated capital, not live equity or intraday drawdown",
            "exposure": float(frame.exposure_minutes.sum() / (len(frame) * 240)),
            "mean_entry_notional_usd": float(frame.loc[frame.entry_trades > 0, "notional_entry_mean_usd"].mean()) if frame.entry_trades.sum() else 0.,
            "notional_note": "mean across entered windows; not equal-risk sizing or margin availability",
            "terminal_flat_windows": int(frame.terminal_flat.sum()), "periods_per_year": periods_per_year,
            "maximum_window_reconciliation_error_usd": float(frame.reconciliation_error_usd.abs().max()),
            "reconciliation_error_usd": net - (gross - fees - slip)}

def verify_inputs(data_root, cache_root, plan, lock, audit_root):
    validate(plan)
    audit = read(Path(audit_root) / "audit.json")
    if _digest(plan) != lock["plan_sha256"] or _digest(audit) != lock["audit_sha256"]:
        raise ValueError("source-day plan or evidence changed after freeze")
    if not lock["readiness"]["primary_ready"] or audit["readiness"] != lock["readiness"]:
        raise ValueError("source-day evidence is blocked")
    for source in audit["sources"]:
        market = source["market"]
        print(f"verifying frozen observations: {market}", flush=True)
        if semantic_file(source_path(data_root, market))["sha256"] != lock["source_hashes"][market]:
            raise ValueError(f"{market} observations changed after freeze")
        table_path = Path(audit_root) / f"{market}-coverage.csv"
        if sha256_file(table_path) != audit["coverage_table_hashes"][market]: raise ValueError("coverage receipt changed")
        table = pd.read_csv(table_path)
        if _digest(table[["date", "eligible"]].to_dict("records")) != lock["masks"][market]: raise ValueError("eligibility mask changed")
    for origin in audit["origins"]:
        for source in origin["source_files"]:
            if sha256_file(Path(cache_root) / source["name"]) != source["sha256"]: raise ValueError("source cache evidence changed")
    for market in lock["readiness"]["included"]:
        if SPECS[market].__dict__ != lock["instrument_specs"][market]: raise ValueError("instrument specification changed")
    return audit

def load_window_minutes(data_root, market, table):
    dates = pd.to_datetime(table.loc[table.eligible, "date"], utc=True)
    parts = []
    for batch in iter_parquet(source_path(data_root, market)):
        ts = batch.ts
        keep = ts.dt.floor("D").isin(dates) & (ts.dt.hour >= 8) & (ts.dt.hour < 12)
        if keep.any(): parts.append(batch.loc[keep])
    if not parts: raise ValueError("no complete windows")
    return pd.concat(parts, ignore_index=True)

def period_rows(frame, plan, common):
    capital = plan["execution"]["starting_capital_usd_per_market"]
    parts = {"whole": (None, None), **plan["splits_utc"]}
    rows = []
    for period, (start, end) in parts.items():
        selected = frame if start is None else frame.loc[(frame.date >= start[:10]) & (frame.date < end[:10])]
        rows.append({**common, "period": period, **summarize_windows(selected, capital)})
    for year in sorted(frame.date.str[:4].unique()):
        rows.append({**common, "period": year, **summarize_windows(frame.loc[frame.date.str.startswith(year)], capital)})
    return rows

def run_study(data_root, cache_root, plan_path, lock_path, audit_root, output, *, synthetic=False):
    started = time.perf_counter()
    peak = [psutil.Process().memory_info().rss]
    stop = threading.Event()
    def sample():
        while not stop.wait(.05): peak[0] = max(peak[0], psutil.Process().memory_info().rss)
    sampler = threading.Thread(target=sample, daemon=True); sampler.start()
    try:
        return _run(data_root, cache_root, plan_path, lock_path, audit_root, output, synthetic, started, peak)
    finally:
        stop.set(); sampler.join()

def _run(data_root, cache_root, plan_path, lock_path, audit_root, output, synthetic, started, peak):
    plan, lock = read(plan_path), read(lock_path)
    verification_start = time.perf_counter()
    audit = verify_inputs(data_root, cache_root, plan, lock, audit_root)
    verification_seconds = time.perf_counter() - verification_start
    output = Path(output); output.mkdir(parents=True, exist_ok=False)
    tables = {m: pd.read_csv(Path(audit_root) / f"{m}-coverage.csv") for m in lock["readiness"]["included"]}
    shared = set.intersection(*[set(t.loc[t.eligible, "date"]) for t in tables.values()])
    summary = {"schema_version": 1, "status": "synthetic_source_day" if synthetic else "conditional_historical_source_day",
               "plan_sha256": lock["plan_sha256"], "primary": "NQ", "protocol": plan, "readiness": lock["readiness"],
               "eligibility": plan["eligibility"], "common_dates": len(shared),
               "common_dates_sha256": _digest(sorted(shared)), "markets": {}}
    grid = grid_from_plan(plan)
    winner = None; phases = {}; all_daily = {}
    for market in lock["readiness"]["included"]:
        folder = output / market; folder.mkdir()
        phase = {}; phase_start = time.perf_counter()
        minutes = load_window_minutes(data_root, market, tables[market])
        rule = market + ".c.0"
        actual = coverage(minutes, plan, market, rule)
        if _digest(actual[["date", "eligible"]].to_dict("records")) != lock["masks"][market]: raise ValueError("actual complete-window mask differs from lock")
        windows = []
        for date, frame in minutes.groupby(minutes.ts.dt.floor("D"), sort=False):
            windows.append(prepare_window(frame, f"{rule}|{date.date()}"))
        phase["source_window_loading_seconds"] = time.perf_counter() - phase_start
        phase["window_rows"] = len(minutes); phase["complete_windows"] = len(windows)
        del minutes
        phase_start = time.perf_counter()
        cache = {}
        for signal in grid:
            cache[signal.id] = [compile_targets(w, window_decisions(w, signal)) for w in windows]
        for baseline in plan["baseline_ids"]:
            cache[baseline] = [compile_targets(w, pd.DataFrame({"known_at": [w.date + pd.Timedelta(hours=9)],
                "target": [1]})) if baseline == "intraday_long" else compile_targets(w, pd.DataFrame({"known_at": pd.DatetimeIndex([], tz="UTC"), "target": pd.Series(dtype=int)})) for w in windows]
        phase["feature_cache_seconds"] = time.perf_counter() - phase_start
        manifest = seal(lock["plan_sha256"], {market: lock["source_hashes"][market]},
            evidence={"source_day_audit": lock["audit_sha256"], "mask": lock["masks"][market], "source_rule": rule,
                      "contract_identity": "unknown", "instrument": SPECS[market].__dict__, "keep_events": False,
                      "causal_check": "built-in date-local features plus prefix and future-perturbation regressions"},
            callables={"prepare": prepare_window, "features": window_decisions, "compile": compile_targets,
                       "execute": simulate_window, "summarize": summarize_windows,
                       "ledger_fill": WindowLedger._fill, "ledger_buy": WindowLedger.buy,
                       "ledger_sell": WindowLedger.sell, "ledger_mark": WindowLedger.mark})
        manifest["artifact_sha256"] = sha256_file(source_path(data_root, market))
        write_manifest(manifest, folder / "execution.json")
        phase_start = time.perf_counter()
        rows, common_rows, panel = [], [], {}
        failures = []
        for config_id, targets in cache.items():
            for scenario in plan["execution"]["scenarios"]:
                case = {"market": market, "config_id": config_id, "scenario": scenario["name"], "execution_sha256": manifest["execution_sha256"],
                        "run_id": _run_id(lock["source_hashes"][market], config_id, scenario, lock["plan_sha256"], manifest["execution_sha256"]),
                        "commission_per_side": scenario["commission_usd_per_side"], "slippage_ticks_per_side": scenario["slippage_ticks_per_side"],
                        "fee_bps": 0., "slippage_bps": 0., "delay_minutes": scenario["delay_minutes"], "mask_sha256": lock["masks"][market]}
                records = []
                for window, signal in zip(windows, targets):
                    result = simulate_window(window, signal, SPECS[market], Costs(scenario["commission_usd_per_side"], scenario["slippage_ticks_per_side"]),
                        scenario["delay_minutes"], starting_capital=plan["execution"]["starting_capital_usd_per_market"], keep_events=False)
                    record = {k: v for k, v in result.items() if k not in ("ledger", "events", "pending")}
                    record.update(date=str(window.date.date()), source_segment_id=window.source_segment_id, contract_identity="unknown")
                    records.append(record)
                    if result["status"] != "ok": failures.append({**case, **record})
                frame = pd.DataFrame(records)
                rows += period_rows(frame, plan, case)
                common_rows += period_rows(frame.loc[frame.date.isin(shared)], plan, {**case, "sample": "common complete dates"})
                series = pd.Series(frame.get("net_pnl_usd", pd.Series(np.nan, index=frame.index)).to_numpy(), index=pd.to_datetime(frame.date, utc=True))
                panel[config_id + "|" + scenario["name"]] = series
                print(f"{market}: {config_id} / {scenario['name']} complete", flush=True)
        phase["evaluation_seconds"] = time.perf_counter() - phase_start
        daily = {k.split("|")[0]: v for k, v in panel.items() if k.endswith("|base")}
        rankings = rank_changes(rows, plan["selection"]["minimum_entry_trades"], baselines=plan["baseline_ids"], tie_field="entry_trades")
        if market == "NQ": winner = rankings["development_winner"]
        uncertainty_start = time.perf_counter()
        uncertainty = winner_uncertainty(winner, daily, plan)
        phase["uncertainty_seconds"] = time.perf_counter() - uncertainty_start
        report = {**summary, "market": market, "source_sha256": lock["source_hashes"][market], "execution_sha256": manifest["execution_sha256"],
                  "baseline_ids": plan["baseline_ids"], "selected_config_from_primary": winner, "rank_changes": rankings,
                  "winner_uncertainty": uncertainty, "runs": rows, "common_runs": common_rows, "failed_windows": failures,
                  "coverage": audit["splits"][market]}
        (folder / "results.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        pd.DataFrame(rows).to_csv(folder / "all-results.csv", index=False)
        pd.DataFrame(common_rows).to_csv(folder / "common-results.csv", index=False)
        pd.DataFrame(panel).to_csv(folder / "daily-pnl-all-scenarios.csv", index_label="utc_date")
        all_daily[market] = daily
        summary["markets"][market] = {"cases": len(cache) * len(plan["execution"]["scenarios"]), "failed_windows": len(failures),
            "own_complete_dates": len(windows), "primary_pick": winner, "own_development_winner": rankings["development_winner"], "execution_sha256": manifest["execution_sha256"]}
        phases[market] = phase
        del windows, cache, panel
    from .uncertainty import paired_block_bootstrap
    paired = []
    if winner is not None:
        for market, daily in all_daily.items():
            mask = daily[winner].index.strftime("%Y-%m-%d").isin(shared)
            for part in ("validation", "historical_final"):
                start, end = plan["splits_utc"][part]
                for baseline in plan["baseline_ids"]:
                    for length in plan["statistics"]["block_lengths"]:
                        paired.append({"market": market, "period": part, "baseline": baseline,
                            **paired_block_bootstrap(daily[winner].loc[mask], daily[baseline].loc[mask], start, end, 100000,
                                block_days=length, replicates=plan["statistics"]["replicates"], seed=plan["statistics"]["seed"], periods_per_year=252,
                                minimum_days=plan["statistics"]["minimum_paired_observations"])})
    summary["common_date_uncertainty"] = paired
    summary["runtime"] = {"total_seconds": time.perf_counter() - started, "verification_seconds": verification_seconds, "markets": phases,
                          "sampled_peak_rss_mib": peak[0] / 1024**2, "sampling_seconds": .05,
                          "audited_source_rows": sum(r["rows"] for r in audit["sources"]),
                          "evaluated_source_rows": sum(r["rows"] for r in audit["sources"] if r["market"] in tables),
                          "evaluated_window_rows": sum(p["window_rows"] for p in phases.values()), "cases": sum(v["cases"] for v in summary["markets"].values()),
                          "feature_policy": "each setting computed once per source-day; reused by all five scenarios", "scale_limit": "single-machine measured workload, not streaming execution"}
    (output / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    from .intraday_reporting import render
    render(output)
    return summary
