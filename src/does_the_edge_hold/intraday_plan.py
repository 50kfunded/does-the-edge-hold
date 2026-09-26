"""A separate source-day protocol; never a substitute for the old roll gate."""
import json
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
from .plan import validate as validate_common, _digest
from .semantic import SCHEMA

def default_plan():
    return {
        "version": 1, "study": "source_day_intraday_v1", "data_identity": SCHEMA,
        "question": "does a selected long/flat rule hold up in later complete intraday windows, costs, slower orders and related markets?",
        "universe": {"primary": "NQ", "required": ["NQ"], "optional": ["ES", "YM"], "allowed_exclusions": ["ES", "YM"]},
        "descriptive_markets": ["GC", "CL"], "audit_markets": ["NQ", "ES", "YM", "GC", "CL"],
        "window": {"start": "08:00", "end_exclusive": "12:00", "warmup_end": "09:00",
                   "entry_fill_cutoff_exclusive": "11:30", "exit_instruction": "11:50", "minutes": 240, "bar_minutes": 5,
                   "calendar": "fixed Monday-Friday UTC candidates, not a verified exchange calendar"},
        "signal_families": {"momentum": {"lookback_bars": [3, 6, 12],
            "rule": "latest completed close minus first open of the last n completed five-minute bars, positive means long; price points, not percentage or n-lag close"},
            "mean_reversion": {"lookback_bars": [6, 12], "entry_z": [.5, 1., 1.5], "exit_z": 0,
            "rule": "latest close minus mean of last n completed closes INCLUDING latest, divided by sample std ddof=1; enter z<=-entry_z, exit z>=0; insufficient or zero variance flat"}},
        "configuration_count": 9, "baseline_ids": ["flat", "intraday_long"],
        "feature_policy": "only exact complete five-minute buckets; reset prices, latent holding state, pending orders and position per UTC date; no warmup orders or latent holding; twelve bars fit the sixty-minute warmup",
        "splits_utc": {"development": ["2016-08-12", "2022-01-01"], "validation": ["2022-01-01", "2024-01-01"],
                       "historical_final": ["2024-01-01", "2026-08-10"]},
        "selection": {"minimum_entry_trades": 20, "metric": "development net daily account-capital Sharpe in base",
                      "tie_break": "fewer filled entries, then lexical configuration id", "later_use": "keep NQ development choice in later NQ and ES/YM; no replacement if ineligible"},
        "execution": {"starting_capital_usd_per_market": 100000, "position": "one full contract long or flat; capital convention, no margin simulation or equal-risk sizing",
            "fill": "observed minute open proxy at or after completed-bar end plus extra delay, not a quote at that instant; directional tick rounding then adverse ticks",
            "terminal": "known before the window; cancel all pending signal orders at 11:50; exit first observed open at/after 11:50+delay and strictly before 12:00; missing exit fails unresolved",
            "entry": "decisions at/after 09:00, entries fill strictly before 11:30; an unfilled signal is superseded by a later decision",
            "baseline": "intraday_long first eligible 09:00 instruction plus delay; same cutoff, costs, mask and terminal instruction",
            "scenarios": [{"name": name, "commission_usd_per_side": fee, "slippage_ticks_per_side": slip, "delay_minutes": delay}
                          for name, fee, slip, delay in [("base", 2.5, 1, 1), ("gross_reference", 0, 0, 1), ("cost_stress", 5, 2, 1),
                                                        ("delay_stress", 2.5, 1, 5), ("combined_stress", 5, 2, 5)]]},
        "statistics": {"clock": {"name": "utc_calendar", "periods_per_year": 252}, "block_lengths": [3, 5, 10], "replicates": 2000, "seed": 1729,
                       "minimum_paired_observations": 30, "uncertainty": "paired circular blocks of ordered eligible windows; conventional 252 scaling, descriptive; calendar gaps and longer memory remain limits"},
        "eligibility": "ex-post exact 240-minute windows only; same source-quality mask for all rules, baselines and scenarios; retrospective conditional returns, not a live 09:00 filter",
        "cross_market": "own complete-window results and separately paired intersection of NQ/ES/YM complete UTC dates; keep the NQ own-window development pick",
        "prior_exposure": "prior NQ/related-market research through 2026 and the public spot results were viewed. backup schema, source matching and coverage were inspected before this lock. no output from this new five-minute grid was viewed before the lock. historical final is not untouched or prospective.",
        "source_boundary": "opaque source_segment_id per source rule and UTC date, contract identity unknown; calendar continuity inferred from historical date semantics plus exact local cache provenance, not recovered instrument IDs",
        "revision_rule": "coverage can justify a documented new lock before strategy results; performance cannot change the protocol quietly"}

def validate(plan):
    validate_common(plan)
    if plan.get("study") != "source_day_intraday_v1" or plan.get("data_identity") != SCHEMA:
        raise ValueError("not a supported source-day protocol")
    fixed = default_plan()
    for key in ("window", "signal_families", "configuration_count", "baseline_ids", "feature_policy", "execution", "selection", "eligibility", "source_boundary", "cross_market"):
        if plan[key] != fixed[key]:
            raise ValueError(f"unsupported source-day semantics: {key}; version the implementation before changing it")
    if plan["universe"]["primary"] != "NQ" or plan["universe"]["required"] != ["NQ"]:
        raise ValueError("NQ is the required source-day primary")
    if set(plan["universe"]["optional"]) - {"ES", "YM"} or set(plan["descriptive_markets"]) - {"GC", "CL"}:
        raise ValueError("initial P&L scope is calendar NQ/ES/YM only")

def candidate_dates(plan):
    lower = plan["splits_utc"]["development"][0]
    upper = plan["splits_utc"]["historical_final"][1]
    return pd.bdate_range(pd.Timestamp(lower, tz="UTC"), pd.Timestamp(upper, tz="UTC"), inclusive="left")

def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def freeze(plan_path, audit_path, output):
    plan, audit = read(plan_path), read(audit_path)
    validate(plan)
    if audit["plan_sha256"] != _digest(plan): raise ValueError("audit belongs to another protocol")
    if not audit["readiness"]["primary_ready"]: raise ValueError("source-day primary evidence is insufficient")
    lock = {"identity_version": 2, "plan_sha256": _digest(plan), "frozen_utc": datetime.now(timezone.utc).isoformat(),
            "source_hashes": {r["market"]: r["semantic"]["sha256"] for r in audit["sources"]},
            "artifact_hashes": {r["market"]: r["artifact_sha256"] for r in audit["sources"]},
            "audit_sha256": _digest(audit), "masks": audit["mask_hashes"], "readiness": audit["readiness"]}
    path = Path(output)
    if path.exists(): raise FileExistsError("source-day lock already exists")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return lock
