"""Redistributable multi-window prices through the actual audit/lock/run path."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from .intraday_plan import default_plan, freeze
from .intraday_audit import run_audit, SOURCE_DOCS
from .intraday_study import run_study

def run_example(output, *, days=90, replicates=200):
    output = Path(output); output.mkdir(parents=True, exist_ok=False)
    bars_root, cache_root = output / "bars", output / "cache"
    bars_root.mkdir(); cache_root.mkdir()
    dates = pd.bdate_range("2020-01-02", periods=days, tz="UTC")
    rng = np.random.default_rng(1729)
    for market in ("NQ", "ES", "YM", "GC", "CL"):
        frames = []
        for i, date in enumerate(dates):
            # Large between-date gaps test resets; within-window ticks are wholly made up.
            steps = rng.integers(-4, 5, 240).cumsum()
            prices = (4000 + i * 500 + steps * (.25 if market in ("NQ", "ES") else 1)).astype("float64")
            frame = pd.DataFrame({"ts": pd.date_range(date + pd.Timedelta(hours=8), periods=240, freq="min").as_unit("ns"),
                                  "open": prices, "high": prices + 1., "low": prices - 1., "close": prices + .25, "volume": np.full(240, 100, dtype="int64")})
            if i == days // 3: frame = frame.drop(index=20)  # Missing warmup candidate stays unscored for every case.
            frames.append(frame)
        bars = pd.concat(frames, ignore_index=True).set_index("ts")
        bars.to_parquet(bars_root / f"{market}_1m.parquet")
        root = market + ("v0" if market in ("GC", "CL") else "c0")
        bars.to_parquet(cache_root / f"databento_{root}_ohlcv-1m_synthetic_ctx.parquet")
    plan = default_plan()
    boundaries = [dates[0], dates[days // 3], dates[2 * days // 3], dates[-1] + pd.Timedelta(days=1)]
    plan["splits_utc"] = {name: [str(boundaries[i].date()), str(boundaries[i + 1].date())] for i, name in enumerate(("development", "validation", "historical_final"))}
    plan["statistics"]["replicates"] = replicates
    plan["prior_exposure"] = "wholly synthetic seeded software fixture; no market inference"
    plan_path, lock_path = output / "plan.json", output / "plan.lock.json"
    plan_path.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    docs = {**SOURCE_DOCS, "scope": "wholly synthetic source-rule fixture; not empirical evidence"}
    audit_root = output / "audit"
    run_audit(bars_root, cache_root, plan_path, audit_root, docs=docs)
    freeze(plan_path, audit_root / "audit.json", lock_path)
    return run_study(bars_root, cache_root, plan_path, lock_path, audit_root, output / "study", synthetic=True)
