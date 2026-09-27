# the within-day study

i ran 165 cases across NQ, ES, YM, with nine rules, two baselines and five cost/delay scenarios.

the NQ development pick was `revert-12-1.5`. i kept it in later dates and the other markets.

these prices are made up. this checks the software, not a market edge.

i score exact 08:00â€“12:00 UTC weekday windows and reset every date. completeness is known after noon. this isn't a live 09:00 filter, unconditional investment curve or claim that missing dates have zero returns.

the fixtures have made-up source labels and deliberate jumps between dates. each scored date resets independently. this doesn't resolve the real study's roll gate.

| market | development windows | validation windows | final windows | pick dev Sharpe | pick val Sharpe | pick final Sharpe |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| [NQ](NQ/report.md) | 30 | 29 | 30 | -2.968 | -6.888 | 0.357 |
| [ES](ES/report.md) | 30 | 29 | 30 | 1.159 | -2.856 | -0.160 |
| [YM](YM/report.md) | 30 | 29 | 30 | -4.397 | -2.027 | -2.200 |

of 18 computed own-window later intervals, 17 include zero, 0 are wholly below zero and 1 are wholly above zero. 18 declared comparisons lack enough paired observations.

these sample intervals only check the software.

## the assumptions

| scenario | commission / side | adverse ticks / side | extra delay minutes |
| --- | ---: | ---: | ---: |
| base | 2.5 | 1 | 1 |
| gross_reference | 0 | 0 | 1 |
| cost_stress | 5 | 2 | 1 |
| delay_stress | 2.5 | 1 | 5 |
| combined_stress | 5 | 2 | 5 |

partial windows remain visible in the source audit and aren't scored. missing warmup or terminal minutes aren't filled. successful ledgers end flat and reconcile gross minus commission/slippage to net; failures retain no completed score.

common complete dates: 89. the paired common-date intervals are saved in `summary.json`, with the actual denominators.

the actual run checked 107,995 source rows, evaluated 64,080 minute observations and cached features once per setting/date before the five scenarios. total measured time: 19.0s; sampled peak RSS: 219.3 MiB. this is one machine, not a throughput guarantee.

[unscored sample price variation](descriptive-price-variation.json) Â· [the example's plan and settings](summary.json)
