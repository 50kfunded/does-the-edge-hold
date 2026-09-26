from does_the_edge_hold.example import example_plan
from does_the_edge_hold.experiments import run_market
from does_the_edge_hold.synthetic import make_bars
from does_the_edge_hold.timing import scheduled_instructions

def test_cost_only_keeps_gross_path_and_fill_count():
    bars = make_bars(minutes=3600)
    schedule = bars.loc[bars.contract.ne(bars.contract.shift()), ["ts", "contract"]].rename(columns={"ts": "effective_at"})
    rows, _ = run_market(bars, "SYN", example_plan(), "p", "s", roll_instructions=scheduled_instructions(schedule))
    for config in {r["config_id"] for r in rows}:
        selected = {r["scenario"]: r for r in rows if r["config_id"] == config and r["period"] == "whole"}
        for name in ("gross_reference", "higher_cost"):
            assert selected[name]["gross_pnl_usd"] == selected["base"]["gross_pnl_usd"]
            assert selected[name]["fills"] == selected["base"]["fills"]
        assert selected["higher_cost"]["net_pnl_usd"] <= selected["base"]["net_pnl_usd"]
