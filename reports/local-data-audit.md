# local data audit

i read the six files in `G:\localview\data\bars` on 25 september 2026 and checked them again from a clean install. i didn't edit or fill any bars. [the public audit](local-data-audit.json) has the schemas, yearly counts, hashes and gap counts. the detailed samples stay in the local run folder.

| file | rows | first UTC bar | last UTC bar |
| --- | ---: | --- | --- |
| NQ 1m | 3,462,008 | 2016-08-12 00:00 | 2026-08-09 23:59 |
| ES 1m | 3,484,266 | 2016-08-12 00:00 | 2026-08-09 23:59 |
| YM 1m | 3,409,043 | 2016-08-14 22:00 | 2026-08-09 23:59 |
| GC 1m | 3,482,922 | 2016-08-14 22:00 | 2026-08-09 23:59 |
| CL 1m | 3,497,569 | 2016-08-14 22:00 | 2026-08-09 23:59 |
| NQ 1s | 60,807,363 | 2021-08-20 00:00 | 2026-08-21 20:59:59 |

i found no duplicate or out-of-order timestamps, null OHLCV values, invalid OHLC bars or nonpositive volume. the second bars overlap the minute history but extend further; they're a timing check, not another market.

the gap list is a set of things to check. some gaps are normal market closures or minutes with no trades, while longer open-session gaps need more work. i used a regular weekly schedule and flagged possible holiday hours, since actual [CME hours](https://www.cmegroup.com/trading-hours.html) can differ. [Databento's OHLCV notes](https://databento.com/docs/knowledge-base) say a no-trade interval has no bar. i didn't infer roll dates from large price changes.

the audit took about 35 seconds here. peak sampled memory was about 178 MiB for a minute file and 508 MiB for the second file; per-file measurements are in the JSON.
