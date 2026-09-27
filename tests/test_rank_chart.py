import pandas as pd
from does_the_edge_hold.reporting import rank_table, plot_market

def test_hidden_baseline_cannot_change_rank_or_color_scale(tmp_path):
    rows = [{"config_id": key, "scenario": "base", "period": part, "status": "ok",
             "sharpe": score, "annual_mean_return": .01} for part in ("development", "validation", "historical_final")
            for key, score in (("flat", None), ("intraday_long", 100), ("a", 3), ("b", 2), ("c", 2))]
    table = rank_table(rows, ["a", "b", "c"])
    assert table.development.to_list() == [1, 2.5, 2.5]
    dates = pd.date_range("2020-01-01", periods=2, tz="UTC")
    daily = {key: pd.Series([1., 2.], index=dates) for key in ("a", "b", "c", "flat", "intraday_long")}
    plot_market(rows, daily, "a", tmp_path, "synthetic", baselines=("flat", "intraday_long"))
    saved = pd.read_csv(tmp_path / "rank-chart-table.csv", index_col=0)
    pd.testing.assert_frame_equal(saved, table, check_index_type=False)
