"""Check the tracked files and reachable history before publishing."""

import json
from pathlib import Path
import re
import subprocess


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True, encoding="utf-8").strip()


def forbidden(path: str) -> bool:
    lower = path.lower()
    return (lower.endswith((".parquet", ".dbn", ".dbn.zst", ".zst", ".zip")) or
            lower.endswith("/.env") or lower == ".env" or
            lower.startswith(("runs/", "cache/", "data/")) or
            lower.endswith(("_rolls.csv", "/symbology.json", "/evidence.json")))


def main() -> None:
    files = git("ls-files").splitlines()
    bad = [path for path in files if forbidden(path)]
    if bad:
        raise SystemExit(f"local data files are tracked: {bad}")
    for path in files:
        if re.search(rb"db-[A-Za-z0-9]{24,}", Path(path).read_bytes()):
            raise SystemExit(f"possible Databento key in {path}")
    for line in git("rev-list", "--objects", "--all").splitlines():
        parts = line.split(" ", 1)
        if len(parts) == 2 and forbidden(parts[1]):
            raise SystemExit(f"local data file appears in history: {parts[1]}")
    revisions = git("rev-list", "--all", "--", "reports/local-data-audit.json").splitlines()
    for revision in revisions:
        report = json.loads(git("show", f"{revision}:reports/local-data-audit.json"))
        for source in report["files"]:
            if source.get("largest_changes") or source.get("largest_gaps"):
                raise SystemExit("per-bar investigation samples appear in public audit history")
    print(f"checked {len(files)} tracked files and reachable history; no vendor bars, mapping files or audit samples found")


if __name__ == "__main__":
    main()
