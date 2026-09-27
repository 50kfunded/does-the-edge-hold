"""Post-results arithmetic on saved, flat-to-flat one-contract paths."""
from __future__ import annotations
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from .plan import _digest

RATIOS = ("entries_per_window", "fills_per_window", "gross_per_round_trip_usd",
          "commission_per_round_trip_usd", "slippage_per_round_trip_usd",
          "tick_cost_per_round_trip_usd", "rounding_per_round_trip_usd",
          "total_cost_per_round_trip_usd", "net_per_round_trip_usd",
          "break_even_total_cost_per_round_trip_usd", "net_without_slippage_per_round_trip_usd")


def _number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _count(value):
    return _number(value) and value >= 0 and int(value) == value


def economics(row, spec, scenario):
    result = {k: row.get(k) for k in ("market", "config_id", "scenario", "period", "run_id", "execution_sha256")}
    result.update(source_status=row.get("status"), status="not_scored", reasons=[],
                  completed_round_trips=None, filled_sides=None, eligible_windows=None,
                  gross_sign=None, nonnegative_cost_can_produce_positive_net=None,
                  **dict.fromkeys(RATIOS))
    if row.get("status") != "ok":
        result["reasons"] = ["source result is not successfully scored"]
        return result
    problems = []
    counts = ("days", "entry_trades", "fills", "terminal_flat_windows")
    amounts = ("gross_pnl_usd", "commission_usd", "slippage_usd", "net_pnl_usd")
    if any(not _count(row.get(k)) for k in counts): problems.append("missing or invalid counts")
    if any(not _number(row.get(k)) for k in amounts): problems.append("missing or nonfinite accounting totals")
    if not spec or any(not _number(spec.get(k)) or spec[k] <= 0 for k in ("tick_size", "multiplier")):
        problems.append("missing or invalid recorded instrument specification")
    if not scenario or any(not _number(scenario.get(k)) or scenario[k] < 0 for k in ("commission_usd_per_side", "slippage_ticks_per_side")):
        problems.append("missing or invalid declared cost scenario")
    elif not _count(scenario.get("delay_minutes")):
        problems.append("missing or invalid declared delay")
    if problems:
        result.update(status="unsupported", reasons=problems)
        return result
    days, trips, sides = int(row["days"]), int(row["entry_trades"]), int(row["fills"])
    gross, fees, slip, net = [row[k] for k in amounts]
    tick_value = spec["tick_size"] * spec["multiplier"]
    expected_fees = sides * scenario["commission_usd_per_side"]
    tick_cost = sides * scenario["slippage_ticks_per_side"] * tick_value
    rounding = slip - tick_cost
    close = lambda a, b: math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-7)
    if days == 0: problems.append("no eligible windows")
    if row["terminal_flat_windows"] != days: problems.append("not every scored window ended flat")
    if sides != 2 * trips: problems.append("filled sides do not equal twice completed entries")
    if not close(gross - fees - slip, net): problems.append("gross minus costs does not reconcile to net")
    if fees < 0 or slip < 0: problems.append("negative recorded costs")
    if not close(fees, expected_fees): problems.append("commission does not match recorded sides and declared rate")
    if rounding < -1e-7: problems.append("recorded slippage is below declared tick costs")
    for row_key, plan_key in (("commission_per_side", "commission_usd_per_side"), ("slippage_ticks_per_side", "slippage_ticks_per_side"), ("delay_minutes", "delay_minutes")):
        if not _number(row.get(row_key)) or not close(row[row_key], scenario.get(plan_key, math.nan)):
            problems.append("recorded rates/delay differ from the scenario")
    if trips == 0 and any(not close(v, 0.) for v in (gross, fees, slip, net)):
        problems.append("zero-trade path has nonzero accounting totals")
    if problems:
        result.update(status="unsupported", reasons=problems)
        return result
    result.update(status="ok" if trips else "no_trades", eligible_windows=days,
                  completed_round_trips=trips, filled_sides=sides,
                  entries_per_window=trips / days, fills_per_window=sides / days,
                  totals_usd={"gross": gross, "commission": fees, "slippage": slip,
                              "declared_tick_cost": tick_cost, "rounding_residual": rounding,
                              "total_cost": fees + slip, "net": net},
                  tick_value_usd=tick_value,
                  declared_commission_usd_per_side=scenario["commission_usd_per_side"],
                  declared_slippage_ticks_per_side=scenario["slippage_ticks_per_side"],
                  delay_minutes=scenario["delay_minutes"],
                  accounting_residual_usd=net - (gross - fees - slip),
                  count_check="one-contract long/flat; all scored windows end flat; sides = 2 * entries",
                  gross_sign="positive" if gross > 0 else "negative" if gross < 0 else "zero",
                  nonnegative_cost_can_produce_positive_net=bool(trips and gross > 0))
    if trips:
        for key, value in (("gross", gross), ("commission", fees), ("slippage", slip),
                           ("tick_cost", tick_cost), ("rounding", rounding),
                           ("total_cost", fees + slip), ("net", net)):
            result[key + "_per_round_trip_usd"] = value / trips
        result["break_even_total_cost_per_round_trip_usd"] = gross / trips
        result["net_without_slippage_per_round_trip_usd"] = (gross - fees) / trips
    else:
        result["reasons"] = ["flat path has no completed trades; per-trade ratios are undefined"]
    return result


