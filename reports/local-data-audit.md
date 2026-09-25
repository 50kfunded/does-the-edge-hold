# local data audit

the read-only audit used the six files in `G:\localview\data\bars` on 25 september 2026. exact schemas, per-year row counts, file hashes and the largest flagged gaps and price changes are in [local-data-audit.json](local-data-audit.json). the command reads bounded batches; it does not clean or rewrite the files.

| file | rows | first UTC bar | last UTC bar | duplicate / out-of-order | invalid OHLC / nonpositive volume |
| --- | ---: | --- | --- | ---: | ---: |
| NQ 1m | 3,462,008 | 2016-08-12 00:00 | 2026-08-09 23:59 | 0 / 0 | 0 / 0 |
| ES 1m | 3,484,266 | 2016-08-12 00:00 | 2026-08-09 23:59 | 0 / 0 | 0 / 0 |
| YM 1m | 3,409,043 | 2016-08-14 22:00 | 2026-08-09 23:59 | 0 / 0 | 0 / 0 |
| GC 1m | 3,482,922 | 2016-08-14 22:00 | 2026-08-09 23:59 | 0 / 0 | 0 / 0 |
| CL 1m | 3,497,569 | 2016-08-14 22:00 | 2026-08-09 23:59 | 0 / 0 | 0 / 0 |
| NQ 1s | 60,807,363 | 2021-08-20 00:00 | 2026-08-21 20:59:59 | 0 / 0 | 0 / 0 |

there were no null values in the six exported OHLCV columns. the NQ second bars extend beyond the minute export and overlap most of its history. they are a timing cross-check, not another market observation. the short live file and cached NQ aggregates were excluded from this six-file audit.

gaps are **candidates**, not repaired bars. the audit uses a regular 18:00–17:00 new york weekly template and flags US federal holidays or longer weekend closures as possible special hours. actual CME holiday and product schedules can differ. short open-session gaps could simply mean no trade: Databento does not publish an OHLCV record for an interval with no trade. longer open-session gaps remain marked for investigation. no missing minute is forward-filled. the unusually large close changes in the JSON are also investigation flags; none were changed or treated as a roll date.

the audit ran one source at a time with batches of at most 65,536 rows. per-file elapsed times are in the JSON. this bounds the decoded batch size; it does not itself measure peak process memory.

references: [Databento OHLCV conventions](https://databento.com/docs/knowledge-base), [CME trading hours and holidays](https://www.cmegroup.com/trading-hours.html).
