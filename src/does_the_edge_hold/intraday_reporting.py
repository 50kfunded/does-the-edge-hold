"""Render source-day results from saved outcomes without rerunning selection."""
from pathlib import Path
from .intraday_plan import read
from .reporting import diagnostics, plot_market, pct
from .trade_economics import write_diagnostics
from .trade_reporting import cost_curve, plot_cost_curve, economics_sections, year_label
import json
import pandas as pd

def render(output, *, plots=True):
    output = Path(output)
    summary = read(output / "summary.json")
    synthetic = summary["status"] == "synthetic_source_day"
    plan = summary["protocol"]
    winner = summary["markets"]["NQ"]["primary_pick"]
    markets = ', '.join(summary['markets'])
    lines = ["# the within-day study", "", f"i ran {summary['runtime']['cases']} cases across {markets}, with nine rules, two baselines and five cost/delay scenarios.", "",
             f"the NQ development pick was `{summary['markets']['NQ']['primary_pick']}`. i kept it in later dates and the other markets.", "",
             "these prices are made up. this checks the software, not a market edge." if synthetic else
             "this is a historical, conditional source-day comparison. i already knew related research through 2026; the final period isn't untouched data.", "",
             "i score exact 08:00–12:00 UTC weekday windows and reset every date. completeness is known after noon. this isn't a live 09:00 filter, unconditional investment curve or claim that missing dates have zero returns.", "",
             "the fixtures have made-up source labels and deliberate jumps between dates. each scored date resets independently. this doesn't resolve the real study's roll gate." if synthetic else
             "real contract identities are unknown. local cache matching and historical source-rule evidence support the narrower within-date inference. the original roll-aware study stays blocked. GC and CL have no scored strategy P&L here.", "",
             "| market | development windows | validation windows | final windows | pick dev Sharpe | pick val Sharpe | pick final Sharpe |",
             "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    own_intervals = []
    reports = {market: read(output / market / "results.json") for market in summary["markets"]}
    trade_data = write_diagnostics(output, summary, reports)
    trade_data["cost_sensitivity"] = cost_curve(trade_data, summary["primary"], winner, list(plan["splits_utc"]))
    (output / "trade-economics.json").write_text(json.dumps(trade_data, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    if plots:
        plot_cost_curve(trade_data["cost_sensitivity"], output, synthetic=synthetic)
    for market in summary["markets"]:
        folder = output / market
        report = reports[market]
        reports[market] = report
        rows = report["runs"]
        diag = diagnostics(report)
        (folder / "diagnostics.json").write_text(json.dumps(diag, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        lookup = {(r["config_id"], r["scenario"], r["period"]): r for r in rows}
        def row(config, period, scenario="base"):
            return lookup.get((config, scenario, period), {})
        def score(value): return "n/a" if value is None else f"{value:.3f}"
        periods = ("development", "validation", "historical_final")
        counts = [sum(v for k, v in report["coverage"][p].items() if k == "complete") for p in periods]
        scores = [score(row(winner, p).get("sharpe")) for p in periods]
        lines.append(f"| [{market}]({market}/report.md) | {' | '.join(map(str, counts))} | {' | '.join(scores)} |")
        own_intervals += [{"market": market, **i} for i in report["winner_uncertainty"]]
        panel = pd.read_csv(folder / "daily-pnl-all-scenarios.csv", index_col=0)
        panel.index = pd.to_datetime(panel.index, utc=True)
        daily = {k.split("|")[0]: panel[k] for k in panel if k.endswith("|base")}
        scope = "synthetic source-day windows" if synthetic else "retrospective complete windows"
        if plots:
            plot_market(rows, daily, winner, folder, scope, baselines=plan["baseline_ids"], conditional=True)
        text = [f"# {market}", "", f"i kept the NQ development pick: `{winner}`. all 55 cases use this market's same complete-window mask. no later reselection.", "",
                "these are made-up prices and software checks." if synthetic else "this is conditional historical P&L under the within-date source-rule inference, with unknown contract identity.", "",
                "| part | complete / candidate weekdays | gross $ | net $ | mean $ / window | scaled annual mean | Sharpe | entries | exposure |",
                "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
        for part in periods:
            r = row(winner, part)
            cov = report["coverage"][part]
            text.append(f"| {part} | {cov['complete']} / {cov['candidate_weekdays']} | {r.get('gross_pnl_usd', 0):,.2f} | {r.get('net_pnl_usd', 0):,.2f} | {r.get('mean_session_pnl_usd', 0):.2f} | {pct(r.get('annual_mean_return'))} | {score(r.get('sharpe'))} | {r.get('entry_trades', 'n/a')} | {pct(r.get('exposure'))} |" if r else f"| {part} | no eligible selection | | | | | | | |")
        text += ["", "252 is a convention applied to eligible windows. scaled means aren't realized annual returns or CAGR. no skipped date is filled with zero. exposure is held minutes / observed window minutes. one full contract has different dollar risk across markets; $100,000 is a reporting convention, with no margin or equal-risk sizing claim.", "",
                 "## all base settings", "", "| setting | dev net $ | val net $ | final net $ | dev Sharpe | val Sharpe | final Sharpe |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
        configs = list(dict.fromkeys(r["config_id"] for r in rows))
        for config in configs:
            values = [f"{row(config, p).get('net_pnl_usd', 0):,.2f}" for p in periods]
            scores = [score(row(config, p).get("sharpe")) for p in periods]
            text.append(f"| {config} | {' | '.join(values + scores)} |")
        text += economics_sections(trade_data, market, winner, plan)
        text += ["", "## did the gross winners survive costs?", "", "| part | positive gross settings | positive after base costs | median scaled mean | pick rank among eligible settings |", "| --- | ---: | ---: | ---: | ---: |"]
        for part, info in diag["periods"].items():
            text.append(f"| {part} | {info['positive_gross_candidates']} | {info['positive_gross_surviving_base_costs']} | {pct(info['median_annual_mean_return'])} | {info['selected_rank']} |")
        text += ["", "## costs and waiting", "", "| part | scenario | comparison | net $ change from base | gross $ change | fill change |", "| --- | --- | --- | ---: | ---: | ---: |"]
        for effect in diag["matched_effects"]:
            if effect["scenario"] != "base":
                text.append(f"| {effect['period']} | {effect['scenario']} | {effect['comparison']} | {effect['net_change_usd_from_base']:,.2f} | {effect['gross_change_usd']:,.2f} | {effect['fill_change']} |")
        text += ["", "each cost-only comparison keeps delay fixed. delay-only keeps cost rates fixed; it changes entry and terminal execution. a better delayed result can happen by chance. these minute opens are assumed first-trade proxies, not quotes or guaranteed fills.", "",
                 "## later uncertainty", "", "| part | pick minus baseline | block observations | paired windows | scaled mean difference | 95% interval |", "| --- | --- | ---: | ---: | ---: | --- |"]
        for interval in report["winner_uncertainty"]:
            if interval["status"] == "ok":
                low, high = interval["ci95_annual_return_difference"]
                text.append(f"| {interval['period']} | {interval['baseline']} | {interval['block_days']} | {interval['days']} | {pct(interval['observed_annual_return_difference'])} | {pct(low)} to {pct(high)} |")
            else:
                text.append(f"| {interval.get('period')} | {interval.get('baseline')} | {interval.get('block_days')} | {interval.get('days')} | {interval['status']} | |")
        text += ["", f"i use paired circular 3/5/10-observation blocks, {plan['statistics']['replicates']:,} draws and seed {plan['statistics']['seed']}, with at least {plan['statistics']['minimum_paired_observations']} paired windows. blocks follow ordered eligible observations, including calendar gaps. they don't restore missing days, correct selection or capture arbitrary long memory.", "",
                 "## same dates across markets", "", "| part | common windows | pick net $ | pick Sharpe | intraday long net $ |", "| --- | ---: | ---: | ---: | ---: |"]
        common_lookup = {(r["config_id"], r["scenario"], r["period"]): r for r in report["common_runs"]}
        for part in periods:
            r = common_lookup.get((winner, "base", part), {})
            long = common_lookup.get(("intraday_long", "base", part), {})
            text.append(f"| {part} | {r.get('days', 'n/a')} | {r.get('net_pnl_usd', 0):,.2f} | {score(r.get('sharpe'))} | {long.get('net_pnl_usd', 0):,.2f} |")
        text += ["", f"the common population has {summary['common_dates']:,} complete UTC dates in every included market. it is a separate coverage-conditioned comparison; the headline pick still comes from NQ's own development windows. [common outcomes](common-results.csv) retain all cases.", "",
                 "## yearly check of the fixed pick", "", "| year | windows | pick net $ | pick Sharpe | intraday long net $ |", "| --- | ---: | ---: | ---: | ---: |"]
        for year in sorted({r["period"] for r in rows if r["period"].isdigit()}):
            r, long = row(winner, year), row("intraday_long", year)
            text.append(f"| {year_label(year, plan)} | {r.get('days', 'n/a')} | {r.get('net_pnl_usd', 0):,.2f} | {score(r.get('sharpe'))} | {long.get('net_pnl_usd', 0):,.2f} |")
        text += ["", "partial labels describe the protocol's calendar span, not full observed coverage. profitable individual years remain visible; they don't replace the frozen split conclusion. i don't execute a switching or newly reselected yearly portfolio.", "",
                 f"protocol: `{report['plan_sha256']}`. semantic source: `{report['source_sha256']}`. execution: `{report['execution_sha256']}`. the manifest retains the input file hash separately.", "",
                 "![scaled means for every candidate](grid.png)", "", "![conditional complete-window sum; no live equity claim](equity.png)", "",
                 "![displayed candidate ranks only](ranks.png)", "",
                 "[all outcomes](all-results.csv) · [every scenario's eligible-window P&L](daily-pnl-all-scenarios.csv) · [rank figure numbers](rank-chart-table.csv)", ""]
        (folder / "report.md").write_text("\n".join(text), encoding="utf-8")
    successful = [i for i in own_intervals if i.get("status") == "ok"]
    includes_zero = sum(i["ci95_annual_return_difference"][0] <= 0 <= i["ci95_annual_return_difference"][1] for i in successful)
    below_zero = sum(i["ci95_annual_return_difference"][1] < 0 for i in successful)
    above_zero = sum(i["ci95_annual_return_difference"][0] > 0 for i in successful)
    lines += ["", f"of {len(successful)} computed own-window later intervals, {includes_zero} include zero, {below_zero} are wholly below zero and {above_zero} are wholly above zero. {len(own_intervals) - len(successful)} declared comparisons lack enough paired observations.", "",
              "these sample intervals only check the software." if synthetic else "these historical intervals are descriptive. they don't correct selection or establish a lasting tradable edge.", "",
              "## the assumptions", "", "| scenario | commission / side | adverse ticks / side | extra delay minutes |", "| --- | ---: | ---: | ---: |"]
    for case in plan["execution"]["scenarios"]:
        lines.append(f"| {case['name']} | {case['commission_usd_per_side']} | {case['slippage_ticks_per_side']} | {case['delay_minutes']} |")
    lines += ["", "partial windows remain visible in the source audit and aren't scored. missing warmup or terminal minutes aren't filled. successful ledgers end flat and reconcile gross minus commission/slippage to net; failures retain no completed score.", "",
              f"common complete dates: {summary['common_dates']:,}. the paired common-date intervals are saved in `summary.json`, with the actual denominators.", "",
              f"the actual run checked {summary['runtime']['audited_source_rows']:,} source rows, evaluated {summary['runtime']['evaluated_window_rows']:,} minute observations and cached features once per setting/date before the five scenarios. total measured time: {summary['runtime']['total_seconds']:.1f}s; sampled peak RSS: {summary['runtime']['sampled_peak_rss_mib']:.1f} MiB. this is one machine, not a throughput guarantee.", "",
              "[unscored sample price variation](descriptive-price-variation.json) · [the example's plan and settings](summary.json)" if synthetic else
              "[unscored source price variation](descriptive-price-variation.json) · [the frozen plan](https://github.com/50kfunded/does-the-edge-hold/blob/main/research/intraday/plan.json) · [within-day methods](https://github.com/50kfunded/does-the-edge-hold/blob/main/docs/intraday-plan.md)", ""]
    lines += ["[post-results trade economics and source identities](trade-economics.json)", ""]
    (output / "report.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
