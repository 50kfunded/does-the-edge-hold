"""One-contract-or-flat futures cash and P&L accounting."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class ContractSpec:
    symbol: str
    multiplier: float
    tick_size: float

    def __post_init__(self) -> None:
        if self.multiplier <= 0 or self.tick_size <= 0:
            raise ValueError("multiplier and tick size must be positive")


@dataclass(frozen=True)
class Costs:
    commission_per_side: float = 2.50
    slippage_ticks_per_side: float = 1.0

    def __post_init__(self) -> None:
        if self.commission_per_side < 0 or self.slippage_ticks_per_side < 0:
            raise ValueError("costs cannot be negative")


@dataclass(frozen=True)
class Fill:
    ts: datetime
    contract: str
    side: str
    raw_price: float
    fill_price: float
    commission: float
    slippage: float
    reason: str
    known_at: datetime | None = None


@dataclass
class Ledger:
    spec: ContractSpec
    costs: Costs
    starting_capital: float = 100_000.0
    cash_pnl: float = 0.0
    gross_realized: float = 0.0
    commission_paid: float = 0.0
    slippage_paid: float = 0.0
    position: int = 0
    contract: str | None = None
    entry_fill: float | None = None
    entry_raw: float | None = None
    mark_price: float | None = None
    fills: list[Fill] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.starting_capital <= 0:
            raise ValueError("starting capital must be positive")

    @property
    def unrealized(self) -> float:
        if not self.position:
            return 0.0
        assert self.mark_price is not None and self.entry_fill is not None
        return (self.mark_price - self.entry_fill) * self.spec.multiplier

    @property
    def gross_pnl(self) -> float:
        if not self.position:
            return self.gross_realized
        assert self.mark_price is not None and self.entry_raw is not None
        return self.gross_realized + (self.mark_price - self.entry_raw) * self.spec.multiplier

    @property
    def net_pnl(self) -> float:
        return self.cash_pnl + self.unrealized

    @property
    def equity(self) -> float:
        return self.starting_capital + self.net_pnl

    @property
    def trade_count(self) -> int:
        return sum(fill.side == "buy" for fill in self.fills)

    def _fill(self, ts: datetime, contract: str, side: str, raw: float, reason: str) -> float:
        direction = 1 if side == "buy" else -1
        slippage = self.costs.slippage_ticks_per_side * self.spec.tick_size * self.spec.multiplier
        fill_price = raw + direction * self.costs.slippage_ticks_per_side * self.spec.tick_size
        self.commission_paid += self.costs.commission_per_side
        self.slippage_paid += slippage
        self.cash_pnl -= self.costs.commission_per_side
        self.fills.append(Fill(ts, contract, side, raw, fill_price,
                               self.costs.commission_per_side, slippage, reason))
        return fill_price

    def buy(self, ts: datetime, contract: str, raw_price: float, reason: str = "signal") -> None:
        if self.position:
            raise ValueError("already long")
        self.entry_fill = self._fill(ts, contract, "buy", raw_price, reason)
        self.entry_raw = raw_price
        self.mark_price = raw_price
        self.contract = contract
        self.position = 1

    def sell(self, ts: datetime, contract: str, raw_price: float, reason: str = "signal") -> None:
        if not self.position or contract != self.contract:
            raise ValueError("cannot close a different or missing contract")
        fill_price = self._fill(ts, contract, "sell", raw_price, reason)
        assert self.entry_fill is not None and self.entry_raw is not None
        self.cash_pnl += (fill_price - self.entry_fill) * self.spec.multiplier
        self.gross_realized += (raw_price - self.entry_raw) * self.spec.multiplier
        self.position = 0
        self.contract = None
        self.entry_fill = None
        self.entry_raw = None
        self.mark_price = None

    def mark(self, contract: str, raw_price: float) -> None:
        if self.position:
            if contract != self.contract:
                raise ValueError("roll transition needs an explicit close and reopen")
            self.mark_price = raw_price

    def roll(self, ts: datetime, old_contract: str, old_exit: float,
             new_contract: str, new_entry: float) -> None:
        """Close old and reopen new at separately supplied tradable prices."""
        if old_contract == new_contract:
            raise ValueError("not a roll")
        if not self.position:
            return
        self.sell(ts, old_contract, old_exit, reason="roll exit")
        self.buy(ts, new_contract, new_entry, reason="roll entry")