def fixed_path_net(gross, trips, cost_per_round_trip):
    if not _number(gross) or not _count(trips) or not _number(cost_per_round_trip) or cost_per_round_trip < 0:
        raise ValueError("finite gross, nonnegative integer trades and nonnegative cost required")
    if trips == 0:
        if gross != 0: raise ValueError("a zero-trade flat path cannot have nonzero gross")
        return {"total_net_usd": 0., "net_per_round_trip_usd": None}
    return {"total_net_usd": gross - trips * cost_per_round_trip,
            "net_per_round_trip_usd": gross / trips - cost_per_round_trip}


def _hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_diagnostics(output, summary, reports):
    output = Path(output)
    plan = summary["protocol"]
    if _digest(plan) != summary["plan_sha256"]: raise ValueError("saved protocol hash mismatch")
    scenarios = {s["name"]: s for s in plan["execution"]["scenarios"]}
    artifact = {"schema_version": 1, "kind": "post_results_trade_economics", "study_status": summary["status"],
                "analysis_status": "post-results descriptive arithmetic; no new strategy run or independent statistical test",
                "protocol_sha256": summary["plan_sha256"], "protocol_source": "summary.json#/protocol",
                "primary_pick": summary["markets"][summary["primary"]]["primary_pick"],
                "reporting_code_sha256": {name: hashlib.sha256((Path(__file__).parent / name).read_text(encoding="utf-8-sig").encode()).hexdigest()
                                           for name in ("trade_economics.py", "intraday_reporting.py")},
                "definitions": {"round_trips": "entries only when every window is flat and filled sides equal 2 * entries",
                    "frequency": "entries or filled sides / eligible windows; not portfolio notional turnover",
                    "ratios": "aggregate period totals / actual completed trades, never an unweighted average of yearly ratios",
                    "rounding": "recorded slippage minus filled sides * adverse ticks * recorded tick value; aggregate residual under the fill model",
                    "cost_curve": "G - R*C; nonnegative total dollar cost per completed trip; same assumed path; no changes to fills, delay, spread, queueing or impact",
                    "positive_budget": "G/R > 0 allows positive net only for C < G/R; it is not an estimated executable cost",
                    "nonpositive_budget": "G/R <= 0 admits no nonnegative cost producing positive net; a negative budget is not an achievable remedy",
                    "delay": "different delays are separate saved paths; a cost-only curve does not predict their effect"},
                "sources": {}, "rows": []}
    for market, report in reports.items():
        folder = output / market
        manifest = json.loads((folder / "execution.json").read_text())
        if manifest["identity"]["protocol_sha256"] != summary["plan_sha256"]:
            raise ValueError("saved execution uses another protocol")
        spec = manifest["identity"]["evidence"].get("instrument")
        artifact["sources"][market] = {"results": market + "/results.json", "results_sha256": _hash(folder / "results.json"),
            "all_results_csv_sha256": _hash(folder / "all-results.csv"), "execution": market + "/execution.json",
            "execution_artifact_sha256": _hash(folder / "execution.json"), "evaluation_execution_sha256": manifest["execution_sha256"],
            "instrument": spec}
        for source_name, sample in (("runs", "own_complete_dates"), ("common_runs", "common_complete_dates")):
            for i, row in enumerate(report.get(source_name, [])):
                item = economics(row, spec, scenarios.get(row.get("scenario")))
                if row.get("execution_sha256") != manifest["execution_sha256"]:
                    item.update(status="unsupported", reasons=["row execution identity differs from saved manifest"])
                    item.update(dict.fromkeys(RATIOS))
                item.update(sample=sample, source_result=market + "/results.json#" + source_name + "/" + str(i))
                artifact["rows"].append(item)
    artifact["status_counts"] = dict(Counter(r["status"] for r in artifact["rows"]))
    (output / "trade-economics.json").write_text(json.dumps(artifact, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return artifact
