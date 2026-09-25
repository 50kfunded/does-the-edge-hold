import pandas as pd

from does_the_edge_hold.audit import audit_file, classify_gap


def test_session_close_and_short_missing_bar() -> None:
    prior = pd.Timestamp("2024-01-05 21:59Z")  # Friday 16:59 in New York
    after = pd.Timestamp("2024-01-07 23:00Z")  # Sunday 18:00 in New York
    label, open_minutes = classify_gap(prior, after, "1m")
    assert label == "regular_weekly_closure_candidate"
    assert open_minutes <= 2
    label, _ = classify_gap(pd.Timestamp("2024-01-09 14:00Z"),
                            pd.Timestamp("2024-01-09 14:03Z"), "1m")
    assert label == "short_no_trade_or_missing_candidate"
    label, _ = classify_gap(pd.Timestamp("2024-01-09 03:37:31Z"),
                            pd.Timestamp("2024-01-09 03:38:53Z"), "1s")
    assert label == "short_no_trade_or_missing_candidate"


def test_audit_flags_values_and_order(tmp_path) -> None:
    path = tmp_path / "NQ_1m.parquet"
    ts = pd.to_datetime(["2024-01-09 14:00Z", "2024-01-09 14:02Z",
                         "2024-01-09 14:02Z", "2024-01-09 14:01Z"])
    pd.DataFrame({"ts": ts, "open": [10, 10, 10, 10],
                  "high": [11, 9, 11, 11], "low": [9, 9, 9, 9],
                  "close": [10, 10, 10, 10], "volume": [1, 1, 0, 1]}).to_parquet(path)
    audit = audit_file(path, "1m", "NQ", batch_size=2)
    assert audit["duplicate_timestamps"] == 1
    assert audit["out_of_order_timestamps"] == 1
    assert audit["invalid_ohlc"] == 1
    assert audit["nonpositive_volume"] == 1
