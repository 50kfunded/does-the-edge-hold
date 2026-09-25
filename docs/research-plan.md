# research plan, frozen before the grid

the choices are in [research-plan.json](../research-plan.json), and [research-plan.lock.json](../research-plan.lock.json) records its hash plus the hashes of the six audited source files. the lock was made before running this project's nine-configuration strategy grid. a final run checks both hashes and refuses silent changes.

the main signal uses 1-hour bars made from start-stamped minute bars. an hour's close is only known at the scheduled end of that hour. the first simulated fill uses an observed minute open at or after that end plus the scenario delay. features restart at each contract change, so a continuous-series price gap cannot become a momentum or mean-reversion signal.

| split | UTC start, inclusive | UTC end, exclusive | NQ minute rows |
| --- | --- | --- | ---: |
| development | 2016-08-12 | 2022-01-01 | 1,847,378 |
| validation | 2022-01-01 | 2024-01-01 | 702,053 |
| historical final | 2024-01-01 | 2026-08-10 | 912,577 |

the matching counts for ES, YM, GC and CL come from the per-year counts in [the local audit](../reports/local-data-audit.json). NQ is the development market. ES, GC and CL are checks in other markets; YM is reported separately because it is another equity index. the plan uses one timeframe, three momentum lookbacks and six mean-reversion settings. it keeps every result, including failures. the development-period winner is chosen by base-scenario net Sharpe if it has at least 20 entries; validation and later data show how that choice holds up, without changing it. the report also ranks every configuration in each split.

the base case assumes $2.50 commission and one tick of slippage **per side**, with an extra one-minute delay. a zero-cost reference, higher-cost case and one-bar delay are also fixed in advance. these are assumed fills from OHLCV bars, not measured bid/ask spreads. each market has $100,000 stated starting capital and at most one full-size futures contract. margin is not treated as a stock purchase price.

the local `nq-powell` project already reports results on NQ and other markets through 2026. i therefore call 2024–2026 a **historical final evaluation**, not an untouched holdout. later genuinely new data would need a separate prospective run recorded after this lock. a source-coverage problem can justify a new version of the plan, but the reason and new lock must be committed before any strategy result is viewed.

the real-data roll gate is currently unresolved. no empirical P&L grid may run until the date-to-contract schedules pass [the roll check](roll-gate.md). the synthetic example and accounting tests can run now.
