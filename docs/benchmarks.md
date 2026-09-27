# the measured runs

i measured generation, ingestion, audit, cache replay, evaluation and reports separately. each size used a fresh Python process. memory is absolute process RSS sampled every 10 ms, including retained input and allocator memory. these were single measurements on my Windows PC, with some background work, not isolated speed guarantees.

| input | cases | ingestion s | audit s | provenance / replay s | evaluation s | evaluation peak MiB | report s |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 10000 | 55 | 0.021 | 0.018 | 0.027 | 6.290 | 145.3 | 0.562 |
| 100000 | 55 | 0.043 | 0.058 | 0.045 | 43.167 | 219.0 | 0.566 |
| 1000000 | 55 | 0.360 | 0.548 | 0.239 | 404.630 | 523.1 | 1.411 |
| public-spot | 192 | 0.005 | 0.016 | 0.313 | 127.245 | 151.4 | 4.164 |

the three synthetic sizes use the full nine-setting, five-scenario grid with two baselines. all 55 cases passed at each size, and the synthetic exports matched their cache. the public profile ran all 192 real spot cases and matched every published financial metric; execution IDs differ when code changes.

evaluation dominates. the engine loads one whole market and loops over execution events; the audit reads bounded Parquet batches. the million-row result doesn't establish a streaming evaluator, full five-market throughput or validated second-bar execution. i kept the implementation small and recorded that limit rather than extrapolating to the full vendor history.

the machine had six physical / twelve logical cores, about 24 GiB RAM and Python 3.12.10. [the JSON files](../reports/benchmarks) keep dependency versions, per-phase memory and background activity. source-resolution differences mean the spot and minute timings aren't a per-row speed comparison.

to repeat a synthetic size:

```powershell
python scripts/benchmark.py --size 1000000 --output runs/your-million-row-benchmark.json
```

to profile the complete real case after taking a snapshot:

```powershell
python scripts/benchmark.py --public-snapshot runs/public-snapshot --output runs/your-public-profile.json
```

the public profile also checks against the saved financial results. raw fixtures and responses stay under ignored runs folders.

## the full within-day case

i ran all 165 cases on 6,608 complete market/date windows: 1,585,920 eligible minute observations. verification inspected 17,335,808 source rows; the three scored markets account for 10,355,317 of them. features were computed once per rule/date and reused across five scenarios.

| phase | NQ s | ES s | YM s |
| --- | ---: | ---: | ---: |
| load and prepare windows | 16.90 | 15.49 | 12.71 |
| cache features | 57.30 | 59.54 | 48.49 |
| evaluate 55 cases | 28.67 | 29.07 | 24.91 |
| paired uncertainty | 0.68 | 0.68 | 0.63 |

the fresh-wheel replay took 325.29 seconds total and reached 452.92 MiB sampled peak RSS. verification took 15.13 seconds, descriptive summaries 8.71 seconds and reports 2.63 seconds. RSS was sampled every 50 ms. tests and the synthetic example overlapped briefly at the start, with ordinary background work afterward.

the earlier development run took 312.79 seconds with 484.79 MiB peak RSS. clone/install work and later tests/spot replay overlapped with it. [both measurements](../reports/benchmarks/intraday.json) keep the phase counts and environments. every financial outcome matched. these are observations from one machine, not isolated throughput guarantees or streaming execution.
