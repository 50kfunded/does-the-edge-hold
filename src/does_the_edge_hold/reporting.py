"""Tables, normalized figures and descriptive research answers."""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PERIODS = ("development", "validation", "historical_final")
BASELINES = ("flat", "always_long")

def baseline_ids(report):
    """Legacy saved reports remain readable; new reports declare their baselines."""
    return tuple(report.get("baseline_ids", report.get("protocol", {}).get("baseline_ids", BASELINES)))

def rank_table(rows, configs):
    """Ordinal ranks in exactly the displayed universe; equal scores share ranks."""
    matrix = {}
    for period in PERIODS:
        scores = {r["config_id"]: r["sharpe"] for r in rows if r.get("scenario") == "base"
                  and r.get("period") == period and r.get("status") == "ok"
                  and r.get("sharpe") is not None and r["config_id"] in configs}
        ranks = pd.Series(scores, dtype=float).rank(ascending=False, method="average")
        matrix[period] = [ranks.get(k, np.nan) for k in configs]
    return pd.DataFrame(matrix, index=pd.Index(configs, name="config_id"))

def diagnostics(report):
    rows = report["runs"]
    configs = sorted({r["config_id"] for r in rows} - set(baseline_ids(report)))
    lookup = {(r["config_id"], r["scenario"], r["period"]): r for r in rows}
    winner = report.get("selected_config_from_primary", report.get("selected_config_from_NQ", report["rank_changes"]["development_winner"]))
    out = {"selected_config": winner, "periods": {}, "rank_stability": {}, "matched_effects": []}
    for period in PERIODS:
        valid = [lookup.get((c, "base", period), {}) for c in configs]
        valid = [r for r in valid if r.get("status") == "ok"]
        gross_positive = [r for r in valid if r["gross_pnl_usd"] > 0]
        rank = report["rank_changes"]["ranks"][period]
        pick = lookup.get((winner, "base", period), {})
        out["periods"][period] = {
            "successful_candidates": len(valid), "eligible_candidates": len(rank),
            "positive_gross_candidates": len(gross_positive),
            "positive_gross_surviving_base_costs": sum(r["net_pnl_usd"] > 0 for r in gross_positive),
            "positive_net_candidates": sum(r["net_pnl_usd"] > 0 for r in valid),
            "median_annual_mean_return": float(np.median([r["annual_mean_return"] for r in valid])) if valid else None,
            "selected_annual_mean_return": pick.get("annual_mean_return"),
            "selected_rank": rank.index(winner) + 1 if winner in rank else None,
            "selected_entries": pick.get("entry_trades"), "observed_sessions": pick.get("days"),
            "selected_sharpe": pick.get("sharpe")}
        for scenario in dict.fromkeys(r["scenario"] for r in rows):
            stress = lookup.get((winner, scenario, period), {})
            if pick.get("status") != "ok" or stress.get("status") != "ok":
                continue
            out["matched_effects"].append({"period": period, "scenario": scenario,
                "net_change_usd_from_base": stress["net_pnl_usd"] - pick["net_pnl_usd"],
                "annual_mean_return_change": stress["annual_mean_return"] - pick["annual_mean_return"],
                "gross_change_usd": stress["gross_pnl_usd"] - pick["gross_pnl_usd"],
                "fill_change": stress["fills"] - pick["fills"],
                "delay_minutes": stress["delay_minutes"],
                "comparison": "reference" if scenario == "base" else
                    "cost only" if stress["delay_minutes"] == pick["delay_minutes"] else
                    "delay only" if all(stress[k] == pick[k] for k in ("fee_bps", "slippage_bps", "commission_per_side", "slippage_ticks_per_side")) else "combined cost and delay"})
    for period in PERIODS[1:]:
        left = report["rank_changes"]["ranks"]["development"]
        right = report["rank_changes"]["ranks"][period]
        common = set(left) & set(right)
        a = pd.Series({k: left.index(k) for k in common}, dtype=float)
        b = pd.Series({k: right.index(k) for k in common}, dtype=float)
        corr = float(a.corr(b, method="spearman")) if len(common) > 1 else None
        out["rank_stability"][period] = {"common_eligible_candidates": len(common), "spearman": corr}
    return out

def pct(v):
    return "n/a" if v is None else f"{v:.3%}"

