# using another input

i can run the examples and tests without an account or market files. `edge-hold intraday-example --output runs/intraday-example` makes fake minutes and uses the same audit, freeze, evaluation and report path as the separate within-day case.

## the spot snapshot

1. run `edge-hold public-fetch --output runs/your-snapshot`.
2. inspect the audit and raw-response hashes. the bars must replay exactly from those responses.
3. run `edge-hold public-study --snapshot runs/your-snapshot --plan research/public-spot/plan.semantic-v2.json --lock research/public-spot/plan.semantic-v2.lock.json --output runs/your-study`.
4. read the summary, execution identities, results, daily panel and report. the BTC choice stays fixed for ETH.

i preserved the original version-one plan, byte lock and results. the separate [semantic migration](../research/public-spot/semantic-migration.json) was made after seeing those results. it allows a different Parquet writer when the normalized observations match exactly. it still checks the original raw-response bytes and candle replay. a revised response or changed candle fails; this isn't a new untouched evaluation.

the repo has hashes, not the original raw candles. a new download that doesn't match can't prove equivalence by itself. keep the old plan and results, copy the plan to a new directory, disclose prior exposure, audit the new snapshot and freeze its new lock before a new grid. record whether the change was serialization or changed data.

## a small signal extension

[the breakout example](../examples/breakout.py) declares its inputs, settings and helpers. a plan can list `extensions: ["examples.breakout"]` and a `breakout` family with `lookback_bars`. [the extension notes](extensions.md) explain identity and sampled causal checks. Python extensions aren't a sandbox or a proof against future access.

canonical input is ordered UTC start-stamped `ts,open,high,low,close,volume,contract`. `MarketAdapter` supplies the instrument specification, bar duration, asset kind and ledger. a one-minute adapter makes hourly signals; longer bars are already signal bars. the within-day case has separate five-minute definitions and date resets. each source needs its own provenance and clock evidence.

there's no live trading, broker connection or claim of outside users.
