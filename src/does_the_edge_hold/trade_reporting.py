"""Tables and a cost-only curve from validated saved-result economics."""
import math
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from .trade_economics import fixed_path_net


def lookup(artifact, market, config, part, scenario="base"):
    return next((r for r in artifact["rows"] if (r["market"], r["config_id"], r["period"], r["scenario"], r["sample"]) ==
                 (market, config, part, scenario, "own_complete_dates")), None)


def cost_curve(artifact, market, pick, periods):
    rows = [lookup(artifact, market, pick, p) for p in periods]
    if any(r is None or r["status"] != "ok" for r in rows):
        return {"status": "unavailable", "reason": "selected base paths require scored completed trades in every split"}
    maximum = max([r["total_cost_per_round_trip_usd"] for r in rows] +
                  [max(0., r["break_even_total_cost_per_round_trip_usd"]) for r in rows])
    upper = max(1., math.ceil(maximum * 1.25))
    series = []
    for r in rows:
        budget = r["break_even_total_cost_per_round_trip_usd"]
        points = sorted(set([0., upper, r["total_cost_per_round_trip_usd"]] + ([budget] if budget > 0 else [])))
        series.append({"period": r["period"], "run_id": r["run_id"], "execution_sha256": r["execution_sha256"],
            "completed_round_trips": r["completed_round_trips"], "gross_usd": r["totals_usd"]["gross"],
            "gross_per_round_trip_usd": r["gross_per_round_trip_usd"], "break_even_budget_usd": budget,
            "nonnegative_cost_can_produce_positive_net": r["nonnegative_cost_can_produce_positive_net"],
            "base_cost_per_round_trip_usd": r["total_cost_per_round_trip_usd"],
            "cost_points_usd": points, "net_per_round_trip_usd": [fixed_path_net(r["totals_usd"]["gross"], r["completed_round_trips"], c)["net_per_round_trip_usd"] for c in points]})
    return {"status": "ok", "market": market, "config_id": pick, "scenario": "base", "sample": "own_complete_dates",
            "figure": market + "/cost-budget.png", "cost_range_usd": [0., upper], "series": series}


def plot_cost_curve(curve, output, *, synthetic=False):
    if curve["status"] != "ok": return
    fig, ax = plt.subplots(figsize=(8.6, 4.8), layout="constrained")
    colors = ["#2465a8", "#d57616", "#3c8054"]
    for i, (s, color) in enumerate(zip(curve["series"], colors)):
        part = s["period"].replace("historical_final", "final (historical)")
        ax.plot(s["cost_points_usd"], s["net_per_round_trip_usd"], color=color, label=part, linewidth=2)
        gross, base, budget = s["gross_per_round_trip_usd"], s["base_cost_per_round_trip_usd"], s["break_even_budget_usd"]
        ax.scatter([0], [gross], color=color, marker="o", s=32)
        ax.scatter([base], [gross - base], color=color, marker="D", s=38)
        if budget > 0:
            ax.scatter([budget], [0], edgecolors=color, facecolors="white", linewidth=1.5, s=55, zorder=4)
            ax.annotate(f"break-even ${budget:.2f}", (budget, 0), xytext=(8, 16 if i == 0 else -24),
                        textcoords="offset points", fontsize=9, color=color,
                        bbox={"boxstyle": "round,pad=0.15", "fc": "white", "ec": "none", "alpha": .9})
    bases = {s["base_cost_per_round_trip_usd"] for s in curve["series"]}
    if len(bases) == 1:
        base = next(iter(bases))
        ax.axvline(base, color="0.65", linestyle=":", linewidth=1)
        ax.text(base, .98, f" base ${base:.2f}", transform=ax.get_xaxis_transform(), va="top", fontsize=9)
    ax.axhline(0, color="0.3", linewidth=1)
    ax.set_xlim(curve["cost_range_usd"])
    ax.set_xlabel("total assumed cost ($ / completed round trip)")
    ax.set_ylabel("net P&L ($ / completed round trip)")
    ax.set_title(("made-up example: " if synthetic else "") + f"{curve['market']} {curve['config_id']}; filled paths held fixed")
    ax.legend(loc="lower left", fontsize=9)
    ax.grid(alpha=.15)
    fig.savefig(Path(output) / curve["figure"], dpi=170)
    plt.close(fig)


def _fmt(value, decimals=2):
    return "n/a" if value is None else f"{value:,.{decimals}f}"


