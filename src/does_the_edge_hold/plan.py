"""Freeze research choices before any empirical grid run."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


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
    if plan["configuration_count"] != 9:
        raise ValueError("configuration count changed; revise the plan explicitly")
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
