"""Versioned, serialization-independent identity of observed OHLCV rows."""
from __future__ import annotations
import hashlib
import struct
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from .data import iter_parquet

SCHEMA = "ohlcv-utc-ns-f64-v1"
HEADER = b"ohlcv-utc-ns-f64-v1|ts:i64be|open,high,low,close,volume:f64be|null:reject|zero:positive\n"

def semantic_digest(batches):
    digest = hashlib.sha256(HEADER)
    previous, count = None, 0
    dtype = np.dtype([("ts", ">i8"), *[(key, ">f8") for key in ("open", "high", "low", "close", "volume")]])
    for frame in batches:
        if frame.empty:
            continue
        if not isinstance(frame.ts.dtype, pd.DatetimeTZDtype):
            raise ValueError("semantic timestamps must have an explicit timezone")
        ts = frame.ts.dt.tz_convert("UTC").dt.as_unit("ns")
        if ts.isna().any() or not ts.is_monotonic_increasing or ts.duplicated().any():
            raise ValueError("reject null, duplicate or unordered timestamps before hashing")
        ns = ts.astype("int64").to_numpy()
        if previous is not None and ns[0] <= previous:
            raise ValueError("reject duplicate or unordered timestamps across batches")
        values = frame[["open", "high", "low", "close", "volume"]].to_numpy(dtype="float64", copy=True)
        if not np.isfinite(values).all():
            raise ValueError("reject nonfinite or null observations before hashing")
        if (values[:, 4] < 0).any():
            raise ValueError("volume cannot be negative")
        if ((values[:, 1] < values[:, :4].max(axis=1)) | (values[:, 2] > values[:, :4].min(axis=1))).any():
            raise ValueError("reject invalid OHLC before hashing")
        if pd.api.types.is_integer_dtype(frame.volume) and any(int(a) != int(b) for a, b in zip(frame.volume, values[:, 4])):
            raise ValueError("integer volume cannot be represented exactly as float64")
        values[values == 0] = 0.0
        records = np.empty(len(frame), dtype=dtype)
        records["ts"] = ns
        for i, key in enumerate(("open", "high", "low", "close", "volume")):
            records[key] = values[:, i]
        digest.update(records.tobytes())
        count += len(frame)
        previous = int(ns[-1])
    digest.update(b"rows:" + struct.pack(">Q", count))
    return {"schema": SCHEMA, "rows": count, "sha256": digest.hexdigest()}

def semantic_file(path):
    field = pq.ParquetFile(path).schema_arrow.field("ts")
    if not getattr(field.type, "tz", None):
        raise ValueError("source timestamps need an explicit timezone")
    return semantic_digest(iter_parquet(path))
