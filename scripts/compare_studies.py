"""Compare saved research outcomes; execution metadata is explicitly separate."""
import argparse
import json
import math
from pathlib import Path
import pandas as pd

EXCLUDED_ROW_FIELDS = {"run_id", "execution_sha256", "causal_check"}

def compare_value(a, b, path):
    if isinstance(a, dict):
        if set(a) != set(b): raise AssertionError(f"fields differ at {path}: {set(a) ^ set(b)}")
        for key in a: compare_value(a[key], b[key], path + "/" + str(key))
    elif isinstance(a, list):
        if len(a) != len(b): raise AssertionError(f"length differs at {path}")
        for i, (left, right) in enumerate(zip(a, b)): compare_value(left, right, path + f"/{i}")
    elif isinstance(a, (int, float)) and not isinstance(a, bool):
        if not isinstance(b, (int, float)) or not math.isclose(a, b, rel_tol=1e-10, abs_tol=2e-8):
            raise AssertionError(f"number differs at {path}: {a}, {b}")
    elif a != b:
        raise AssertionError(f"value differs at {path}: {a!r}, {b!r}")

def compare(left, right, markets):
    receipt = {"scope": "all outcome fields, uncertainty, ranks, carried pick and available daily panels",
               "excluded_row_fields": sorted(EXCLUDED_ROW_FIELDS), "tolerance": {"relative": 1e-10, "absolute": 2e-8}, "markets": {}}
    for market in markets:
        a, b = [json.loads((Path(root) / market / "results.json").read_text()) for root in (left, right)]
        for name in ("runs", "common_runs"):
            if name not in a: continue
            sort_key = lambda r: (r["config_id"], r["scenario"], r["period"])
            clean = lambda rows: [{k: v for k, v in r.items() if k not in EXCLUDED_ROW_FIELDS} for r in sorted(rows, key=sort_key)]
            compare_value(clean(a[name]), clean(b[name]), market + "/" + name)
        for name in ("winner_uncertainty", "rank_changes", "walk_forward", "selected_config_from_primary"):
            if name in a: compare_value(a[name], b[name], market + "/" + name)
        panels = []
        for name in ("daily-pnl.csv", "daily-pnl-all-scenarios.csv"):
            paths = [Path(root) / market / name for root in (left, right)]
            if all(p.exists() for p in paths):
                panels.append(name)
                frames = [pd.read_csv(p, index_col=0) for p in paths]
                pd.testing.assert_frame_equal(*frames, check_exact=False, rtol=1e-10, atol=2e-8)
        receipt["markets"][market] = {"matched": True, "result_rows": len(a["runs"]),
                                     "common_rows": len(a.get("common_runs", [])), "panels": panels}
    return receipt

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--left", type=Path, required=True)
    parser.add_argument("--right", type=Path, required=True)
    parser.add_argument("--markets", nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = compare(args.left, args.right, args.markets)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
