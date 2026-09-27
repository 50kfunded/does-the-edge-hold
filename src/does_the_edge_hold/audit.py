"""Stream a source-file audit without changing the source."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import heapq
import json
import sys
import time

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import psutil
from pandas.tseries.holiday import USFederalHolidayCalendar

from .data import iter_parquet, sha256_file, source_path


TICKS = {"NQ": 0.25, "ES": 0.25, "YM": 1.0, "GC": 0.1, "CL": 0.01}
HOLIDAYS = set(USFederalHolidayCalendar().holidays("2016-01-01", "2027-01-01").date)


def public_summary(report: dict) -> dict:
    """Keep aggregate metadata for publishing; investigation samples stay local."""
    import copy

    summary = copy.deepcopy(report)
    for source in summary["files"]:
        source.pop("largest_changes", None)
        source.pop("largest_gaps", None)
    summary["publication_scope"] = "aggregate metadata only; per-bar investigation samples stay local"
    return summary


def _weekly_open(local: pd.DatetimeIndex) -> np.ndarray:
    day = local.dayofweek.to_numpy()
    hour = local.hour.to_numpy()
    return ~(((day == 4) & (hour >= 17)) | (day == 5) |
             ((day == 6) & (hour < 18)) | (hour == 17))


def classify_gap(previous: pd.Timestamp, current: pd.Timestamp,
                 resolution: str) -> tuple[str, int]:
    """Use regular Globex hours; holiday and no-trade labels stay tentative."""
    step = pd.Timedelta(seconds=1 if resolution == "1s" else 60)
    missing = int((current - previous) // step) - 1
    if missing <= (300 if resolution == "1s" else 5):
        return "short_no_trade_or_missing_candidate", 0
    if current - previous > pd.Timedelta(days=7):
        return "long_gap_investigate", 0
    interior = pd.date_range(previous + pd.Timedelta(minutes=1),
                             current - pd.Timedelta(seconds=1), freq="min", tz="UTC")
    if len(interior) == 0:
        return "open_gap_investigate", 0
    local = interior.tz_convert("America/New_York")
    open_minutes = int(_weekly_open(local).sum())
    closed_minutes = len(local) - open_minutes
    if closed_minutes > 0 and open_minutes <= 2:
        return "regular_weekly_closure_candidate", open_minutes
    if any(day in HOLIDAYS for day in set(local.date)) or (
        (current - previous) >= pd.Timedelta(hours=60) and
        5 in set(local.dayofweek.to_numpy())
    ):
        return "holiday_or_special_hours_candidate", open_minutes
    return "open_gap_investigate", open_minutes


def audit_file(path: str | Path, resolution: str, market: str,
               *, batch_size: int = 65_536) -> dict:
    started = time.perf_counter()
    path = Path(path)
    parquet = pq.ParquetFile(path)
    row_count = 0
    process = psutil.Process()
    peak_rss_bytes = process.memory_info().rss
    first = last = None
    peak_batch_rows = 0
    previous_ns = None
    previous_close = None
    years = Counter()
    missing = Counter()
    gap_classes = Counter()
    gap_missing_slots = Counter()
    duplicate = out_of_order = invalid_ohlc = nonpositive_volume = 0
    large_change_count = 0
    largest_gaps: list[tuple[int, int, str, str, str, int]] = []
    largest_changes: list[tuple[float, str, float, float]] = []
    step_ns = 1_000_000_000 if resolution == "1s" else 60_000_000_000
    for batch in iter_parquet(path, batch_size=batch_size):
        row_count += len(batch)
        peak_rss_bytes = max(peak_rss_bytes, process.memory_info().rss)
        peak_batch_rows = max(peak_batch_rows, len(batch))
        stamps = batch["ts"]
        if stamps.notna().any():
            batch_min, batch_max = stamps.min(), stamps.max()
            first = batch_min if first is None else min(first, batch_min)
            last = batch_max if last is None else max(last, batch_max)
        years.update(stamps.dt.year.value_counts().to_dict())
        for col in ("ts", "open", "high", "low", "close", "volume"):
            missing[col] += int(batch[col].isna().sum())
        op = batch["open"].to_numpy(dtype=float)
        hi = batch["high"].to_numpy(dtype=float)
        lo = batch["low"].to_numpy(dtype=float)
        cl = batch["close"].to_numpy(dtype=float)
        vol = batch["volume"].to_numpy(dtype=float)
        valid = np.isfinite(op) & np.isfinite(hi) & np.isfinite(lo) & np.isfinite(cl)
        invalid_ohlc += int(np.sum(valid & ((hi < np.maximum.reduce([op, cl, lo])) |
                                              (lo > np.minimum.reduce([op, cl, hi])))))
        nonpositive_volume += int(np.sum(np.isfinite(vol) & (vol <= 0)))
        ns = stamps.array.asi8
        nat = np.iinfo(np.int64).min
        before = np.r_[previous_ns if previous_ns is not None else nat, ns[:-1]]
        valid_pair = (ns != nat) & (before != nat)
        delta = np.zeros(len(ns), dtype=np.int64)
        np.subtract(ns, before, out=delta, where=valid_pair)
        duplicate += int(np.sum(valid_pair & (delta == 0)))
        out_of_order += int(np.sum(valid_pair & (delta < 0)))
        gap_indices = np.flatnonzero(valid_pair & (delta > step_ns))
        gap_slots = delta[gap_indices] // step_ns - 1
        short_limit = 300 if resolution == "1s" else 5
        short = gap_slots <= short_limit
        short_count = int(short.sum())
        gap_classes["short_no_trade_or_missing_candidate"] += short_count
        gap_missing_slots["short_no_trade_or_missing_candidate"] += int(gap_slots[short].sum())
        for index in gap_indices[~short]:
            previous = pd.Timestamp(int(before[index]), tz="UTC")
            current = pd.Timestamp(int(ns[index]), tz="UTC")
            label, open_minutes = classify_gap(previous, current, resolution)
            slots = int(delta[index] // step_ns) - 1
            gap_classes[label] += 1
            gap_missing_slots[label] += slots
            item = (slots, int(ns[index]), previous.isoformat(), current.isoformat(), label, open_minutes)
            if len(largest_gaps) < 20:
                heapq.heappush(largest_gaps, item)
            elif item > largest_gaps[0]:
                heapq.heapreplace(largest_gaps, item)
        prior = np.r_[previous_close if previous_close is not None else cl[0], cl[:-1]]
        changes = np.abs(cl - prior)
        threshold = np.maximum(0.01 * np.abs(prior), 100 * TICKS[market])
        flagged = np.flatnonzero(stamps.notna().to_numpy() & np.isfinite(changes) & (changes >= threshold))
        large_change_count += len(flagged)
        for index in flagged:
            item = (float(changes[index]), stamps.iloc[index].isoformat(),
                    float(prior[index]), float(cl[index]))
            if len(largest_changes) < 20:
                heapq.heappush(largest_changes, item)
            elif item > largest_changes[0]:
                heapq.heapreplace(largest_changes, item)
        previous_ns = int(ns[-1]) if ns[-1] != nat else None
        previous_close = float(cl[-1])
    peak_rss_bytes = max(peak_rss_bytes, process.memory_info().rss)
    return {
        "path": str(path), "sha256": sha256_file(path), "bytes": path.stat().st_size,
        "resolution": resolution, "market": market,
        "schema": {field.name: str(field.type) for field in parquet.schema_arrow},
        "row_count": row_count, "footer_row_count": parquet.metadata.num_rows,
        "first_utc": first.isoformat() if first is not None else None,
        "last_utc": last.isoformat() if last is not None else None,
        "rows_by_year": dict(sorted(years.items())),
        "duplicate_timestamps": duplicate, "out_of_order_timestamps": out_of_order,
        "missing_values": dict(missing), "invalid_ohlc": invalid_ohlc,
        "nonpositive_volume": nonpositive_volume,
        "gap_counts": dict(gap_classes), "missing_slots_by_gap_class": dict(gap_missing_slots),
        "largest_gaps": [dict(missing_slots=n, previous_utc=p, current_utc=c,
                               class_=label, regular_open_minutes=opened)
                          for n, _, p, c, label, opened in sorted(largest_gaps, reverse=True)],
        "large_change_rule": "absolute close change >= max(1% of prior absolute close, 100 ticks)",
        "large_change_count": large_change_count,
        "largest_changes": [dict(abs_change=value, at_utc=at, prior_close=prior,
                                 close=close, label="investigate")
                            for value, at, prior, close in sorted(largest_changes, reverse=True)],
        "peak_batch_rows": peak_batch_rows,
        "sampled_peak_process_rss_bytes": peak_rss_bytes,
        "runtime_seconds": round(time.perf_counter() - started, 2),
        "session_rule": "regular 18:00-17:00 America/New_York weekly template; holiday hours not verified",
        "gap_note": "a missing OHLCV bar may have had no trade; a label is a candidate, not proof",
    }


def audit_sources(root: str | Path, *, include_seconds: bool = True, markets=None, include_semantic=False) -> dict:
    files = [(market, "1m") for market in (markets if markets is not None else ("NQ", "ES", "YM", "GC", "CL"))]
    if include_seconds:
        files.append(("NQ", "1s"))
    results = []
    for market, resolution in files:
        print(f"auditing {market} {resolution}...", file=sys.stderr, flush=True)
        path = source_path(root, market, resolution)
        result = audit_file(path, resolution, market)
        if include_semantic:
            from .semantic import semantic_file
            try:
                result["semantic"] = semantic_file(path)
            except ValueError as exc:
                result["semantic_error"] = str(exc)
        results.append(result)
    return {"generated_utc": datetime.now(timezone.utc).isoformat(),
            "source_root": str(Path(root).resolve()),
            "files": results,
            "roll_gate": "unresolved until date-to-contract mapping is verified",
            "overlap_note": "NQ second and minute files overlap; aggregates are not independent markets"}


def write_audit(report: dict, destination: str | Path) -> None:
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
