import pandas as pd

from does_the_edge_hold.ledger import ContractSpec, Costs
from does_the_edge_hold.timing import hourly_from_minutes, simulate


def bars() -> pd.DataFrame:
    ts = pd.date_range("2024-01-08 00:00", periods=122, freq="min", tz="UTC")
    return pd.DataFrame({"ts": ts, "open": range(122), "high": range(122),
                         "low": range(122), "close": range(122),
                         "volume": 1, "contract": "A"})


def test_hour_close_is_known_at_end_not_start() -> None:
    hourly = hourly_from_minutes(bars())
    assert hourly.loc[0, "bar_start"] == pd.Timestamp("2024-01-08 00:00Z")
    assert hourly.loc[0, "close"] == 59
    assert hourly.loc[0, "known_at"] == pd.Timestamp("2024-01-08 01:00Z")


def test_trade_uses_later_minute_open_and_delay() -> None:
    minute = bars()
    decision = pd.DataFrame({"known_at": [pd.Timestamp("2024-01-08 01:00Z")],
                             "target": [1]})
    spec = ContractSpec("SYN", 1, 1)
    immediate = simulate(minute, decision, spec, Costs(0, 0))
    delayed = simulate(minute, decision, spec, Costs(0, 0), delay_minutes=5)
    assert immediate.ledger.fills[0].ts == pd.Timestamp("2024-01-08 01:00Z")
    assert immediate.ledger.fills[0].raw_price == 60
    assert delayed.ledger.fills[0].ts == pd.Timestamp("2024-01-08 01:05Z")
    assert delayed.ledger.fills[0].raw_price == 65


def test_missing_minutes_do_not_create_fake_fills() -> None:
    minute = bars().drop(index=[60, 61, 62]).reset_index(drop=True)
    decision = pd.DataFrame({"known_at": [pd.Timestamp("2024-01-08 01:00Z")],
                             "target": [1]})
    result = simulate(minute, decision, ContractSpec("SYN", 1, 1), Costs(0, 0))
    assert result.ledger.fills[0].ts == pd.Timestamp("2024-01-08 01:03Z")
