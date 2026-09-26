# local study

i checked the six local Parquet files and compared the five minute exports with their source cache.

**the roll gate is unresolved, so i haven't run the empirical P&L grid.** it needs verified contract mapping and causal execution timing. the public example uses synthetic contracts and stays separate.

GC and CL also need a causal volume-roll policy: a historical switch date alone doesn't justify exiting at the last old-contract minute's open. the current runner blocks that case.

| file | rows | first UTC bar | last UTC bar |
| --- | ---: | --- | --- |
| NQ 1m | 3,462,008 | 2016-08-12T00:00:00+00:00 | 2026-08-09T23:59:00+00:00 |
| ES 1m | 3,484,266 | 2016-08-12T00:00:00+00:00 | 2026-08-09T23:59:00+00:00 |
| YM 1m | 3,409,043 | 2016-08-14T22:00:00+00:00 | 2026-08-09T23:59:00+00:00 |
| GC 1m | 3,482,922 | 2016-08-14T22:00:00+00:00 | 2026-08-09T23:59:00+00:00 |
| CL 1m | 3,497,569 | 2016-08-14T22:00:00+00:00 | 2026-08-09T23:59:00+00:00 |
| NQ 1s | 60,807,363 | 2021-08-20T00:00:00+00:00 | 2026-08-21T20:59:59+00:00 |

## minute rows in each part

| market | development | validation | historical final |
| --- | ---: | ---: | ---: |
| NQ | 1,847,378 | 702,053 | 912,577 |
| ES | 1,866,679 | 702,856 | 914,731 |
| YM | 1,832,708 | 692,593 | 883,742 |
| GC | 1,874,050 | 696,406 | 912,466 |
| CL | 1,890,751 | 699,430 | 907,388 |

NQ, ES and YM matched calendar continuous series. GC and CL matched volume continuous series. the second bars overlap the minute data; i haven't used them for fill claims.

i'd already seen results through 2026 in an older project. the final period is a historical check, not an untouched holdout. detailed bar samples stay in the local run folder; the public audit contains aggregate metadata.
