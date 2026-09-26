"""Long-or-flat signals built only from completed bars."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import inspect
import types

import numpy as np
import pandas as pd

REGISTRY = {}
DECLARATIONS = {}

def register_signal(name, callback, *, inputs, state=(), dependencies=()):
    if name in ("momentum", "mean_reversion") or name in REGISTRY:
        raise ValueError("signal name is already registered")
    if not {"known_at", "contract", "close"}.issubset(inputs):
        raise ValueError("declare the timestamp, segment and price inputs")
    REGISTRY[name] = callback
    DECLARATIONS[name] = {"inputs": list(inputs), "state": list(state), "dependencies": list(dependencies)}
    try:
        extension_identity(name)
    except Exception:
        del REGISTRY[name]
        del DECLARATIONS[name]
        raise


def extension_identity(name):
    """Capture declared settings without reading unrelated globals or credentials."""
    from .execution import callable_identity
    if name not in DECLARATIONS:
        raise ValueError("extension needs declared inputs, state and dependencies")
    declaration = DECLARATIONS[name]
    fn = REGISTRY[name]
    referenced = inspect.getclosurevars(fn)
    if set(referenced.builtins) & {"open", "input", "eval", "exec", "__import__", "globals", "locals"}:
        raise ValueError("extension uses unsupported hidden I/O or dynamic state")
    state, dependencies = {}, {}
    for key, value in referenced.globals.items():
        if isinstance(value, types.ModuleType) and value.__name__ in ("pandas", "numpy"):
            dependencies[key] = {"module": value.__name__}
        elif key in declaration["state"]:
            try:
                state[key] = json.loads(json.dumps(value, allow_nan=False, sort_keys=True))
            except (TypeError, ValueError) as exc:
                raise ValueError("declared extension state must be JSON data") from exc
        elif key in declaration["dependencies"] and inspect.isfunction(value):
            # Helpers must be pure: no further hidden global/default/closure settings.
            refs = inspect.getclosurevars(value)
            if refs.globals or value.__closure__ or value.__defaults__:
                raise ValueError("dependency helpers must have no captured settings")
            dependencies[key] = callable_identity(value)
        else:
            raise ValueError(f"undeclared extension global: {key}")
    if set(declaration["state"]) - set(state):
        raise ValueError("declared state must be a referenced global")
    return {"callable": callable_identity(fn), "declaration": json.loads(json.dumps(declaration)),
            "state": state, "dependencies": dependencies,
            "causal_policy": "determinism, sampled prefixes and future perturbations before evaluation"}


def extension_decisions(bars, spec):
    name = spec.family
    before = extension_identity(name)
    inputs = DECLARATIONS[name]["inputs"]
    frame = bars.loc[:, inputs].copy()
    def evaluate(data):
        out = REGISTRY[name](data.copy(), spec)
        if not isinstance(out, pd.DataFrame) or not {"known_at", "target"}.issubset(out):
            raise ValueError("extension must return aligned long/flat decisions")
        if not out.known_at.equals(data.known_at) or not out.target.isin([0, 1]).all():
            raise ValueError("extension must return aligned long/flat decisions")
        if extension_identity(name) != before:
            raise ValueError("extension changed its state during evaluation")
        return out.loc[:, ["known_at", "target"]]
    full = evaluate(frame)
    if not full.equals(evaluate(frame)):
        raise ValueError("extension is not deterministic")
    # Every prefix for small fixtures; deterministic distributed prefixes for large inputs.
    cuts = set(range(1, min(len(frame), 32) + 1))
    cuts.update(np.linspace(1, len(frame), min(16, len(frame)), dtype=int))
    for cut in sorted(cuts):
        if not full.iloc[:cut].equals(evaluate(frame.iloc[:cut])):
            raise ValueError("extension failed the causal prefix check")
        altered = frame.copy()
        for column in set(inputs) & {"open", "high", "low", "close", "volume"}:
            altered.loc[altered.index[cut:], column] = altered.iloc[cut:][column] * 1.17 + 3
        if not full.iloc[:cut].equals(evaluate(altered).iloc[:cut]):
            raise ValueError("extension failed future perturbation check")
    full.attrs["causal_check"] = {"status": "sampled_pass", "prefixes": len(cuts),
                                "limit": "not a proof against arbitrary code, hidden I/O or randomness"}
    return full


@dataclass(frozen=True)
class SignalSpec:
    family: str
    lookback_hours: int
    entry_z: float | None = None

    @property
    def id(self) -> str:
        if self.family == "momentum":
            return f"mom-{self.lookback_hours}"
        if self.family == "mean_reversion":
            return f"revert-{self.lookback_hours}-{self.entry_z:g}"
        return f"{self.family}-{self.lookback_hours}"

    @property
    def config_hash(self) -> str:
        payload = json.dumps(self.__dict__, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode()).hexdigest()


def grid_from_plan(plan: dict) -> list[SignalSpec]:
    count = plan["configuration_count"]
    if isinstance(count, bool) or not isinstance(count, int) or count < 1:
        raise ValueError("configuration count must be a positive integer")
    families = plan["signal_families"]
    grid = []
    for family, params in families.items():
        if "lookback_hours" in params and "lookback_bars" in params:
            raise ValueError("declare one lookback unit")
        if family == "mean_reversion" and params.get("exit_z", 0) != 0:
            raise ValueError("this mean-reversion implementation exits at zero")
        if family not in ("momentum", "mean_reversion") and family not in REGISTRY:
            raise ValueError(f"unregistered family: {family}")
        lengths = params.get("lookback_bars", params.get("lookback_hours", []))
        if not lengths or any(isinstance(n, bool) or not isinstance(n, int) or n <= 0 for n in lengths):
            raise ValueError("lookbacks must be positive finite integers")
        entries = params.get("entry_z", []) if family == "mean_reversion" else [None]
        if not entries or any(z is not None and (not np.isfinite(z) or z <= 0) for z in entries):
            raise ValueError("entry thresholds must be positive and finite")
        grid.extend(SignalSpec(family, n, z) for n in lengths for z in entries)
    if len(grid) != plan["configuration_count"] or len({item.id for item in grid}) != len(grid):
        raise ValueError("grid does not match the frozen research plan")
    return grid


def decisions(hourly: pd.DataFrame, spec: SignalSpec) -> pd.DataFrame:
    """A decision at `known_at` may use that bar's close, never later bars."""
    required = {"known_at", "close", "contract"}
    if not required.issubset(hourly):
        raise ValueError(f"signal bars need {sorted(required)}")
    if not hourly["known_at"].is_monotonic_increasing:
        raise ValueError("signal bars must be time ordered")
    if spec.family in REGISTRY:
        return extension_decisions(hourly, spec)
    target = np.zeros(len(hourly), dtype=np.int8)
    segments = hourly["contract"].ne(hourly["contract"].shift()).cumsum()
    for _, group in hourly.groupby(segments, sort=False, observed=True):
        indices = group.index.to_numpy()
        close = group["close"].astype(float).reset_index(drop=True)
        if spec.family == "momentum":
            past = close.shift(spec.lookback_hours)
            target[indices] = (close > past).fillna(False).to_numpy(dtype=np.int8)
        elif spec.family == "mean_reversion":
            if spec.entry_z is None or spec.entry_z <= 0:
                raise ValueError("mean reversion needs positive entry_z")
            prior = close.shift(1)
            mean = prior.rolling(spec.lookback_hours, min_periods=spec.lookback_hours).mean()
            stdev = prior.rolling(spec.lookback_hours, min_periods=spec.lookback_hours).std()
            z = (close - mean) / stdev.replace(0, np.nan)
            holding = 0
            for local, value in enumerate(z.to_numpy()):
                if not np.isfinite(value):
                    holding = 0
                elif holding and value >= 0:
                    holding = 0
                elif not holding and value <= -spec.entry_z:
                    holding = 1
                target[indices[local]] = holding
        else:
            raise ValueError(f"unknown signal family {spec.family}")
    return pd.DataFrame({"known_at": pd.to_datetime(hourly["known_at"], utc=True),
                         "target": target})
