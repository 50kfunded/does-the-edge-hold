import json
from pathlib import Path

import pytest

from does_the_edge_hold.experiments import run_empirical, run_market
from does_the_edge_hold.synthetic import make_bars


ROOT = Path(__file__).resolve().parents[1]


def test_all_grid_runs_are_kept() -> None:
    plan = json.loads((ROOT / "research-plan.json").read_text(encoding="utf-8"))
    rows, daily = run_market(make_bars(minutes=600), "SYN", plan, "plan", "source")
    assert len({row["run_id"] for row in rows}) == 44  # nine rules + two baselines, four scenarios
    assert len(daily) == 11
    assert not any(row["status"] == "failed" for row in rows)
    assert {row["scenario"] for row in rows} == {
        "gross_reference", "base", "higher_cost", "one_bar_late"}
    repeated, repeated_daily = run_market(make_bars(minutes=600), "SYN", plan, "plan", "source")
    assert rows == repeated
    for config, values in daily.items():
        assert values.equals(repeated_daily[config])


def test_empirical_pnl_stops_at_roll_gate(tmp_path) -> None:
    with pytest.raises(RuntimeError, match="blocked by roll gate"):
        run_empirical(tmp_path / "no-bars", tmp_path / "no-mapping",
                      ROOT / "reports/local-data-audit.json",
                      ROOT / "reports/local-provenance.json",
                      ROOT / "research-plan.json", ROOT / "research-plan.lock.json",
                      tmp_path / "output")
    assert not (tmp_path / "output").exists()
