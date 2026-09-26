"""Build local roll schedules from Databento's free symbology resolver."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd

from .data import sha256_file
from .roll_gate import ROLL_POLICY


def write_resolution(response: dict, audit: dict, provenance: dict,
                     destination: str | Path) -> Path:
    """Save resolver output locally; never place it under the tracked reports dir."""
    if response.get("status") != 0 or response.get("partial") or response.get("not_found"):
        raise ValueError("symbol resolution is partial or failed")
    if response.get("stype_in") != "continuous" or response.get("stype_out") != "raw_symbol":
        raise ValueError("resolution must map continuous to raw contract symbols")
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    audits = {row["market"]: row for row in audit["files"] if row["resolution"] == "1m"}
    origins = {row["market"]: row for row in provenance["markets"]}
    manifest = {"method": "databento.symbology.resolve", "dataset": "GLBX.MDP3",
                "roll_policy": ROLL_POLICY, "markets": {}}
    for market in ("NQ", "ES", "YM", "GC", "CL"):
        if not origins[market].get("verified_match"):
            raise ValueError(f"{market} export origin is not verified")
        root = origins[market]["selected_root"]
        symbol = market + "." + root[-2] + ".0"
        intervals = response.get("result", {}).get(symbol)
        if not intervals or len(intervals) < 2:
            raise ValueError(f"{market} has no usable date-to-contract intervals")
        starts = pd.to_datetime([part["d0"] for part in intervals], utc=True)
        ends = pd.to_datetime([part["d1"] for part in intervals], utc=True)
        contracts = [str(part["s"]) for part in intervals]
        if not starts.is_monotonic_increasing or starts.duplicated().any():
            raise ValueError(f"{market} mapping dates overlap")
        if any(end <= start for start, end in zip(starts, ends)):
            raise ValueError(f"{market} mapping has empty intervals")
        if any(starts[i + 1] != ends[i] for i in range(len(starts) - 1)):
            raise ValueError(f"{market} mapping has a date gap")
        first = pd.Timestamp(audits[market]["first_utc"])
        last = pd.Timestamp(audits[market]["last_utc"])
        if starts[0] > first or ends[-1] <= last:
            raise ValueError(f"{market} mapping does not cover its minute export")
        schedule = pd.DataFrame({"effective_at": starts, "contract": contracts})
        file = destination / f"{market}_rolls.csv"
        schedule.to_csv(file, index=False)
        manifest["markets"][market] = {
            "continuous_symbol": symbol,
            "source_sha256": audits[market]["sha256"],
            "schedule_sha256": sha256_file(file),
            "coverage_end": ends[-1].isoformat(),
            "roll_count": int(schedule["contract"].ne(schedule["contract"].shift()).sum()) - 1,
        }
    output = destination / "evidence.json"
    output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return output


def resolve_free(audit: dict, provenance: dict, destination: str | Path) -> Path:
    """Call only symbology.resolve. No paid time-series request is made."""
    key = os.getenv("DATABENTO_API_KEY")
    if not key:
        raise ValueError("set DATABENTO_API_KEY for the free mapping lookup")
    import databento as db

    origins = {row["market"]: row for row in provenance["markets"]}
    symbols = [market + "." + origins[market]["selected_root"][-2] + ".0"
               for market in ("NQ", "ES", "YM", "GC", "CL")]
    minutes = [row for row in audit["files"] if row["resolution"] == "1m"]
    start = min(pd.Timestamp(row["first_utc"]) for row in minutes).date().isoformat()
    end = (max(pd.Timestamp(row["last_utc"]) for row in minutes) +
           pd.Timedelta(days=1)).date().isoformat()
    response = db.Historical(key).symbology.resolve(
        dataset="GLBX.MDP3", symbols=symbols, stype_in="continuous",
        stype_out="raw_symbol", start_date=start, end_date=end)
    return write_resolution(response, audit, provenance, destination)
