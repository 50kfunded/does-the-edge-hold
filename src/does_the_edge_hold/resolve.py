"""Build local roll schedules from Databento's free symbology resolver."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd

from .data import sha256_file


def intervals(response: dict, symbol: str, stype_in: str, stype_out: str) -> pd.DataFrame:
    if response.get("status") != 0 or response.get("partial") or response.get("not_found"):
        raise ValueError("symbol resolution is partial or failed")
    if (response.get("stype_in"), response.get("stype_out")) != (stype_in, stype_out):
        raise ValueError(f"resolution must map {stype_in} to {stype_out}")
    parts = response.get("result", {}).get(symbol)
    if not parts:
        raise ValueError(f"no intervals for {symbol}")
    out = pd.DataFrame(parts).rename(columns={"d0": "effective_at", "d1": "end_at", "s": "contract"})
    out = out[["effective_at", "end_at", "contract"]]
    for key in ("effective_at", "end_at"):
        out[key] = pd.to_datetime(out[key], utc=True, errors="raise")
    if out.isna().any().any() or out["contract"].astype(str).str.strip().eq("").any():
        raise ValueError("missing identity or date")
    if not out.effective_at.is_monotonic_increasing or out.effective_at.duplicated().any():
        raise ValueError("mapping starts must increase")
    if (out.end_at <= out.effective_at).any():
        raise ValueError("mapping has empty intervals")
    if any(out.effective_at.iloc[i + 1] != out.end_at.iloc[i] for i in range(len(out) - 1)):
        raise ValueError("mapping has a date gap or overlap")
    out["contract"] = out.contract.astype(str)
    return out


def with_raw_symbols(ids: pd.DataFrame, response: dict) -> pd.DataFrame:
    rows = []
    for part in ids.itertuples(index=False):
        raw = intervals(response, part.contract, "instrument_id", "raw_symbol")
        cursor = part.effective_at
        for r in raw.itertuples(index=False):
            start, end = max(part.effective_at, r.effective_at), min(part.end_at, r.end_at)
            if end <= start:
                continue
            if start != cursor:
                raise ValueError("raw-symbol mapping is incomplete or incompatible")
            rows.append({"effective_at": start, "end_at": end, "contract": r.contract,
                         "instrument_id": part.contract})
            cursor = end
        if cursor != part.end_at:
            raise ValueError("raw-symbol mapping is incomplete or incompatible")
    return pd.DataFrame(rows)


def write_resolution(response: dict, audit: dict, provenance: dict,
                     destination: str | Path, *, raw_response: dict | None = None,
                     request: dict | None = None, retrieved_at: str | None = None) -> Path:
    """Save resolver output locally; never place it under the tracked reports dir."""
    destination = Path(destination)
    audits = {row["market"]: row for row in audit["files"] if row["resolution"] == "1m"}
    origins = {row["market"]: row for row in provenance["markets"]}
    prepared = {}
    for market in audits:
        if not origins[market].get("verified_match"):
            raise ValueError(f"{market} export origin is not verified")
        root = origins[market]["selected_root"]
        symbol = market + "." + root[-2] + ".0"
        schedule = intervals(response, symbol, "continuous", "instrument_id")
        if not schedule.contract.str.fullmatch(r"\d+").all():
            raise ValueError("instrument IDs must be numeric")
        if raw_response is not None:
            schedule = with_raw_symbols(schedule, raw_response)
        first = pd.Timestamp(audits[market]["first_utc"])
        last = pd.Timestamp(audits[market]["last_utc"])
        if schedule.effective_at.iloc[0] > first or schedule.end_at.iloc[-1] <= last:
            raise ValueError(f"{market} mapping does not cover its minute export")
        prepared[market] = (symbol, schedule)
    destination.mkdir(parents=True, exist_ok=False)
    for name, value in (("resolution.json", response), ("raw-resolution.json", raw_response)):
        if value is not None:
            (destination / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    from datetime import datetime, timezone
    manifest = {"method": "databento.symbology.resolve", "dataset": "GLBX.MDP3",
                "retrieved_at": retrieved_at or datetime.now(timezone.utc).isoformat(),
                "request": request or {"stype_in": "continuous", "stype_out": "instrument_id",
                                       "symbols": [v[0] for v in prepared.values()]},
                "response_sha256": sha256_file(destination / "resolution.json"),
                "policy_status": "requires separate advance instruction evidence", "markets": {}}
    if raw_response is not None:
        manifest["raw_response_sha256"] = sha256_file(destination / "raw-resolution.json")
    for market, (symbol, schedule) in prepared.items():
        file = destination / f"{market}_rolls.csv"
        schedule.to_csv(file, index=False)
        manifest["markets"][market] = {
            "continuous_symbol": symbol,
            "source_sha256": audits[market]["sha256"],
            "schedule_sha256": sha256_file(file),
            "coverage_end": schedule.end_at.iloc[-1].isoformat(),
            "identity_type": "raw_symbol" if raw_response else "instrument_id",
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
        stype_out="instrument_id", start_date=start, end_date=end)
    return write_resolution(response, audit, provenance, destination,
                            request={"dataset": "GLBX.MDP3", "symbols": symbols,
                                     "stype_in": "continuous", "stype_out": "instrument_id",
                                     "start_date": start, "end_date": end})
