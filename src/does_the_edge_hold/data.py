"""Read-only adapters for the local Parquet exports."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Iterator

import pandas as pd
import pyarrow.parquet as pq


MARKETS = ("NQ", "ES", "YM", "GC", "CL")
BAR_COLUMNS = ("ts", "open", "high", "low", "close", "volume")


def source_path(root: str | Path, market: str, resolution: str = "1m") -> Path:
    market = market.upper()
    if market not in MARKETS or resolution not in ("1m", "1s"):
        raise ValueError("unknown market or resolution")
    if resolution == "1s" and market != "NQ":
        raise ValueError("only NQ has a local 1-second export")
    path = Path(root) / f"{market}_{resolution}.parquet"
    if not path.is_file():
        raise FileNotFoundError(path)
    return path


def iter_parquet(path: str | Path, batch_size: int = 65_536) -> Iterator[pd.DataFrame]:
    """Read one bounded batch at a time; never write to the source."""
    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    parquet = pq.ParquetFile(path)
    names = set(parquet.schema_arrow.names)
    missing = set(BAR_COLUMNS) - names
    if missing:
        raise ValueError(f"missing columns in {path}: {sorted(missing)}")
    for batch in parquet.iter_batches(batch_size=batch_size, columns=list(BAR_COLUMNS)):
        frame = batch.to_pandas()
        if "ts" not in frame.columns and frame.index.name == "ts":
            frame = frame.reset_index()
        frame["ts"] = pd.to_datetime(frame["ts"], utc=True)
        yield frame[list(BAR_COLUMNS)]


def load_minutes(root: str | Path, market: str) -> pd.DataFrame:
    """Load one minute market, never the whole multi-market collection."""
    path = source_path(root, market)
    return pd.concat(iter_parquet(path), ignore_index=True)


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()
