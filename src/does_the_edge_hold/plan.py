"""Freeze research choices before any empirical grid run."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import math
import pandas as pd

def validate(plan: dict) -> None:
    import importlib
    from .signals import REGISTRY
    for module in plan.get("extensions", []):
        extension = importlib.import_module(module)
        if not any(fn.__module__ == module for fn in REGISTRY.values()):
            extension.register()
    from .signals import grid_from_plan
    from .daily_clock import DailyClock
    from .roll_gate import universe
    if not isinstance(plan.get("version"), int) or plan["version"] < 1:
        raise ValueError("protocol version must be positive")
    grid_from_plan(plan)
    roles = universe(plan)
    required, optional = roles["required"], roles["optional"]
    if roles["primary"] not in required or len(set(required + optional)) != len(required + optional):
        raise ValueError("primary/required/optional roles are inconsistent")
    if not set(roles["allowed_exclusions"]).issubset(optional):
        raise ValueError("only optional markets may be excluded")
    previous = None
    for name in ("development", "validation", "historical_final"):
        start, end = pd.to_datetime(plan["splits_utc"][name], utc=True)
        if pd.isna(start) or pd.isna(end) or start >= end or (previous is not None and start != previous):
            raise ValueError("split dates must be ordered, nonempty and contiguous")
        previous = end
    if not plan.get("prior_exposure"):
        raise ValueError("prior data exposure must be disclosed")
    execution = plan["execution"]
    capital = execution["starting_capital_usd_per_market"]
    if not math.isfinite(capital) or capital <= 0:
        raise ValueError("capital must be positive and finite")
    scenarios = execution["scenarios"]
    names = [s["name"] for s in scenarios]
    if "base" not in names or len(set(names)) != len(names):
        raise ValueError("scenario names must be unique and include base")
    for s in scenarios:
        for field in ("commission_usd_per_side", "slippage_ticks_per_side", "delay_minutes", "fee_bps", "slippage_bps"):
            if field not in s:
                continue
            if not math.isfinite(s[field]) or s[field] < 0:
                raise ValueError("costs and delays must be finite and nonnegative")
        if int(s["delay_minutes"]) != s["delay_minutes"]:
            raise ValueError("delay must be an integer minute count")
    if not isinstance(plan["selection"]["minimum_entry_trades"], int) or plan["selection"]["minimum_entry_trades"] < 1:
        raise ValueError("selection trade threshold must be positive")
    DailyClock.from_plan(plan)
    metric = plan["selection"].get("metric")
    if metric is not None and metric not in (
        "net Sharpe on daily account-capital returns in the base scenario",
        "development net daily account-capital Sharpe in base"):
        raise ValueError("unsupported selection metric; this evaluator selects net daily Sharpe")
    lengths = plan.get("statistics", {}).get("block_lengths", [3, 5, 10])
    if not lengths or any(isinstance(n, bool) or not isinstance(n, int) or n < 1 for n in lengths):
        raise ValueError("block lengths must be positive integers")


def _digest(value: object) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def source_hashes(audit: dict) -> dict[str, str]:
    return {f"{item['market']}_{item['resolution']}": item["sha256"]
            for item in audit["files"]}


def freeze(plan_path: str | Path, audit_path: str | Path,
           lock_path: str | Path) -> dict:
    plan = json.loads(Path(plan_path).read_text(encoding="utf-8"))
    audit = json.loads(Path(audit_path).read_text(encoding="utf-8"))
    validate(plan)
    lock = {"plan_sha256": _digest(plan), "source_hashes": source_hashes(audit),
            "frozen_utc": datetime.now(timezone.utc).isoformat(),
            "version": plan["version"]}
    path = Path(lock_path)
    if path.exists():
        raise FileExistsError("a frozen lock exists; document a revision before replacing it")
    path.write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return lock


def verify(plan: dict, audit: dict, lock: dict) -> None:
    if _digest(plan) != lock["plan_sha256"]:
        raise ValueError("research plan changed after it was frozen")
    if source_hashes(audit) != lock["source_hashes"]:
        raise ValueError("source data changed after the research plan was frozen")
    validate(plan)
