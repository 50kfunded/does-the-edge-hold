import numpy as np
import pandas as pd

from does_the_edge_hold.walk_forward import evaluate


def test_walk_forward_selects_only_previous_years() -> None:
    dates = pd.bdate_range("2017-01-01", "2020-12-31", tz="UTC")
    rng = np.random.default_rng(2)
    a = pd.Series(rng.normal(1, 3, len(dates)), index=dates)
    b = pd.Series(rng.normal(-1, 3, len(dates)), index=dates)
    a.loc[a.index.year == 2020] -= 3
    b.loc[b.index.year == 2020] += 3
    rows = [{"config_id": config, "scenario": "base", "period": str(year),
             "status": "ok", "entry_trades": 30, "fills": 60}
            for config in ("a", "b") for year in range(2017, 2021)]
    windows = evaluate({"a": a, "b": b}, rows, 100_000, 20)
    assert windows[0]["test_year"] == 2020
    assert windows[0]["winner"] == "a"
    assert windows[0]["test_net_pnl_usd"] < 0
