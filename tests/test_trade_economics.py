import copy
import json
import shutil
from pathlib import Path
import numpy as np
import pytest
from does_the_edge_hold.trade_economics import economics, fixed_path_net, write_diagnostics

ROOT = Path(__file__).resolve().parents[1] / "reports/intraday"


def saved(market="NQ", period="development", config="revert-6-1.5", scenario="base"):
    report = json.loads((ROOT / market / "results.json").read_text())
    row = next(r for r in report["runs"] if (r["period"], r["config_id"], r["scenario"]) == (period, config, scenario))
    spec = json.loads((ROOT / market / "execution.json").read_text())["identity"]["evidence"]["instrument"]
    cost = next(s for s in report["protocol"]["execution"]["scenarios"] if s["name"] == scenario)
    return row, spec, cost


@pytest.mark.parametrize("part,gross,net,trips", [("development", 8900., -18895., 1853),
    ("validation", 2780., -10000., 852), ("historical_final", -5250., -20460., 1014)])
def test_independent_nq_anchors(part, gross, net, trips):
    row, spec, cost = saved(period=part)
    result = economics(row, spec, cost)
    assert result["status"] == "ok"
    assert result["completed_round_trips"] == trips and result["filled_sides"] == 2 * trips
    assert result["gross_per_round_trip_usd"] == pytest.approx(gross / trips)
    assert result["commission_per_round_trip_usd"] == 5.
    assert result["tick_cost_per_round_trip_usd"] == 10.
    assert result["rounding_per_round_trip_usd"] == 0.
    assert result["total_cost_per_round_trip_usd"] == 15.
    assert result["net_per_round_trip_usd"] == pytest.approx(net / trips)
    assert result["net_without_slippage_per_round_trip_usd"] < 0
    assert result["gross_per_round_trip_usd"] - result["total_cost_per_round_trip_usd"] == pytest.approx(result["net_per_round_trip_usd"])
    assert result["break_even_total_cost_per_round_trip_usd"] == result["gross_per_round_trip_usd"]
    assert result["nonnegative_cost_can_produce_positive_net"] == (gross > 0)


def test_different_ticks_and_rounding_residual_are_separate():
    for market, tick_value, base_cost in (("NQ", 5., 15.), ("ES", 12.5, 30.), ("YM", 5., 15.)):
        row, spec, cost = saved(market)
        result = economics(row, spec, cost)
        assert result["tick_value_usd"] == tick_value
        assert result["total_cost_per_round_trip_usd"] == base_cost
    row, spec, cost = saved("ES", scenario="cost_stress")
    assert economics(row, spec, cost)["total_cost_per_round_trip_usd"] == 60.
    row = copy.deepcopy(row)
    row["slippage_usd"] += 2.5
    row["net_pnl_usd"] -= 2.5
    result = economics(row, spec, cost)
    assert result["totals_usd"]["rounding_residual"] == 2.5
    assert result["rounding_per_round_trip_usd"] == pytest.approx(2.5 / row["entry_trades"])


def test_zero_trades_failures_and_missing_values_are_explicit():
    row, spec, cost = saved(config="flat")
    result = economics(row, spec, cost)
    assert result["status"] == "no_trades" and result["completed_round_trips"] == 0
    assert result["entries_per_window"] == 0 and result["fills_per_window"] == 0
    assert result["gross_per_round_trip_usd"] is None and result["break_even_total_cost_per_round_trip_usd"] is None
    assert result["nonnegative_cost_can_produce_positive_net"] is False
    row, spec, cost = saved()
    assert economics(row, None, cost)["status"] == "unsupported"
    assert economics(row, spec, {**cost, "delay_minutes": None})["status"] == "unsupported"
    failed = {**row, "status": "failed_unresolved"}
    assert economics(failed, spec, cost)["status"] == "not_scored"
    assert economics(failed, spec, cost)["net_per_round_trip_usd"] is None
    for changed in ({**row, "fills": None}, {**row, "gross_pnl_usd": float("nan")},
                    {**row, "fills": row["fills"] + 1}, {**row, "terminal_flat_windows": row["days"] - 1},
                    {**row, "net_pnl_usd": row["net_pnl_usd"] + 1}, {**row, "commission_per_side": 9.}):
        result = economics(changed, spec, cost)
        assert result["status"] == "unsupported" and result["net_per_round_trip_usd"] is None


def test_fixed_path_cost_formula_never_offers_negative_fees():
    assert fixed_path_net(80, 10, 0)["net_per_round_trip_usd"] == 8.
    assert fixed_path_net(80, 10, 8)["total_net_usd"] == 0.
    assert fixed_path_net(80, 10, 9)["total_net_usd"] == -10.
    assert fixed_path_net(0, 10, 0)["total_net_usd"] == 0.
    assert fixed_path_net(-80, 10, 0)["net_per_round_trip_usd"] == -8.
    assert fixed_path_net(0, 0, 5)["net_per_round_trip_usd"] is None
    with pytest.raises(ValueError): fixed_path_net(80, 10, -1)
    with pytest.raises(ValueError): fixed_path_net(80, 0, 1)
    row, spec, cost = saved()
    for gross, sign, allowed in ((0., "zero", False), (-80., "negative", False), (80., "positive", True)):
        r = {**row, "gross_pnl_usd": gross, "net_pnl_usd": gross - row["commission_usd"] - row["slippage_usd"]}
        result = economics(r, spec, cost)
        assert result["gross_sign"] == sign and result["nonnegative_cost_can_produce_positive_net"] == allowed


