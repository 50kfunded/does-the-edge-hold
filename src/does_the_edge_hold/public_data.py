"""A bounded, unauthenticated Coinbase daily-candle snapshot and strict replay."""
from __future__ import annotations
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd
from .adapters import MarketAdapter
from .data import sha256_file
from .ledger import ContractSpec

DOCS = "https://docs.cdp.coinbase.com/api-reference/exchange-api/rest-api/products/get-product-candles"

def fetch(root, *, products=("BTC-USD", "ETH-USD"), start="2017-01-01", end="2026-09-01"):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=False)
    lower, upper = pd.Timestamp(start, tz="UTC"), pd.Timestamp(end, tz="UTC")
    manifest = {"source": "Coinbase Exchange public candles", "docs": DOCS,
                "granularity_seconds": 86400, "start_inclusive": lower.isoformat(), "end_exclusive": upper.isoformat(),
                "retrieved_at": datetime.now(timezone.utc).isoformat(), "products": {}}
    for product in products:
        parts, requests = [], []
        cursor = lower
        while cursor < upper:
            boundary = min(cursor + pd.Timedelta(days=250), upper)
            query = urllib.parse.urlencode({"granularity": 86400, "start": cursor.isoformat(), "end": boundary.isoformat()})
            url = f"https://api.exchange.coinbase.com/products/{product}/candles?{query}"
            for attempt in range(3):
                try:
                    request = urllib.request.Request(url, headers={"User-Agent": "does-the-edge-hold/0.1 research snapshot"})
                    with urllib.request.urlopen(request, timeout=25) as response:
                        body = response.read()
                    break
                except (urllib.error.URLError, TimeoutError):
                    if attempt == 2:
                        raise
                    time.sleep(1 + attempt)
            file = root / f"{product}-{cursor.date()}.json"
            file.write_bytes(body)
            records = json.loads(body)
            if not isinstance(records, list) or any(len(r) != 6 for r in records):
                raise ValueError("unexpected candle response")
            frame = pd.DataFrame(records, columns=["epoch", "low", "high", "open", "close", "volume"])
            frame["ts"] = pd.to_datetime(frame.epoch, unit="s", utc=True)
            # API includes buckets outside a request range; exclusion is explicit.
            keep = (frame.ts >= cursor) & (frame.ts < boundary)
            requests.append({"url": url, "file": file.name, "sha256": sha256_file(file),
                             "returned_rows": len(frame), "out_of_window_rows": int((~keep).sum())})
            parts.append(frame.loc[keep, ["ts", "open", "high", "low", "close", "volume"]])
            cursor = boundary
            time.sleep(.15)
        bars = pd.concat(parts, ignore_index=True).sort_values("ts").reset_index(drop=True)
        bars["contract"] = product
        file = root / f"{product}.parquet"
        bars.to_parquet(file, index=False)
        manifest["products"][product] = {"file": file.name, "sha256": sha256_file(file), "requests": requests}
    (root / "snapshot.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return audit_snapshot(root)

def audit_snapshot(root, *, semantic=False):
    root = Path(root)
    manifest = json.loads((root / "snapshot.json").read_text(encoding="utf-8"))
    files = []
    expected = pd.date_range(manifest["start_inclusive"], manifest["end_exclusive"], freq="D", inclusive="left")
    for product, meta in manifest["products"].items():
        file = root / meta["file"]
        artifact_hash = sha256_file(file)
        if not semantic and artifact_hash != meta["sha256"]:
            raise ValueError("snapshot bars changed")
        for request in meta["requests"]:
            if sha256_file(root / request["file"]) != request["sha256"]:
                raise ValueError("snapshot response changed")
        bars = pd.read_parquet(file)
        replay = []
        for request in meta["requests"]:
            query = urllib.parse.parse_qs(urllib.parse.urlparse(request["url"]).query)
            raw = json.loads((root / request["file"]).read_text())
            part = pd.DataFrame(raw, columns=["epoch", "low", "high", "open", "close", "volume"])
            part["ts"] = pd.to_datetime(part.epoch, unit="s", utc=True)
            part = part.loc[(part.ts >= pd.Timestamp(query["start"][0])) & (part.ts < pd.Timestamp(query["end"][0]))]
            replay.append(part[["ts", "open", "high", "low", "close", "volume"]])
        replayed = pd.concat(replay, ignore_index=True).sort_values("ts").reset_index(drop=True)
        replayed["contract"] = product
        bars["ts"] = bars.ts.dt.as_unit("ns")
        replayed["ts"] = replayed.ts.dt.as_unit("ns")
        from .semantic import semantic_digest
        observed_identity = semantic_digest([bars])
        replay_identity = semantic_digest([replayed])
        if semantic:
            if observed_identity != replay_identity or not bars.contract.eq(product).all():
                raise ValueError("snapshot observations changed from raw response replay")
        else:
            pd.testing.assert_frame_equal(bars, replayed, check_exact=True)
        MarketAdapter(ContractSpec(product, 1, .01), "spot", 1440).validate(bars)
        observed = pd.DatetimeIndex(bars.ts)
        missing = expected.difference(observed)
        outside = observed.difference(expected)
        files.append({"market": product, "resolution": "1d", "sha256": artifact_hash,
                      "semantic": observed_identity, "rows": len(bars),
                      "first_utc": bars.ts.iloc[0].isoformat(), "last_utc": bars.ts.iloc[-1].isoformat(),
                      "missing_calendar_days": len(missing), "outside_window_days": len(outside),
                      "maximum_open_usd": float(bars.open.max()), "quality_status": "ready" if not len(missing) and not len(outside) else "blocked",
                      "exact_response_replay": True,
                      "request_count": len(meta["requests"])})
    return {"scope": "public spot OHLCV; separate from blocked futures", "source": manifest["source"],
            "retrieved_at": manifest["retrieved_at"], "files": files,
            "quality_policy": "fail on invalid bars, duplicates, order, missing calendar days or outside-window bars; no imputation"}
