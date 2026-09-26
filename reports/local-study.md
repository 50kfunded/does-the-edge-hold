# my local futures check

i regenerated the six-file audit and five minute-cache comparisons after the repair. all source hashes still match the lock. i read the G: files without changing them.

**the futures P&L study is still blocked.** no market has the real identity mapping and independently supported advance roll instructions. NQ remains the required primary; a valid optional subset cannot replace it.

| source | rows | cache origin |
| --- | ---: | --- |
| NQ 1m | 3,462,008 | NQc0 |
| ES 1m | 3,484,266 | ESc0 |
| YM 1m | 3,409,043 | YMc0 |
| GC 1m | 3,482,922 | GCv0 |
| CL 1m | 3,497,569 | CLv0 |
| NQ 1s | 60,807,363 | ingestion code names NQ.c.0; reconstruction unverified |

the audit still finds no duplicates, out-of-order timestamps, missing values, invalid OHLC or nonpositive volume. gaps are labelled as candidates, not verified product closures. detailed bar samples stay local.

| market | development rows | validation rows | final rows |
| --- | ---: | ---: | ---: |
| NQ | 1,847,378 | 702,053 | 912,457 |
| ES | 1,866,679 | 702,856 | 914,611 |
| YM | 1,832,708 | 692,593 | 883,639 |
| GC | 1,874,050 | 696,406 | 912,347 |
| CL | 1,890,751 | 699,430 | 907,268 |

these counts now use the declared New York session dates. the final partial Monday session is outside the final split. the original audit's UTC coverage dates stay unchanged.

[audit](local-data-audit.json) · [cache provenance](local-provenance.json) · [regenerated status](repair/local-regeneration.json) · [missing artifacts](../docs/roll-gate.md)

the separate [public spot study](public-spot/report.md) is real empirical work, but it doesn't validate these futures files.
