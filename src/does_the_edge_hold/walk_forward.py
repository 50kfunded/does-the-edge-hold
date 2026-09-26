"""Secondary rolling calendar-year diagnostic."""

from __future__ import annotations

import math

import pandas as pd


def _sharpe(daily: pd.Series, capital: float, periods_per_year=365) -> float | None:
    if len(daily) < 2:
        return None
    values = daily / capital
    std = values.std(ddof=1)
    return float(values.mean() / std * math.sqrt(periods_per_year)) if std > 0 else None


def evaluate(base_daily: dict[str, pd.Series], rows: list[dict],
             capital: float, minimum_trades: int, *, periods_per_year=365) -> list[dict]:
    """Select on each prior three calendar years and inspect the next year."""
    candidates = [key for key in base_daily if key not in ("flat", "always_long")]
    years = sorted({int(row["period"]) for row in rows if row.get("period", "").isdigit()
                    and row.get("scenario") == "base"})
    out = []
    for test_year in years:
        if test_year - 3 < min(years):
            continue
        ranked = []
        for config in candidates:
            daily = base_daily[config]
            train = daily.loc[(daily.index.year >= test_year - 3) &
                              (daily.index.year < test_year)]
            entries = sum(row["entry_trades"] for row in rows
                          if row.get("config_id") == config and row.get("scenario") == "base"
                          and row.get("period") in {str(y) for y in range(test_year - 3, test_year)}
                          and row.get("status") == "ok")
            fills = sum(row["fills"] for row in rows if row.get("config_id") == config and
                        row.get("scenario") == "base" and row.get("period") in
                        {str(y) for y in range(test_year - 3, test_year)} and row.get("status") == "ok")
            score = _sharpe(train, capital, periods_per_year)
            if entries >= minimum_trades and score is not None:
                ranked.append((-score, fills, config))
        ranked.sort()
        if not ranked:
            out.append({"test_year": test_year, "winner": None,
                        "status": "no eligible configuration"})
            continue
        winner = ranked[0][2]
        daily = base_daily[winner]
        test = daily.loc[daily.index.year == test_year]
        out.append({"test_year": test_year, "train_years": [test_year - 3, test_year - 2,
                                                               test_year - 1],
                    "winner": winner, "train_sharpe": -ranked[0][0],
                    "test_net_pnl_usd": float(test.sum()),
                    "test_sharpe": _sharpe(test, capital, periods_per_year), "test_days": len(test),
                    "interpretation": "candidate-selection diagnostic on continuously simulated states; not an executed switching portfolio",
                    "status": "ok"})
    return out
