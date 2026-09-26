"""Check which local cached continuous series produced each export."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import re

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from .data import sha256_file, source_path


def cache_candidates(cache_root: str | Path, market: str) -> dict[str, list[Path]]:
    roots: dict[str, list[Path]] = defaultdict(list)
    pattern = re.compile(rf"^databento_({market}[cv]\d)_ohlcv-1m_.*_ctx\.parquet$")
    for path in Path(cache_root).glob(f"databento_{market}*_ohlcv-1m_*_ctx.parquet"):
        match = pattern.match(path.name)
        if match:
            roots[match.group(1)].append(path)
    return {key: sorted(value) for key, value in roots.items()}


def verify_minute_origin(bars_root: str | Path, cache_root: str | Path,
                         market: str, *, original_precision=False) -> dict:
    """Recreate the builder's cache choice and compare every exported bar."""
    market = market.upper()
    candidates = cache_candidates(cache_root, market)
    if not candidates:
        return {"market": market, "verified_match": False, "reason": "cache slices missing"}
    selected = max(candidates, key=lambda root: sum(p.stat().st_size for p in candidates[root]))
    sources = candidates[selected]
    parts = [pd.read_parquet(path) for path in sources]
    reconstructed = pd.concat(parts)
    reconstructed = reconstructed[~reconstructed.index.duplicated(keep="last")].sort_index()
    export = pd.read_parquet(source_path(bars_root, market))
    same_rows = len(reconstructed) == len(export)
    same_times = same_rows and reconstructed.index.equals(export.index)
    same_values = same_times
    if same_times:
        for name in ("open", "high", "low", "close", "volume"):
            dtype = None if original_precision else "uint32" if name == "volume" else "float32"
            same_values &= bool(np.array_equal(reconstructed[name].to_numpy(dtype=dtype),
                                                export[name].to_numpy(dtype=dtype), equal_nan=True))
            if original_precision:
                same_values &= reconstructed[name].dtype == export[name].dtype
    return {
        "market": market, "selected_root": selected,
        "roll_rule_from_cache_name": "calendar" if "c" in selected else "volume",
        "candidate_roots": {key: sum(p.stat().st_size for p in paths)
                            for key, paths in candidates.items()},
        "source_files": [{"name": path.name, "sha256": sha256_file(path),
                          "rows": pq.ParquetFile(path).metadata.num_rows}
                         for path in sources],
        "export_rows": len(export), "reconstructed_rows": len(reconstructed),
        "matching_timestamps": bool(same_times), "matching_values": bool(same_values),
        "verified_match": bool(same_times and same_values),
        "comparison": "exact values and dtypes; no precision cast" if original_precision else "legacy export float32/uint32 comparison",
        "trust_boundary": "local transformation chain, not authenticated vendor delivery",
        "mapping_status": "not supplied by OHLCV export or cached Parquet slices",
    }
