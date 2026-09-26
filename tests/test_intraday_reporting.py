import numpy as np
import pandas as pd
from does_the_edge_hold.intraday_study import summarize_windows
from does_the_edge_hold.uncertainty import paired_block_bootstrap

def test_failed_window_never_becomes_zero_or_completed_score():
    failed = pd.DataFrame({"status": ["ok", "failed_unresolved"], "net_pnl_usd": [2., np.nan]})
    score = summarize_windows(failed, 100000)
    assert score["status"] == "failed" and "sharpe" not in score and "net_pnl_usd" not in score

def test_short_paired_population_fails_the_declared_gate():
    dates = pd.bdate_range("2024-01-01", periods=20, tz="UTC")
    pick = pd.Series(np.arange(20), index=dates)
    result = paired_block_bootstrap(pick, pick * 0, "2024-01-01", "2025-01-01", 100000, minimum_days=30)
    assert result["status"] == "too_few_days" and result["days"] == 20
