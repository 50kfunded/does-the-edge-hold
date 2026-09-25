import pandas as pd

from does_the_edge_hold.signals import SignalSpec, decisions


def hourly() -> pd.DataFrame:
    return pd.DataFrame({"known_at": pd.date_range("2024-01-01 01:00", periods=8,
                                                    freq="h", tz="UTC"),
                         "close": [10, 11, 12, 11, 10, 9, 8, 7],
                         "contract": ["A"] * 8})


def test_future_prices_do_not_change_earlier_signals() -> None:
    original = hourly()
    altered = original.copy()
    altered.loc[5:, "close"] = [99, 98, 97]
    for spec in (SignalSpec("momentum", 2), SignalSpec("mean_reversion", 2, 0.5)):
        before = decisions(original, spec)
        after = decisions(altered, spec)
        assert before.loc[:4, "target"].tolist() == after.loc[:4, "target"].tolist()


def test_roll_resets_signal_history() -> None:
    bars = hourly()
    bars.loc[4:, "contract"] = "B"
    output = decisions(bars, SignalSpec("momentum", 2))
    assert output.loc[4:5, "target"].tolist() == [0, 0]
