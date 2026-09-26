"""Run every frozen configuration and preserve failures."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

from .data import load_minutes, sha256_file, source_path
from .ledger import Costs
from .metrics import daily_pnl, summarize
from .plan import verify
from .roll_gate import assess, require_ready, read_instructions
from .rolls import attach_contracts, read_schedule
from .signals import SignalSpec, decisions, grid_from_plan
from .specs import SPECS
from .timing import hourly_from_minutes, simulate
from .uncertainty import paired_block_bootstrap
from .walk_forward import evaluate as walk_forward


def _run_id(source_hash: str, config_id: str, scenario: dict, plan_hash: str) -> str:
    payload = json.dumps([source_hash, config_id, scenario, plan_hash], sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def _periods(plan: dict) -> dict[str, tuple[str | None, str | None]]:
    result = {"whole": (None, None)}
    result.update({name: tuple(bounds) for name, bounds in plan["splits_utc"].items()})
    return result


def run_market(minutes: pd.DataFrame, market: str, plan: dict, plan_hash: str,
               source_hash: str, *, roll_instructions=None) -> tuple[list[dict], dict[str, pd.Series]]:
    """Run one market at a time; keep base-scenario daily P&L for diagnostics."""
    hourly = hourly_from_minutes(minutes)
    grid = grid_from_plan(plan)
    capital = float(plan["execution"]["starting_capital_usd_per_market"])
    scenarios = plan["execution"]["scenarios"]
    results = []
    base_daily: dict[str, pd.Series] = {}
    candidates: list[tuple[str, SignalSpec | pd.DataFrame, str]] = [
        (item.id, item, item.config_hash) for item in grid]
    empty = pd.DataFrame({"known_at": pd.DatetimeIndex([], tz="UTC"), "target": pd.Series(dtype=int)})
    long = pd.DataFrame({"known_at": [pd.to_datetime(minutes["ts"].iloc[0], utc=True)], "target": [1]})
    candidates.extend([("flat", empty, "baseline-flat"),
                       ("always_long", long, "baseline-always-long")])
    for config_id, signal, config_hash in candidates:
        signal_error = None
        try:
            targets = decisions(hourly, signal) if isinstance(signal, SignalSpec) else signal
        except Exception as exc:
            signal_error = exc
        for scenario in scenarios:
            run_id = _run_id(source_hash, config_id, scenario, plan_hash)
            common = {"market": market, "config_id": config_id,
                      "config_hash": config_hash, "run_id": run_id,
                      "scenario": scenario["name"],
                      "commission_per_side": scenario["commission_usd_per_side"],
                      "slippage_ticks_per_side": scenario["slippage_ticks_per_side"],
                      "delay_minutes": scenario["delay_minutes"]}
            try:
                if signal_error is not None:
                    raise signal_error
                run = simulate(minutes, targets, SPECS[market],
                               Costs(scenario["commission_usd_per_side"],
                                     scenario["slippage_ticks_per_side"]),
                               delay_minutes=int(scenario["delay_minutes"]),
                               starting_capital=capital, roll_instructions=roll_instructions)
                for period, (start, end) in _periods(plan).items():
                    results.append({**common, "period": period,
                                    **summarize(run, start, end)})
                for year in sorted(run.curve["ts"].dt.year.unique()):
                    results.append({**common, "period": str(year),
                                    **summarize(run, f"{year}-01-01T00:00:00Z",
                                                f"{year+1}-01-01T00:00:00Z")})
                if scenario["name"] == "base":
                    base_daily[config_id] = daily_pnl(run)
            except Exception as exc:
                results.append({**common, "period": "whole", "status": "failed",
                                "error": f"{type(exc).__name__}: {exc}"})
    return results, base_daily


def rank_changes(results: list[dict], minimum_trades: int) -> dict:
    rank = {}
    for period in ("development", "validation", "historical_final"):
        rows = [row for row in results if row.get("period") == period and
                row.get("scenario") == "base" and row.get("status") == "ok" and
                row["config_id"] not in ("flat", "always_long") and
                row["entry_trades"] >= minimum_trades and row["sharpe"] is not None]
        rows.sort(key=lambda row: (-row["sharpe"], row["fills"], row["config_id"]))
        rank[period] = [row["config_id"] for row in rows]
    return {"ranks": rank, "development_winner": next(iter(rank["development"]), None)}


def winner_uncertainty(winner: str | None, daily: dict[str, pd.Series],
                       plan: dict) -> list[dict]:
    if winner is None:
        return []
    comparisons = []
    capital = float(plan["execution"]["starting_capital_usd_per_market"])
    for period in ("validation", "historical_final"):
        start, end = plan["splits_utc"][period]
        for baseline in ("flat", "always_long"):
            if winner not in daily or baseline not in daily:
                comparisons.append({"period": period, "baseline": baseline,
                                    "status": "missing_run"})
                continue
            comparisons.append({"period": period, "baseline": baseline,
                                **paired_block_bootstrap(daily[winner], daily[baseline],
                                                         start, end, capital)})
    return comparisons


def run_empirical(data_root: str | Path, mapping_root: str | Path,
                  audit_path: str | Path, provenance_path: str | Path,
                  plan_path: str | Path, lock_path: str | Path,
                  output: str | Path) -> dict:
    """The gate and plan lock are checked before loading bars for P&L."""
    read_json = lambda path: json.loads(Path(path).read_text(encoding="utf-8"))
    audit, origin, plan, lock = map(read_json,
                                    (audit_path, provenance_path, plan_path, lock_path))
    verify(plan, audit, lock)
    decision = assess(audit, origin, mapping_root, plan=plan)
    require_ready(decision)
    hashes = {row["market"]: row["sha256"] for row in audit["files"]
              if row["resolution"] == "1m"}
    for market in decision["included"]:
        if sha256_file(source_path(data_root, market)) != hashes[market]:
            raise ValueError(f"{market} source file changed since the frozen audit")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    (output / "universe.json").write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")
    reports = {}
    primary_winner = None
    primary = decision["primary"]
    for market in [primary] + [m for m in decision["included"] if m != primary]:
        minutes = attach_contracts(load_minutes(data_root, market),
                                   read_schedule(Path(mapping_root) / f"{market}_rolls.csv"))
        rows, daily = run_market(minutes, market, plan, lock["plan_sha256"], hashes[market],
                                 roll_instructions=read_instructions(Path(mapping_root) / f"{market}_instructions.csv"))
        ranking = rank_changes(rows, plan["selection"]["minimum_entry_trades"])
        if market == primary:
            primary_winner = ranking["development_winner"]
        report = {"market": market, "status": "historical_evaluation",
                  "plan_sha256": lock["plan_sha256"], "source_sha256": hashes[market],
                  "roll_gate": decision, "rank_changes": ranking,
                  "selected_config_from_NQ": primary_winner,
                  "winner_uncertainty": winner_uncertainty(primary_winner,
                                                            daily, plan),
                  "walk_forward": walk_forward(daily, rows,
                      plan["execution"]["starting_capital_usd_per_market"],
                      plan["selection"]["minimum_entry_trades"]), "runs": rows}
        (output / f"{market}_results.json").write_text(json.dumps(report, indent=2) + "\n",
                                                       encoding="utf-8")
        from .reporting import market_report
        market_report(report, output / market, daily)
        reports[market] = {"run_count": len({row["run_id"] for row in rows}),
                           "failed_runs": sum(row["status"] == "failed" for row in rows),
                           "development_winner": report["rank_changes"]["development_winner"]}
        del minutes, rows, daily
    return {"status": "historical_evaluation", "markets": reports,
            "note": "prior NQ exploration through 2026 means the final split is not pristine"}