def economics_sections(artifact, market, pick, plan):
    periods = list(plan["splits_utc"])
    selected = [lookup(artifact, market, pick, p) for p in periods]
    lines = ["", "## what each completed trade earned", "",
             "these are aggregate dollars divided by actual completed round trips, not averages of yearly ratios. frequency means entries or filled sides per eligible window; it isn't portfolio notional turnover.", "",
             "| part | round trips | entries / window | fills / window | gross $ / trip | commission $ / trip | tick cost $ / trip | rounding $ / trip | net $ / trip |",
             "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for part, r in zip(periods, selected):
        fields = ("completed_round_trips", "entries_per_window", "fills_per_window", "gross_per_round_trip_usd",
                  "commission_per_round_trip_usd", "tick_cost_per_round_trip_usd", "rounding_per_round_trip_usd", "net_per_round_trip_usd")
        vals = [_fmt(r.get(k) if r else None, 0 if k == "completed_round_trips" else 2) for k in fields]
        lines.append(f"| {part} | " + " | ".join(vals) + " |")
        if r and r["status"] not in ("ok", "no_trades"):
            lines += ["", f"{part}: {r['status']}; {'; '.join(r['reasons'])}.", ""]
    valid = next((r for r in selected if r and r["status"] == "ok"), None)
    if valid:
        nominal = 2 * (valid["declared_commission_usd_per_side"] + valid["declared_slippage_ticks_per_side"] * valid["tick_value_usd"])
        lines += ["", f"the recorded tick value is ${valid['tick_value_usd']:.2f}. base uses two ${valid['declared_commission_usd_per_side']:.2f} commissions and {2 * valid['declared_slippage_ticks_per_side']:g} adverse ticks per round trip: ${nominal:.2f} before any rounding residual. the rounding column is recorded slippage minus that declared tick cost."]
    lines += ["", "## all candidates per trade", "", "each cell shows gross / total costs / net dollars per round trip. the adjacent frequency is completed trips per eligible window. totals and sample counts remain above."]
    header = ["", "| setting | dev gross / cost / net | dev trips / window | val gross / cost / net | val trips / window | final gross / cost / net | final trips / window |",
              "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    configs = list(dict.fromkeys(r["config_id"] for r in artifact["rows"] if r["market"] == market and r["sample"] == "own_complete_dates" and r["scenario"] == "base"))
    def candidate_line(config):
        values = []
        for part in periods:
            r = lookup(artifact, market, config, part)
            values += [" / ".join(_fmt(r.get(k) if r else None) for k in ("gross_per_round_trip_usd", "total_cost_per_round_trip_usd", "net_per_round_trip_usd")),
                       _fmt(r.get("entries_per_window") if r else None)]
        return f"| {config} | " + " | ".join(values) + " |"
    lines += header + [candidate_line(c) for c in configs if c not in plan["baseline_ids"]]
    lines += ["", "### baselines on the same windows"] + header + [candidate_line(c) for c in plan["baseline_ids"]]
    lines += ["", "flat has no completed trades, so its per-trade ratios are undefined. missing, failed or inconsistent accounting also gives n/a; the diagnostic artifact records the reason."]
    if "intraday_long" in plan["baseline_ids"]:
        lines += ["", "## the pick versus intraday long", "",
                  "these differences use the same market's eligible windows: pick minus baseline. net difference equals gross difference minus the extra modelled costs. this is an accounting decomposition, not a claim about the cause of a market regime.", "",
                  "| part | pick trips / window | long trips / window | gross difference $ / window | cost difference $ / window | net difference $ / window |",
                  "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
        for part, r in zip(periods, selected):
            long = lookup(artifact, market, "intraday_long", part)
            if not r or not long or r["status"] != "ok" or long["status"] != "ok" or r["eligible_windows"] != long["eligible_windows"]:
                lines.append(f"| {part} | n/a | n/a | n/a | n/a | n/a |")
                continue
            vals = [r["entries_per_window"], long["entries_per_window"]] + [(r["totals_usd"][k] - long["totals_usd"][k]) / r["eligible_windows"] for k in ("gross", "total_cost", "net")]
            lines.append(f"| {part} | " + " | ".join(_fmt(v) for v in vals) + " |")
    if market == artifact["cost_sensitivity"].get("market"):
        lines += ["", "## the cost budget on the fixed paths", "",
                  "net at total cost C per round trip is G - R*C. break-even is G/R, the gross column above. a positive budget allows positive net only below that cost; a zero or negative budget allows none. a negative budget isn't an achievable fee reduction.", "",
                  "![net per trade as assumed total cost changes](cost-budget.png)", "",
                  "the circles start at zero cost, hollow circles mark positive break-even budgets, and diamonds show recorded base costs. these trades and timestamps stay fixed. this isn't an estimate of executable costs and doesn't change fill probabilities, spread, queueing or impact. delay changes can change the path and have separate saved economics."]
    lines += ["", "[saved trade economics for every scenario and sample](../trade-economics.json). this is post-results descriptive arithmetic; the original evaluation identities stay unchanged."]
    return lines


def year_label(year, plan):
    start = max(pd.Timestamp(f"{year}-01-01"), min(pd.Timestamp(v[0]) for v in plan["splits_utc"].values()))
    end = min(pd.Timestamp(f"{int(year)+1}-01-01"), max(pd.Timestamp(v[1]) for v in plan["splits_utc"].values()))
    if start != pd.Timestamp(f"{year}-01-01") or end != pd.Timestamp(f"{int(year)+1}-01-01"):
        return f"{year} (partial: {start.date()} to {end.date()}, end exclusive)"
    return year
