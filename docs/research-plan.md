# the choices i froze

i kept [v1](../research/v1-plan.json) and [v2](../research/v2-plan.json), with their original locks. [futures v3](../research-plan.json) fixes the reviewed timing, daily clock and matched scenarios. no empirical futures grid has run.

the futures plan keeps NQ primary, with ES/GC/CL as checks and YM reported separately. it uses one-hour signals: momentum at 12/24/72 completed bars and mean reversion at 24/72 bars with entry z of 0.5/1/1.5. that's nine settings. lookbacks count observed bars; history resets at each contract change.

| part | futures session-date labels | separate public spot UTC dates |
| --- | --- | --- |
| development | 2016-08-12 to 2022-01-01 | 2017-01-01 to 2022-01-01 |
| validation | 2022-01-01 to 2024-01-01 | 2022-01-01 to 2024-01-01 |
| historical final | 2024-01-01 to 2026-08-10 | 2024-01-01 to 2026-09-01 |

ends are exclusive. the futures bounds refer to New York session-date labels stored at UTC midnight. the terminal partial Monday session is outside the final split. the whole-run diagnostic still retains observed data.

futures base costs are $2.50 plus one tick per side, delayed one minute. zero cost and higher cost keep that delay. a 60-minute delay keeps base costs; combined stress changes both. starting capital is $100k per full contract. the development choice needs 20 entries and the highest base net daily Sharpe; ties use fewer fills then configuration ID.

## the separate spot case

i audited the coverage, then froze [the spot plan](../research/public-spot/plan.json) before strategy returns. it uses 14 settings: momentum at 7/14/30/60/120 daily bars, and mean reversion at 14/30/60 bars with the same three entry z values. BTC is primary; the BTC choice is carried to ETH. both are required in this case.

base costs are assumed 10 bps fee and 5 bps slippage per side, with one extra day after the completed daily signal. cost-only stress doubles the rates; delay-only stress adds two or three days instead; combined stress does both. one coin is funded from $1m cash, with no borrowing or interest. the development minimum is ten entries.

both plans predeclare gross-to-net survival, selected vs typical later results, rank stability, cross-market transfer and matched cost/delay effects. paired circular block lengths are 3/5/10, with 2,000 draws and seed 1729. yearly selection is a continuous-state diagnostic, not an executed switching portfolio.

i'd already seen futures results through 2026 in the older project. broad crypto history was also known. these are historical evaluations, not pristine holdouts. a prospective check needs its future dates and fixed choices committed before those results exist.

the protocol lock records choices and audited source hashes. a separate execution manifest seals code, actual callables, instrument/accounting metadata, roll evidence and dependency versions. output folders refuse overwrites; implementation changes get new run identities.
