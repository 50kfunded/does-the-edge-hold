import copy

import pytest

from does_the_edge_hold.roll_gate import assess, require_ready
from does_the_edge_hold.resolve import write_resolution


def test_missing_mapping_is_a_hard_gate() -> None:
    audit = {"files": [{"market": market, "resolution": "1m", "sha256": "x"}
                       for market in ("NQ", "ES", "YM", "GC", "CL")]}
    provenance = {"markets": [{"market": market, "verified_match": True}
                              for market in ("NQ", "ES", "YM", "GC", "CL")]}
    result = assess(audit, provenance)
    assert result["status"] == "unresolved"
    with pytest.raises(RuntimeError, match="blocked by roll gate"):
        require_ready(result)


def test_resolved_schedule_passes_only_for_matching_exports(tmp_path) -> None:
    markets = ("NQ", "ES", "YM", "GC", "CL")
    audit = {"files": [{"market": market, "resolution": "1m",
                        "sha256": market, "first_utc": "2024-01-01T00:00:00+00:00",
                        "last_utc": "2024-02-15T00:00:00+00:00"} for market in markets]}
    origins = {"markets": [{"market": market, "verified_match": True,
                            "selected_root": market + "c0"}
                           for market in markets]}
    result = {}
    for origin in origins["markets"]:
        market = origin["market"]
        symbol = market + "." + origin["selected_root"][-2] + ".0"
        result[symbol] = [{"d0": "2024-01-01", "d1": "2024-02-01", "s": market + "H4"},
                          {"d0": "2024-02-01", "d1": "2024-03-01", "s": market + "M4"}]
    response = {"status": 0, "partial": [], "not_found": [],
                "stype_in": "continuous", "stype_out": "raw_symbol", "result": result}
    write_resolution(response, audit, origins, tmp_path)
    assert assess(audit, origins, tmp_path)["status"] == "ready"
    wrong = copy.deepcopy(audit)
    wrong["files"][0]["sha256"] = "different data"
    assert assess(wrong, origins, tmp_path)["status"] == "unresolved"


def test_volume_roll_dates_do_not_make_the_pre_roll_exit_causal(tmp_path) -> None:
    markets = ("NQ", "ES", "YM", "GC", "CL")
    audit = {"files": [{"market": market, "resolution": "1m", "sha256": market,
                        "first_utc": "2024-01-01T00:00Z", "last_utc": "2024-02-15T00:00Z"}
                       for market in markets]}
    origins = {"markets": [{"market": market, "verified_match": True,
                            "selected_root": market + ("v0" if market in ("GC", "CL") else "c0")}
                           for market in markets]}
    result = {market + "." + origin["selected_root"][-2] + ".0": [
                  {"d0": "2024-01-01", "d1": "2024-02-01", "s": market + "H4"},
                  {"d0": "2024-02-01", "d1": "2024-03-01", "s": market + "M4"}]
              for market, origin in zip(markets, origins["markets"])}
    response = {"status": 0, "partial": [], "not_found": [], "stype_in": "continuous",
                "stype_out": "raw_symbol", "result": result}
    write_resolution(response, audit, origins, tmp_path)
    gate = assess(audit, origins, tmp_path)
    assert gate["markets"]["NQ"]["ready"]
    assert not gate["markets"]["GC"]["ready"]
    assert any("volume-ranked" in reason for reason in gate["markets"]["GC"]["problems"])
