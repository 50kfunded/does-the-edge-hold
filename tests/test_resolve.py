import copy
import json

import pandas as pd
import pytest

from does_the_edge_hold.resolve import intervals, with_raw_symbols, write_resolution
from does_the_edge_hold.rolls import attach_contracts, read_schedule


@pytest.fixture
def response():
    return {"status": 0, "partial": [], "not_found": [], "stype_in": "continuous",
            "stype_out": "instrument_id", "result": {"ES.c.0": [
                {"d0": "2023-01-01", "d1": "2023-03-01", "s": "123"},
                {"d0": "2023-03-01", "d1": "2023-06-01", "s": "456"}]}}


def test_official_shaped_ids_and_bounds(response, tmp_path):
    audit = {"files": [{"market": "ES", "resolution": "1m", "sha256": "fixture",
                        "first_utc": "2023-01-02T00:00Z", "last_utc": "2023-05-31T23:59Z"}]}
    origins = {"markets": [{"market": "ES", "verified_match": True, "selected_root": "ESc0"}]}
    root = tmp_path / "mapping"
    output = write_resolution(response, audit, origins, root, retrieved_at="2023-06-02T00:00Z")
    evidence = json.loads(output.read_text())
    assert evidence["markets"]["ES"]["identity_type"] == "instrument_id"
    assert json.loads((root / "resolution.json").read_text()) == response
    schedule = read_schedule(root / "ES_rolls.csv")
    bars = pd.DataFrame({"ts": pd.to_datetime(["2023-02-28T23:59Z", "2023-03-01T00:00Z"], utc=True)})
    assert list(attach_contracts(bars, schedule).contract.astype(str)) == ["123", "456"]
    with pytest.raises(ValueError, match="interval"):
        attach_contracts(pd.DataFrame({"ts": pd.to_datetime(["2023-06-01T00:00Z"], utc=True)}), schedule)


@pytest.mark.parametrize("change", ["gap", "overlap", "partial", "unsupported"])
def test_bad_resolutions_fail(response, change):
    r = copy.deepcopy(response)
    if change == "gap":
        r["result"]["ES.c.0"][1]["d0"] = "2023-03-02"
    elif change == "overlap":
        r["result"]["ES.c.0"][1]["d0"] = "2023-02-28"
    elif change == "partial":
        r["partial"] = ["ES.c.0"]
    else:
        r["stype_out"] = "raw_symbol"
    with pytest.raises(ValueError):
        intervals(r, "ES.c.0", "continuous", "instrument_id")


def test_raw_names_intersect_date_valid_ids(response):
    raw = {"status": 0, "partial": [], "not_found": [], "stype_in": "instrument_id",
           "stype_out": "raw_symbol", "result": {
               "123": [{"d0": "2022-12-01", "d1": "2023-02-01", "s": "ESH3"},
                       {"d0": "2023-02-01", "d1": "2023-03-01", "s": "ESM3"}],
               "456": [{"d0": "2023-03-01", "d1": "2023-07-01", "s": "ESU3"}]}}
    ids = intervals(response, "ES.c.0", "continuous", "instrument_id")
    assert list(with_raw_symbols(ids, raw).contract) == ["ESH3", "ESM3", "ESU3"]
    raw["result"]["123"][0]["d0"] = "2023-01-02"
    with pytest.raises(ValueError, match="incomplete"):
        with_raw_symbols(ids, raw)