def market_report(report, output, daily=None):
    import json
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    rows = report["runs"]
    baselines = baseline_ids(report)
    protocol = report.get("protocol", {})
    pd.DataFrame(rows).to_csv(output / "all-results.csv", index=False)
    diag = diagnostics(report)
    (output / "diagnostics.json").write_text(json.dumps(diag, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    winner = diag["selected_config"]
    lookup = {(r["config_id"], r["scenario"], r["period"]): r for r in rows}
    configs = sorted({r["config_id"] for r in rows} - set(baselines))
    cases = list(dict.fromkeys(r["scenario"] for r in rows))
    runs = len({r["run_id"] for r in rows})
    failed = len({r["run_id"] for r in rows if r["status"] == "failed"})
    synthetic = report["status"] == "synthetic"
    scope = "made-up prices" if synthetic else "public spot bars" if report["status"] == "historical_public_spot" else "futures bars"
    lines = [f"# {report['market']}", "",
        f"i ran {len(configs)} settings and {len(baselines)} baselines across {len(cases)} scenarios on {scope}. {failed} of {runs} runs failed. [every result](all-results.csv) stays in the report.",
        "", "these are software checks, not market findings." if synthetic else
        f"i kept the development pick from {report.get('primary', protocol.get('universe', {}).get('primary', 'unspecified'))}: `{winner}`. the later periods are historical checks, not untouched data.", "",
        "## the three parts", "",
        "| part | observed days / sessions | eligible settings | positive gross → positive net | pick: annual mean | median setting: annual mean | pick: Sharpe | pick rank | entries |",
        "| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |"]
    for period, info in diag["periods"].items():
        score = info["selected_sharpe"]
        lines.append(f"| {period} | {info['observed_sessions']} | {info['eligible_candidates']} | {info['positive_gross_candidates']} → {info['positive_gross_surviving_base_costs']} | {pct(info['selected_annual_mean_return'])} | {pct(info['median_annual_mean_return'])} | {score:.3f} | {info['selected_rank']} | {info['selected_entries']} |" if score is not None else f"| {period} | no eligible pick | | | | | | | |")
    lines += ["", "annual mean is mean daily P&L / stated capital, scaled by the declared observations per year. it isn't CAGR. the median is across all successful candidates, including those below the selection trade threshold; it isn't a traded portfolio.", ""]
    audit = report.get("audit")
    if audit:
        lines += [f"coverage: {audit['first_utc']} through {audit['last_utc']}, {audit['rows']:,} source bars; {audit['missing_calendar_days']} missing days. period counts are above.", ""]
    lines += ["## all settings at base assumptions", "",
        "| setting | development annual mean | validation annual mean | final annual mean |",
        "| --- | ---: | ---: | ---: |"]
    for config in configs + list(baselines):
        values = [pct(lookup.get((config, "base", p), {}).get("annual_mean_return")) for p in PERIODS]
        lines.append(f"| {config} | {' | '.join(values)} |")
    lines += ["", "## what changed under stress", "",
        "| part | scenario | comparison | annual mean change from base | gross $ change | fill change |",
        "| --- | --- | --- | ---: | ---: | ---: |"]
    for effect in diag["matched_effects"]:
        if effect["scenario"] == "base":continue
        lines.append(f"| {effect['period']} | {effect['scenario']} | {effect['comparison']} | {pct(effect['annual_mean_return_change'])} | {effect['gross_change_usd']:,.2f} | {effect['fill_change']} |")
    lines += ["", "cost-only cases keep the delay fixed; delay-only cases keep cost rates fixed. delay can help by chance. these are assumed fills from OHLCV, not measured spreads or actual orders.", "",
        "## how uncertain it is", "",
        "| part | comparison | block length | annual mean difference | 95% interval |",
        "| --- | --- | ---: | ---: | --- |"]
    for comp in report.get("winner_uncertainty", []):
        if comp["status"] == "ok":
            low, high = comp["ci95_annual_return_difference"]
            lines.append(f"| {comp['period']} | pick − {comp['baseline']} | {comp['block_days']} | {pct(comp['observed_annual_return_difference'])} | {pct(low)} to {pct(high)} |")
        else:
            lines.append(f"| {comp['period']} | {comp['baseline']} | {comp.get('block_days')} | {comp['status']} | |")
    stats = protocol.get("statistics", {})
    lines += ["", f"paired circular blocks keep the two strategies on the same observations. block lengths: {stats.get('block_lengths', [3, 5, 10])}; draws: {stats.get('replicates', 2000):,}; seed: {stats.get('seed', 1729)}. these are descriptive intervals. longer dependence, regime changes, prior knowledge and selection remain limits.", "",
        "## rank changes and yearly selections", ""]
    for period, info in diag["rank_stability"].items():
        lines.append(f"- development vs {period}: Spearman {info['spearman']}, on {info['common_eligible_candidates']} settings eligible in both parts.")
    lines += ["", "walk-forward below selects on the prior three calendar years. it inspects an already continuously simulated candidate in the next year. it doesn't execute a switching portfolio, charge switching costs or reset inventory at the year boundary.", "",
        "| next year | selected setting | train Sharpe | next-year Sharpe | next-year days |",
        "| --- | --- | ---: | ---: | ---: |"]
    for window in report.get("walk_forward", []):
        if window["status"] == "ok":
            value = window["test_sharpe"]
            lines.append(f"| {window['test_year']} | {window['winner']} | {window['train_sharpe']:.3f} | {'n/a' if value is None else f'{value:.3f}'} | {window['test_days']} |")
    lines += ["", "## assumptions i kept", ""]
    if report["status"] == "historical_public_spot":
        execution = protocol.get("execution", {})
        lines += [f"i used one cash-funded unit per market, with ${execution.get('starting_capital_usd_per_market', 0):,.0f} stated capital and zero interest on spare cash. the markets have different dollar risk; this isn't equal-risk replication. final inventory is marked, not sold at an invented price.", ""]
    else:
        lines += ["one futures contract or flat, price-difference P&L times the multiplier. roll instructions need independent advance evidence. daily marks miss intraday drawdown. exposure counts observed sampled marks, not elapsed trading time.", ""]
    lines += ["| scenario | commission / side | slippage ticks / side | fee bps | slippage bps | extra delay minutes |", "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for case in protocol.get("execution", {}).get("scenarios", []):
        lines.append(f"| {case['name']} | {case['commission_usd_per_side']} | {case['slippage_ticks_per_side']} | {case.get('fee_bps', 0)} | {case.get('slippage_bps', 0)} | {case['delay_minutes']} |")
    lines += [""]
    lines += [f"protocol: `{report['plan_sha256']}`. source: `{report['source_sha256']}`.", ""]
    if report.get("execution_sha256"):
        lines += [f"execution: `{report['execution_sha256']}`. the saved manifest records code, actual callables, inputs and dependencies.", ""]
    if daily is not None:
        plot_market(rows, daily, winner, output, scope, baselines=baselines)
        lines += ["![annual means across all settings](grid.png)", "", "![base daily P&L path](equity.png)", "", "![candidate ranks by split](ranks.png)", ""]
    (output / "report.md").write_text("\n".join(lines), encoding="utf-8")

def plot_market(rows, daily, winner, output, scope, *, baselines=BASELINES, conditional=False):
    configs = [k for k in daily if k not in baselines]
    x = np.arange(len(configs))
    fig, ax = plt.subplots(figsize=(12, 5), layout="constrained")
    for offset, period in enumerate(PERIODS):
        values = {r["config_id"]: r["annual_mean_return"] * 100 for r in rows if r.get("scenario") == "base" and r.get("period") == period and r.get("status") == "ok"}
        ax.bar(x + (offset - 1) * .26, [values.get(k, np.nan) for k in configs], width=.26, label=period.replace("historical_final", "final"))
    ax.axhline(0, color="#777", linewidth=.7)
    ax.set_xticks(x, configs, rotation=30, ha="right")
    ax.set(ylabel="annual mean return on stated capital (%)", title=f"every setting; unequal periods normalized — {scope}")
    ax.legend()
    fig.savefig(output / "grid.png", dpi=140)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(10, 4), layout="constrained")
    for config in dict.fromkeys([winner, *baselines]):
        if config in daily:
            ax.plot(np.arange(1, len(daily[config]) + 1) if conditional else daily[config].index, daily[config].cumsum(), label=config)
    ax.set(ylabel="conditional net P&L sum ($)" if conditional else "cumulative net P&L ($)",
           title=f"fixed development pick; base costs and delay — {scope}")
    if conditional: ax.set_xlabel("eligible window number; skipped dates excluded; not live equity")
    ax.legend()
    fig.savefig(output / "equity.png", dpi=140)
    plt.close(fig)
    table = rank_table(rows, configs)
    table.to_csv(output / "rank-chart-table.csv")
    matrix = table.to_numpy().T
    fig, ax = plt.subplots(figsize=(12, 3), layout="constrained")
    im = ax.imshow(matrix, aspect="auto", cmap="viridis_r", vmin=1, vmax=max(2, len(configs)))
    ax.set_xticks(x, configs, rotation=30, ha="right")
    ax.set_yticks(range(3), ["development", "validation", "final"])
    ax.set_title("daily Sharpe ranks in the displayed candidates only; ties use average rank")
    fig.colorbar(im, ax=ax, label="rank (1 is highest)")
    fig.savefig(output / "ranks.png", dpi=140)
    plt.close(fig)

