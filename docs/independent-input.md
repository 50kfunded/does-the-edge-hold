# using another input

the public spot case is the independent source walkthrough. it uses a different source, timeframe, cash ledger and daily clock through the same evaluator. it doesn't turn imported P&L into proof of execution.

1. install the project and run the public example and tests.
2. run `edge-hold public-fetch --output runs/your-snapshot`. no account is needed.
3. inspect the snapshot's raw-response hashes and audit. each API request stays local, and bars must replay exactly from those responses.
4. run `edge-hold public-study --snapshot runs/your-snapshot --output runs/your-study`.
5. read `summary.json`, each `execution.json`, `results.json`, `daily-pnl.csv` and `report.md`. the BTC choice stays fixed for ETH.

the frozen lock requires the original Parquet SHA-256. a different writer version can change file bytes without changing bars. if the lock fails, compare normalized timestamps and exact OHLCV against a snapshot you actually possess. the repo includes request/body hashes, not raw candles, so it cannot prove bar equality for a new download by itself.

for a new snapshot, keep the original plan and results. copy the plan to a new directory, increment its version, disclose that the old results have now been seen, and record whether the change was only serialization or revised data. audit it, then use `edge-hold freeze --plan ... --audit ... --output ...`. pass that new plan and lock to `public-study`. don't relabel it as the original exact reproduction or an untouched evaluation.

## a small signal extension

[examples/breakout.py](../examples/breakout.py) registers a past-high breakout using the canonical completed-bar interface. a plan can list `extensions: ["examples.breakout"]` and a `breakout` family with `lookback_bars`. the independent-extension test adds its own instrument specification without editing the evaluator.

canonical input is ordered UTC start-stamped `ts,open,high,low,close,volume,contract`. `MarketAdapter` supplies the instrument specification, bar duration, asset kind and ledger. a one-minute adapter makes hourly signals; longer bars are already signal bars. adapters must disclose that choice and provide genuine source provenance.

this keeps the scope small: audits, long/flat rules, execution assumptions and reports. there's no live trading, broker connection, optimization service or claim of outside users.

