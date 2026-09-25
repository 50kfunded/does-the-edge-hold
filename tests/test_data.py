import pandas as pd

from does_the_edge_hold.data import iter_parquet, sha256_file


def test_readonly_batches_and_hash(tmp_path) -> None:
    path = tmp_path / "bars.parquet"
    frame = pd.DataFrame({"ts": pd.date_range("2024-01-01", periods=5, freq="min", tz="UTC"),
                          "open": [1] * 5, "high": [1] * 5, "low": [1] * 5,
                          "close": [1] * 5, "volume": [1] * 5})
    frame.set_index("ts").to_parquet(path)
    before = sha256_file(path)
    parts = list(iter_parquet(path, batch_size=2))
    assert [len(part) for part in parts] == [2, 2, 1]
    assert pd.concat(parts)["ts"].iloc[-1] == pd.Timestamp("2024-01-01 00:04Z")
    assert sha256_file(path) == before
