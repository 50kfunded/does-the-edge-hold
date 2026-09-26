from does_the_edge_hold.local_report import count_splits
from does_the_edge_hold.synthetic import make_bars


def test_split_counts_use_start_inclusive_and_end_exclusive(tmp_path) -> None:
    bars = make_bars(minutes=240)
    path = tmp_path / "bars.parquet"
    bars.to_parquet(path, index=False)
    counts = count_splits(path, {"first": ["2024-01-08T00:00Z", "2024-01-08T01:00Z"],
                                "second": ["2024-01-08T01:00Z", "2024-01-08T02:00Z"]})
    assert counts == {"first": 60, "second": 60}
