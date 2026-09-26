"""Funded spot cash/inventory accounting; no futures principal convention."""
from dataclasses import dataclass, field
from .ledger import ContractSpec, Costs, Fill

@dataclass
class SpotLedger:
    spec: ContractSpec
    costs: Costs
    starting_capital: float = 1_000_000
    position: int = 0
    contract: str | None = None
    entry_raw: float | None = None
    mark_price: float | None = None
    gross_realized: float = 0
    commission_paid: float = 0
    slippage_paid: float = 0
    fills: list = field(default_factory=list)

    def __post_init__(self):
        if self.starting_capital <= 0 or self.costs.commission_per_side or self.costs.slippage_ticks_per_side:
            raise ValueError("spot uses positive funded capital and bps costs")
        self.cash_balance = self.starting_capital

    @property
    def equity(self):
        return self.cash_balance + self.position * self.spec.multiplier * (self.mark_price or 0)

    @property
    def net_pnl(self):
        return self.equity - self.starting_capital

    @property
    def gross_pnl(self):
        return self.gross_realized + (self.spec.multiplier * (self.mark_price - self.entry_raw) if self.position else 0)

    @property
    def trade_count(self):
        return sum(f.side == "buy" for f in self.fills)

    def _quote(self, raw, side):
        if raw <= 0:
            raise ValueError("spot price must be positive")
        fill = raw * (1 + (1 if side == "buy" else -1) * self.costs.slippage_bps / 10_000)
        fee = abs(fill * self.spec.multiplier) * self.costs.fee_bps / 10_000
        return fill, fee

    def _record(self, ts, contract, side, raw, fill, fee, reason):
        slip = abs(fill - raw) * self.spec.multiplier
        self.commission_paid += fee
        self.slippage_paid += slip
        self.fills.append(Fill(ts, contract, side, raw, fill, fee, slip, reason))

    def buy(self, ts, contract, raw_price, reason="signal"):
        if self.position:
            raise ValueError("already long")
        fill, fee = self._quote(raw_price, "buy")
        principal = fill * self.spec.multiplier + fee
        if principal > self.cash_balance:
            raise ValueError("insufficient spot cash; no borrowing allowed")
        self.cash_balance -= principal
        self.position, self.contract, self.entry_raw, self.mark_price = 1, contract, raw_price, raw_price
        self._record(ts, contract, "buy", raw_price, fill, fee, reason)

    def sell(self, ts, contract, raw_price, reason="signal"):
        if not self.position or contract != self.contract:
            raise ValueError("cannot close missing or different spot inventory")
        fill, fee = self._quote(raw_price, "sell")
        self.cash_balance += fill * self.spec.multiplier - fee
        self.gross_realized += (raw_price - self.entry_raw) * self.spec.multiplier
        self.position, self.contract, self.entry_raw, self.mark_price = 0, None, None, None
        self._record(ts, contract, "sell", raw_price, fill, fee, reason)

    def mark(self, contract, raw_price):
        if raw_price <= 0 or (self.position and contract != self.contract):
            raise ValueError("invalid spot mark")
        if self.position:
            self.mark_price = raw_price
