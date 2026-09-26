"""A complete public run that needs no account or licensed files."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import time

import numpy as np

from .data import sha256_file
from .experiments import rank_changes, run_market, winner_uncertainty
from .ledger import Costs, Ledger
from .plan import _digest
from .reporting import market_report
from .specs import SPECS
from .synthetic import make_bars


def example_plan() -> dict:
    return {"scope": "synthetic only", "configuration_count": 9,
            "signal_families": {"momentum": {"lookback_hours": [12, 24, 72]},
                                "mean_reversion": {"lookback_hours": [24, 72], "entry_z": [.5, 1, 1.5]}},
            "splits_utc": {"development": ["2024-01-08T00:00:00Z", "2024-01-18T00:00:00Z"],
                           "validation": ["2024-01-18T00:00:00Z", "2024-01-28T00:00:00Z"],
                           "historical_final": ["2024-01-28T00:00:00Z", "2024-02-07T00:00:00Z"]},
            "selection": {"minimum_entry_trades": 3},
            "execution": {"starting_capital_usd_per_market": 100_000,
                          "scenarios": [
                              {"name": "gross_reference", "commission_usd_per_side": 0, "slippage_ticks_per_side": 0, "delay_minutes": 1},
                              {"name": "base", "commission_usd_per_side": 2.5, "slippage_ticks_per_side": 1, "delay_minutes": 1},
                              {"name": "higher_cost", "commission_usd_per_side": 5, "slippage_ticks_per_side": 2, "delay_minutes": 1},
                              {"name": "one_bar_late", "commission_usd_per_side": 2.5, "slippage_ticks_per_side": 1, "delay_minutes": 60},
                              {"name": "combined_stress", "commission_usd_per_side": 5, "slippage_ticks_per_side": 2, "delay_minutes": 60}]} }


def controlled_demos() -> dict:
    rng = np.random.default_rng(1729)
    noise = rng.normal(0, 1, size=(100, 40, 504))
    scores = noise[:, :, :252].mean(axis=2) / noise[:, :, :252].std(axis=2, ddof=1) * np.sqrt(252)
    winners = np.argmax(scores, axis=1)
    later = noise[np.arange(100), winners, 252:]
    later_scores = later.mean(axis=1) / later.std(axis=1, ddof=1) * np.sqrt(252)
    selected_scores = scores[np.arange(100), winners]
    ledger = Ledger(SPECS["SYN"], Costs(2.5, 1))
    stamp = datetime(2024, 1, 1, tzinfo=timezone.utc)
    ledger.buy(stamp, "SYN-A", 100)
    ledger.sell(stamp, "SYN-A", 100.25)
    return {"noise_selection": {"seed": 1729, "candidates_per_trial": 40, "trials": 100, "days_per_part": 252,
                                 "development_sharpe": float(np.median(selected_scores)),
                                 "median_development_sharpe": float(np.median(scores)),
                                 "later_sharpe": float(np.median(later_scores)),
                                 "selected_development_scores": selected_scores.tolist(),
                                 "selected_later_scores": later_scores.tolist(),
                                 "note": "independent zero-mean noise, not simulated futures strategies"},
            "costs": {"gross_pnl_usd": ledger.gross_pnl, "net_pnl_usd": ledger.net_pnl,
                      "commission_usd": ledger.commission_paid, "slippage_usd": ledger.slippage_paid}}


def run_example(output: str | Path) -> dict:
    started = time.perf_counter()
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    plan = example_plan()
    (output / "example-plan.json").write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    bars = make_bars(minutes=43_200)
    from .timing import scheduled_instructions
    schedule = bars.loc[bars.contract.ne(bars.contract.shift()), ["ts", "contract"]].rename(columns={"ts": "effective_at"})
    instructions = scheduled_instructions(schedule)
    path = output / "synthetic_bars.parquet"
    bars.to_parquet(path, index=False)
    source_hash, plan_hash = sha256_file(path), _digest(plan)
    rows, daily = run_market(bars, "SYN", plan, plan_hash, source_hash, roll_instructions=instructions)
    ranking = rank_changes(rows, plan["selection"]["minimum_entry_trades"])
    report = {"market": "SYN", "status": "synthetic", "plan_sha256": plan_hash,
              "source_sha256": source_hash, "seed": 7, "minute_rows": len(bars),
              "rank_changes": ranking, "runs": rows,
              "winner_uncertainty": winner_uncertainty(ranking["development_winner"], daily, plan),
              "controlled_demos": controlled_demos()}
    (output / "results.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    market_report(report, output, daily)
    demo = report["controlled_demos"]
    noise, cost = demo["noise_selection"], demo["costs"]
    with (output / "report.md").open("a", encoding="utf-8") as handle:
        handle.write(f"\n## two smaller checks\n\ni repeated a noise experiment 100 times, with 40 candidates in each run and no expected edge. the median selected development Sharpe was {noise['development_sharpe']:.2f}; the same picks scored {noise['later_sharpe']:.2f} on later noise. the median across all development candidates was {noise['median_development_sharpe']:.2f}. the JSON keeps every selected score.\n\ni also bought at 100 and sold at 100.25 with a $20 multiplier. that made ${cost['gross_pnl_usd']:.2f} gross, but lost ${abs(cost['net_pnl_usd']):.2f} after both sides' costs.\n")
    (output / "runtime.json").write_text(json.dumps({"seconds": time.perf_counter() - started}, indent=2) + "\n", encoding="utf-8")
    return report
