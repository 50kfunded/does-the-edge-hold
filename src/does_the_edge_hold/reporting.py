"""Small tables and figures for an audit run."""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def market_report(report: dict, output: Path, daily: dict[str, pd.Series] | None = None) -> None:
    output.mkdir(parents=True, exist_ok=True)
    rows = report["runs"]
    pd.DataFrame(rows).to_csv(output / "all-results.csv", index=False)
    ranking = report["rank_changes"]
    winner = report.get("selected_config_from_NQ", ranking["development_winner"])
    scope = "synthetic data" if report["status"] == "synthetic" else "historical futures data"
    lines = [f"# {report['market']} audit", "", f"i ran nine settings and two baselines across four cost and delay cases on {scope}. all 44 runs are in [the CSV](all-results.csv), including any failures.", ""]
    if report["status"] == "synthetic":
        lines += ["these prices are made up. this checks the software, not whether a market has an edge.", ""]
    else:
        lines += ["i'd already explored these years in an older project, so this is a historical evaluation. the setting below was picked on NQ development data and kept for the other markets.", ""]
    lines += [f"the development pick is `{winner}`." if winner else "no setting met the development selection rule.", "",
              "| setting | development net $ | validation net $ | final net $ |", "| --- | ---: | ---: | ---: |"]
    configs = list(dict.fromkeys(row["config_id"] for row in rows))
    lookup = {(row["config_id"], row["scenario"], row["period"]): row for row in rows}
    for config in configs:
        values = []
        for period in ("development", "validation", "historical_final"):
            row = lookup.get((config, "base", period), {})
            values.append(f"{row['net_pnl_usd']:,.2f}" if row.get("status") == "ok" else "n/a")
        lines.append(f"| {config} | {' | '.join(values)} |")
    if winner:
        lines += ["", "## costs and delay", "", "| case | gross $ | net $ | fills |", "| --- | ---: | ---: | ---: |"]
        for scenario in ("gross_reference", "base", "higher_cost", "one_bar_late"):
            row = lookup.get((winner, scenario, "whole"), {})
            if row.get("status") == "ok":
                lines.append(f"| {scenario} | {row['gross_pnl_usd']:,.2f} | {row['net_pnl_usd']:,.2f} | {row['fills']} |")
        lines += ["", "## later results against the baselines", "",
                  "| part | baseline | annual return difference | 95% bootstrap interval |",
                  "| --- | --- | ---: | --- |"]
        for comparison in report.get("winner_uncertainty", []):
            if comparison["status"] == "ok":
                low, high = comparison["ci95_annual_return_difference"]
                lines.append(f"| {comparison['period']} | {comparison['baseline']} | {comparison['observed_annual_return_difference']:.2%} | {low:.2%} to {high:.2%} |")
    lines += ["", "i used paired five-day blocks, 2,000 bootstrap draws and seed 1729. the intervals depend on these days being a useful sample; they don't remove selection bias or predict future returns.", "",
              "the JSON and CSV keep gross/net P&L, return on stated capital, daily volatility and Sharpe, daily drawdown, hourly exposure, fills, costs, years and splits. prices are marked at the end; an open position isn't forced closed just to improve a result.", ""]
    if daily is not None:
        plot_market(rows, daily, winner, output, scope)
        lines += ["![results across the grid](grid.png)", "", "![net P&L through the run](equity.png)", ""]
    (output / "report.md").write_text("\n".join(lines), encoding="utf-8")


def plot_market(rows: list[dict], daily: dict[str, pd.Series], winner: str | None,
                output: Path, scope: str) -> None:
    configs = [key for key in daily if key not in ("flat", "always_long")]
    x = np.arange(len(configs))
    fig, ax = plt.subplots(figsize=(12, 5), layout="constrained")
    for offset, period in enumerate(("development", "validation", "historical_final")):
        values = {row["config_id"]: row["net_pnl_usd"] for row in rows
                  if row.get("scenario") == "base" and row.get("period") == period
                  and row.get("status") == "ok"}
        ax.bar(x + (offset - 1) * .26, [values.get(key, np.nan) for key in configs],
               width=.26, label=period.replace("historical_final", "final"))
    ax.axhline(0, color="#777", linewidth=.7)
    ax.set_xticks(x, configs, rotation=25, ha="right")
    ax.set(ylabel="net P&L ($)", title=f"all nine settings — {scope}")
    ax.legend()
    fig.savefig(output / "grid.png", dpi=140)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(10, 4), layout="constrained")
    for config in dict.fromkeys([winner, "always_long", "flat"]):
        if config in daily:
            ax.plot(daily[config].index, daily[config].cumsum(), label=config)
    ax.set(ylabel="cumulative net P&L ($)", title=f"base costs and delay — {scope}")
    ax.legend()
    fig.savefig(output / "equity.png", dpi=140)
    plt.close(fig)
