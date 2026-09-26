import copy
import json
import pandas as pd
import pytest
from does_the_edge_hold.data import sha256_file
from does_the_edge_hold.resolve import write_resolution
from does_the_edge_hold.roll_gate import assess, require_ready, ROLL_POLICY
from does_the_edge_hold.timing import scheduled_instructions

def fixture_evidence(tmp_path, markets=("NQ", "ES")):
    audit = {"files": [{"market": m, "resolution": "1m", "sha256": m,
        "first_utc": "2024-01-01T00:00Z", "last_utc": "2024-02-15T00:00Z"} for m in markets]}
    origins = {"markets": [{"market": m, "verified_match": True, "selected_root": m + "c0"} for m in markets]}
    response = {"status": 0, "partial": [], "not_found": [], "stype_in": "continuous", "stype_out": "instrument_id",
        "result": {m + ".c.0": [{"d0": "2024-01-01", "d1": "2024-02-01", "s": "123"},
                    {"d0": "2024-02-01", "d1": "2024-03-01", "s": "456"}] for m in markets}}
    root = tmp_path / "mapping"
    write_resolution(response, audit, origins, root)
    evidence = json.loads((root / "evidence.json").read_text())
    evidence["roll_policy"] = ROLL_POLICY
    for m in markets:
        from does_the_edge_hold.rolls import read_schedule
        instructions = scheduled_instructions(read_schedule(root / f"{m}_rolls.csv"))
        instructions.to_csv(root / f"{m}_instructions.csv", index=False)
        source = root / f"{m}_policy-source.json"
        source.write_text(json.dumps({"scope": "wholly synthetic fixture", "known_in_advance": True}))
        evidence["markets"][m].update(instructions_sha256=sha256_file(root / f"{m}_instructions.csv"),
            policy_evidence={"kind": "advance_schedule", "reviewed": True, "sha256": sha256_file(source)})
    (root / "evidence.json").write_text(json.dumps(evidence))
    return audit, origins, root

def test_missing_mapping_is_a_hard_gate():
    gate = assess({"files": []}, {"markets": []})
    assert gate["primary_blocked"]
    with pytest.raises(RuntimeError, match="blocked by roll gate"):
        require_ready(gate)

def test_valid_subset_and_blocked_primary(tmp_path):
    audit, origins, root = fixture_evidence(tmp_path)
    plan = {"universe": {"primary": "NQ", "required": ["NQ"], "optional": ["ES", "GC"],
                        "allowed_exclusions": ["ES", "GC"]}}
    gate = assess(audit, origins, root, plan=plan)
    assert gate["status"] == "ready"
    assert gate["included"] == ["NQ", "ES"] and "GC" in gate["excluded"]
    wrong = copy.deepcopy(audit)
    wrong["files"][0]["sha256"] = "different data"
    assert assess(wrong, origins, root, plan=plan)["primary_blocked"]
    wrong = copy.deepcopy(audit)
    wrong["files"][1]["out_of_order_timestamps"] = 1
    assert assess(wrong, origins, root, plan=plan)["included"] == ["NQ"]

def test_identity_alone_is_not_a_causal_policy(tmp_path):
    audit, origins, root = fixture_evidence(tmp_path)
    (root / "NQ_policy-source.json").unlink()
    gate = assess(audit, origins, root)
    assert not gate["markets"]["NQ"]["ready"]
    assert any("advance-policy" in p for p in gate["markets"]["NQ"]["problems"])

