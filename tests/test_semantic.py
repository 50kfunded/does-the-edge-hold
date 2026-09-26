import numpy as np
import pandas as pd
import pytest
from does_the_edge_hold.semantic import semantic_digest, semantic_file
from does_the_edge_hold.data import sha256_file
from does_the_edge_hold.synthetic import make_bars

def test_same_observations_different_parquet_encodings(tmp_path):
    bars = make_bars(minutes=240).drop(columns="contract")
    a, b = tmp_path / "a.parquet", tmp_path / "b.parquet"
    bars.to_parquet(a, compression="snappy", index=False)
    bars.set_index("ts").to_parquet(b, compression="gzip", row_group_size=17)
    assert sha256_file(a) != sha256_file(b)
    assert semantic_file(a) == semantic_file(b)
    assert semantic_digest([bars.iloc[:13], bars.iloc[13:]]) == semantic_file(a)
    changed = bars.copy()
    changed.loc[50, "close"] = np.nextafter(changed.loc[50, "close"], changed.loc[50, "high"])
    assert semantic_digest([changed]) != semantic_file(a)

@pytest.mark.parametrize("bad", ["order", "duplicate", "null", "infinite"])
def test_bad_observations_are_not_sorted_or_filled(bad):
    bars = make_bars(minutes=240).drop(columns="contract")
    if bad == "order": bars = bars.iloc[::-1]
    if bad == "duplicate": bars.loc[1, "ts"] = bars.loc[0, "ts"]
    if bad == "null": bars.loc[3, "close"] = np.nan
    if bad == "infinite": bars.loc[3, "close"] = np.inf
    with pytest.raises(ValueError): semantic_digest([bars])
