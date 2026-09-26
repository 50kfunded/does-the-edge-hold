"""Per-market identity, policy and quality gates."""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
from .data import sha256_file
from .rolls import read_schedule
ROLL_POLICY = "advance instruction; first old-contract open after executable time plus delay, before deadline; new-contract open after boundary plus delay"
ALLOWED_METHODS = {"databento.symbology.resolve", "manual_reviewed"}

def universe(plan: dict) -> dict:
    primary = plan.get("primary_market", "NQ")
    checks = plan.get("checks", ["ES", "GC", "CL"])
    separate = plan.get("separate_check", "YM")
    return plan.get("universe", {"primary": primary, "required": [primary],
        "optional": checks + ([separate] if separate else []),
        "allowed_exclusions": checks + ([separate] if separate else []),
        "blocked_primary": "stop; never select a replacement primary"})

def read_instructions(path: str | Path) -> pd.DataFrame:
    frame = pd.read_csv(path, dtype={"old_contract": str, "new_contract": str})
    needed = {"known_at", "executable_at", "deadline", "effective_at", "old_contract", "new_contract"}
    if not needed.issubset(frame):
        raise ValueError("instruction file lacks required columns")
    for name in ("known_at", "executable_at", "deadline", "effective_at"):
        frame[name] = pd.to_datetime(frame[name], utc=True, errors="raise")
    if frame.isna().any().any() or frame.effective_at.duplicated().any():
        raise ValueError("instructions have missing or duplicated values")
    if not ((frame.known_at <= frame.executable_at) & (frame.executable_at < frame.deadline) &
            (frame.deadline <= frame.effective_at)).all():
        raise ValueError("instruction timing is not causal")
    return frame

def assess(audit: dict, provenance: dict, mapping_root: str | Path | None = None,
           *, plan: dict | None = None) -> dict:
    roles = universe(plan or {})
    markets = list(dict.fromkeys(roles["required"] + roles["optional"]))
    audits = {r["market"]: r for r in audit["files"] if r["resolution"] == "1m"}
    origins = {r["market"]: r for r in provenance["markets"]}
    root = Path(mapping_root) if mapping_root is not None else None
    manifest, common = None, []
    if root is None or not (root / "evidence.json").is_file():
        common.append("date-valid instrument identity and advance roll evidence are absent")
    else:
        try:
            manifest = json.loads((root / "evidence.json").read_text(encoding="utf-8"))
            if manifest.get("method") not in ALLOWED_METHODS:
                common.append("mapping method is not reviewed")
            if manifest.get("roll_policy") != ROLL_POLICY:
                common.append("advance roll policy has not been reviewed")
            if manifest.get("method") == "databento.symbology.resolve":
                if not (root / "resolution.json").is_file() or sha256_file(root / "resolution.json") != manifest.get("response_sha256"):
                    common.append("original resolver response is missing or changed")
        except (ValueError, OSError) as exc:
            common.append(f"mapping evidence could not be read: {exc}")
    per_market = {}
    quality = (plan or {}).get("quality", {})
    for market in markets:
        problems = list(common)
        a, origin = audits.get(market), origins.get(market)
        if a is None or origin is None or not origin.get("verified_match"):
            problems.append("export could not be matched to its continuous cache")
        if a is not None:
            for field in ("duplicate_timestamps", "out_of_order_timestamps", "invalid_ohlc", "nonpositive_volume"):
                if a.get(field, 0):
                    problems.append(f"quality gate: {field}")
            if sum(a.get("missing_values", {}).values()):
                problems.append("quality gate: missing values")
            if quality.get("maximum_gap_seconds") is not None and a.get("maximum_gap_seconds", 0) > quality["maximum_gap_seconds"]:
                problems.append("gap exceeds the protocol limit")
        if manifest is not None and a is not None and origin is not None:
            meta = manifest.get("markets", {}).get(market, {})
            try:
                symbol = market + "." + origin["selected_root"][-2] + ".0"
                if meta.get("continuous_symbol") != symbol or meta.get("source_sha256") != a["sha256"]:
                    raise ValueError("identity evidence is for a different source")
                file = root / f"{market}_rolls.csv"
                if not file.is_file() or sha256_file(file) != meta.get("schedule_sha256"):
                    raise ValueError("identity file/hash mismatch")
                schedule = read_schedule(file)
                if "end_at" not in schedule:
                    raise ValueError("identity intervals need explicit exclusive ends")
                if schedule.effective_at.iloc[0] > pd.Timestamp(a["first_utc"]) or schedule.end_at.iloc[-1] <= pd.Timestamp(a["last_utc"]):
                    raise ValueError("mapping does not cover all bars")
                instruction_path = root / f"{market}_instructions.csv"
                if not instruction_path.is_file() or sha256_file(instruction_path) != meta.get("instructions_sha256"):
                    raise ValueError("advance instructions/file hash are absent")
                instructions = read_instructions(instruction_path)
                policy = meta.get("policy_evidence", {})
                policy_source = root / f"{market}_policy-source.json"
                if policy.get("kind") != "advance_schedule" or not policy.get("reviewed") or not policy_source.is_file() or sha256_file(policy_source) != policy.get("sha256"):
                    raise ValueError("independent advance-policy evidence is absent; date mapping alone is insufficient")
                changes = schedule.loc[schedule.contract.ne(schedule.contract.shift())].iloc[1:]
                if list(changes.effective_at) != list(instructions.effective_at):
                    raise ValueError("instructions do not cover identity transitions")
                for r in instructions.itertuples():
                    at = schedule.index[schedule.effective_at == r.effective_at][0]
                    if str(schedule.contract.iloc[at - 1]) != r.old_contract or str(schedule.contract.iloc[at]) != r.new_contract:
                        raise ValueError("instruction contracts disagree with identities")
            except (ValueError, KeyError, OSError, IndexError) as exc:
                problems.append(str(exc))
        per_market[market] = {"ready": not problems, "problems": problems,
                              "role": "required" if market in roles["required"] else "optional"}
    included = [m for m, item in per_market.items() if item["ready"]]
    excluded = {m: item["problems"] for m, item in per_market.items() if not item["ready"]}
    forbidden = [m for m in excluded if m not in roles["allowed_exclusions"]]
    primary_blocked = roles["primary"] not in included
    ready = not forbidden and not primary_blocked
    return {"status": "ready" if ready else "unresolved", "roll_policy": ROLL_POLICY,
            "markets": per_market, "included": included, "excluded": excluded,
            "primary": roles["primary"], "primary_blocked": primary_blocked,
            "reasons": [f"{m}: {p}" for m, problems in excluded.items() for p in problems],
            "scope": "declared minute-bar universe; second-bar provenance is separate"}

def require_ready(decision: dict) -> None:
    if decision["status"] != "ready":
        raise RuntimeError("empirical futures P&L blocked by roll gate: " + "; ".join(decision["reasons"]))

