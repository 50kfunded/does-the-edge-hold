# research plan

i froze the choices in [research-plan.json](../research-plan.json) before running the strategy grid. [the lock](../research-plan.lock.json) records the plan and data hashes, so a later run can catch changes.

i kept [the first plan](../research/v1-plan.json) and [its lock](../research/v1-plan.lock.json). version 2 makes one detail clearer: the lookback counts observed hourly bars, so it can cross a market closure. i noticed the wording while checking the synthetic run. the settings and splits stayed the same, and the real-data grid hasn't run.

i'm using 1-hour bars made from the minute files. a signal is known when its hour ends, and the earliest fill is the next available minute open plus the delay. signals restart after each contract roll.

the grid has nine settings: momentum with 12, 24 or 72 hours of history, and mean reversion with 24 or 72 hours of history at entry z-scores of 0.5, 1 or 1.5. i test NQ first, then ES, GC and CL. YM is a separate check because it's another equity index.

| part | UTC dates |
| --- | --- |
| development | 12 aug 2016 to 1 jan 2022 |
| validation | 1 jan 2022 to 1 jan 2024 |
| historical final | 1 jan 2024 to 10 aug 2026 |

i pick the development winner by net daily Sharpe in the base case, with at least 20 entries. ties go to fewer fills, then the setting's name. i keep the other results, including failed runs, and don't use later results to change the pick.

the base case is $2.50 commission and one tick of slippage per side, with a one-minute delay. i also test zero cost and delay, $5 plus two ticks per side with a five-minute delay, and the base costs with a 60-minute delay. each market starts with a stated $100,000 and holds one full-size contract or stays flat. these are assumptions from bars, not observed bid/ask fills.

i've already seen NQ and other market results through 2026 in my older `nq-powell` project. that means the last period is a historical check, not untouched data. if the data audit forces a change, i'll record why and freeze a new plan before looking at strategy results.

the [roll check](roll-gate.md) is still unresolved, so the real-data P&L grid is blocked. the synthetic example can run now.