def test_period_ratio_uses_actual_trades_not_average_of_years():
    row, spec, cost = saved()
    years = [saved(period=str(year))[0] for year in range(2016, 2022)]
    total_gross = sum(r["gross_pnl_usd"] for r in years)
    total_trades = sum(r["entry_trades"] for r in years)
    assert total_gross == row["gross_pnl_usd"] and total_trades == row["entry_trades"]
    result = economics(row, spec, cost)
    assert result["gross_per_round_trip_usd"] == total_gross / total_trades
    assert result["gross_per_round_trip_usd"] != pytest.approx(np.mean([r["gross_pnl_usd"] / r["entry_trades"] for r in years]))


def test_all_saved_cases_validate_and_preserve_evaluation_identity(tmp_path):
    summary = json.loads((ROOT / "summary.json").read_text())
    reports = {}
    for market in summary["markets"]:
        folder = tmp_path / market
        folder.mkdir()
        for name in ("results.json", "execution.json", "all-results.csv"):
            shutil.copyfile(ROOT / market / name, folder / name)
        reports[market] = json.loads((folder / "results.json").read_text())
    artifact = write_diagnostics(tmp_path, summary, reports)
    assert len(artifact["rows"]) == 4950
    assert artifact["status_counts"] == {"ok": 4500, "no_trades": 450}
    assert artifact["analysis_status"].startswith("post-results")
    for r in artifact["rows"]:
        assert r["execution_sha256"] == artifact["sources"][r["market"]]["evaluation_execution_sha256"]
        assert r["source_result"].startswith(r["market"] + "/results.json#/")
    assert json.loads((tmp_path / "trade-economics.json").read_text()) == artifact


def test_cost_plot_and_tables_use_the_saved_diagnostic_values(tmp_path, monkeypatch):
    from does_the_edge_hold.trade_reporting import cost_curve, plot_cost_curve, economics_sections, year_label
    from matplotlib.figure import Figure
    rows = []
    for config in ("revert-6-1.5", "flat", "intraday_long"):
        for part in ("development", "validation", "historical_final"):
            row, spec, cost = saved(period=part, config=config)
            rows.append({**economics(row, spec, cost), "sample": "own_complete_dates"})
    artifact = {"rows": rows}
    plan = json.loads((ROOT / "summary.json").read_text())["protocol"]
    curve = cost_curve(artifact, "NQ", "revert-6-1.5", list(plan["splits_utc"]))
    artifact["cost_sensitivity"] = curve
    assert curve["cost_range_usd"][0] == 0 and curve["cost_range_usd"][1] >= 15.
    for s in curve["series"]:
        assert min(s["cost_points_usd"]) == 0 and 15. in s["cost_points_usd"]
        index = s["cost_points_usd"].index(15.)
        row, _, _ = saved(period=s["period"])
        assert s["net_per_round_trip_usd"][index] == pytest.approx(row["net_pnl_usd"] / row["entry_trades"])
        if s["break_even_budget_usd"] > 0:
            assert s["net_per_round_trip_usd"][s["cost_points_usd"].index(s["break_even_budget_usd"])] == pytest.approx(0.)
        else:
            assert all(c >= 0 for c in s["cost_points_usd"])
    captured = []
    save = Figure.savefig
    def record(figure, *args, **kwargs):
        captured.extend((list(line.get_xdata()), list(line.get_ydata())) for line in figure.axes[0].lines[:3])
        return save(figure, *args, **kwargs)
    monkeypatch.setattr(Figure, "savefig", record)
    (tmp_path / "NQ").mkdir()
    plot_cost_curve(curve, tmp_path)
    assert (tmp_path / "NQ/cost-budget.png").exists()
    assert captured == [(s["cost_points_usd"], s["net_per_round_trip_usd"]) for s in curve["series"]]
    text = "\n".join(economics_sections(artifact, "NQ", "revert-6-1.5", plan))
    assert "| development | 1,853 | 1.65 | 3.30 | 4.80 | 5.00 | 10.00 | 0.00 | -10.20 |" in text
    assert "### baselines on the same windows" in text and "n/a / n/a / n/a" in text
    assert year_label("2020", plan) == "2020"
    assert "partial" in year_label("2026", plan) and "2026-08-10" in year_label("2026", plan)
    invalid = copy.deepcopy(artifact)
    source, spec, cost = saved()
    failed = {**economics({**source, "status": "failed_unresolved"}, spec, cost), "sample": "own_complete_dates"}
    invalid["rows"][0] = failed
    invalid["cost_sensitivity"] = cost_curve(invalid, "NQ", "revert-6-1.5", list(plan["splits_utc"]))
    lines = economics_sections(invalid, "NQ", "revert-6-1.5", plan)
    assert "| development | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |" in lines
    note = next(i for i, line in enumerate(lines) if line.startswith("development: not_scored"))
    final_row = next(i for i, line in enumerate(lines) if line.startswith("| historical_final |"))
    assert note > final_row  # failure notes cannot split the Markdown table
