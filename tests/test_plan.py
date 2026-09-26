import copy
import json

import pytest

from does_the_edge_hold.plan import freeze, verify
from does_the_edge_hold.example import example_plan


def test_final_run_rejects_a_changed_plan_or_source(tmp_path) -> None:
    plan = example_plan()
    plan.update(version=3, prior_exposure="synthetic fixture inspected")
    plan["signal_families"]["momentum"]["lookback_hours"].append(96)
    plan["configuration_count"] = 10
    audit = {"files": [{"market": "NQ", "resolution": "1m", "sha256": "abc"}]}
    plan_path, audit_path, lock_path = (tmp_path / name for name in
                                        ("plan.json", "audit.json", "lock.json"))
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    audit_path.write_text(json.dumps(audit), encoding="utf-8")
    lock = freeze(plan_path, audit_path, lock_path)
    verify(plan, audit, lock)
    with pytest.raises(FileExistsError):
        freeze(plan_path, audit_path, lock_path)
    changed_plan = copy.deepcopy(plan)
    changed_plan["signal"] = "different rule"
    with pytest.raises(ValueError, match="plan changed"):
        verify(changed_plan, audit, lock)
    changed_audit = copy.deepcopy(audit)
    changed_audit["files"][0]["sha256"] = "different"
    with pytest.raises(ValueError, match="source data changed"):
        verify(plan, changed_audit, lock)
