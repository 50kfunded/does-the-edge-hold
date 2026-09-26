"""An explicit gate between descriptive data audit and empirical futures P&L."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .data import sha256_file
from .rolls import read_schedule


ROLL_POLICY = "exit at open of final old-contract minute; re-enter at open of first new-contract minute"
ALLOWED_METHODS = {"databento.symbology.resolve", "manual_reviewed"}


def assess(audit: dict, provenance: dict, mapping_root: str | Path | None = None) -> dict:
    """Return a reviewable decision; no mapping means no empirical P&L."""
    reasons = []
    per_market = {}
    audits = {row["market"]: row for row in audit["files"] if row["resolution"] == "1m"}
    origins = {row["market"]: row for row in provenance["markets"]}
    manifest = None
    root = Path(mapping_root) if mapping_root is not None else None
    if root is None or not (root / "evidence.json").is_file():
        reasons.append("date-to-contract mapping and its evidence are absent")
    else:
        try:
            manifest = json.loads((root / "evidence.json").read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            reasons.append(f"mapping evidence could not be read: {exc}")
    if manifest is not None and manifest.get("method") not in ALLOWED_METHODS:
        reasons.append("mapping method is not documented as resolver output or manually reviewed")
    if manifest is not None and manifest.get("roll_policy") != ROLL_POLICY:
        reasons.append("roll policy does not match the implementation")
    for market in ("NQ", "ES", "YM", "GC", "CL"):
        a, origin = audits.get(market), origins.get(market)
        problems = []
        if a is None or origin is None or not origin.get("verified_match"):
            problems.append("export could not be matched to its continuous cache")
        if origin is not None and origin.get("selected_root", "")[-2:-1] == "v":
            problems.append("volume-ranked mapping alone cannot justify an exit at the final old-contract minute open; the current runner needs a reviewed policy extension with additional contract prices or advance schedule evidence")
        if manifest is None:
            problems.append("no verified mapping supplied")
        elif a is not None and origin is not None:
            meta = manifest.get("markets", {}).get(market)
            if not isinstance(meta, dict):
                problems.append("market mapping is missing")
            else:
                expected_symbol = (market + "." + origin["selected_root"][-2] + ".0")
                if meta.get("continuous_symbol") != expected_symbol:
                    problems.append("continuous symbol does not match the source cache")
                if meta.get("source_sha256") != a["sha256"]:
                    problems.append("mapping evidence is for a different source file")
                file = root / f"{market}_rolls.csv"
                if not file.is_file() or meta.get("schedule_sha256") != sha256_file(file):
                    problems.append("schedule file or hash does not match its evidence")
                else:
                    try:
                        schedule = read_schedule(file)
                        first = pd.Timestamp(a["first_utc"])
                        last = pd.Timestamp(a["last_utc"])
                        end = pd.to_datetime(meta["coverage_end"], utc=True)
                        if schedule["effective_at"].iloc[0] > first or end <= last:
                            problems.append("mapping does not cover all source bars")
                        if len(schedule) < 2:
                            problems.append("long series has no documented contract changes")
                    except (ValueError, KeyError) as exc:
                        problems.append(f"schedule is invalid: {exc}")
        per_market[market] = {"ready": not problems, "problems": problems}
        reasons.extend(f"{market}: {problem}" for problem in problems)
    return {"status": "ready" if not reasons else "unresolved",
            "roll_policy": ROLL_POLICY, "markets": per_market,
            "reasons": reasons,
            "scope": "five minute-bar exports; NQ second bars require a separate source match"}


def require_ready(decision: dict) -> None:
    if decision["status"] != "ready":
        raise RuntimeError("empirical futures P&L blocked by roll gate: " + "; ".join(decision["reasons"]))
