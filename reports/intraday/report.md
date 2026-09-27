# the within-day study

i ran 165 cases across NQ, ES, YM, with nine rules, two baselines and five cost/delay scenarios.

the NQ development pick was `revert-6-1.5`. i kept it in later dates and the other markets.

this is a historical, conditional source-day comparison. i already knew related research through 2026; the final period isn't untouched data.

i score exact 08:00–12:00 UTC weekday windows and reset every date. completeness is known after noon. this isn't a live 09:00 filter, unconditional investment curve or claim that missing dates have zero returns.

real contract identities are unknown. local cache matching and historical source-rule evidence support the narrower within-date inference. the original roll-aware study stays blocked. GC and CL have no scored strategy P&L here.

| market | development windows | validation windows | final windows | pick dev Sharpe | pick val Sharpe | pick final Sharpe |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| [NQ](NQ/report.md) | 1122 | 503 | 642 | -0.727 | -0.700 | -0.699 |
| [ES](ES/report.md) | 1221 | 504 | 653 | -2.789 | -3.159 | -2.069 |
| [YM](YM/report.md) | 1026 | 470 | 467 | -1.204 | -3.093 | -2.238 |

of 36 computed own-window later intervals, 24 include zero, 12 are wholly below zero and 0 are wholly above zero. 0 declared comparisons lack enough paired observations.

these historical intervals are descriptive. they don't correct selection or establish a lasting tradable edge.

## the assumptions

| scenario | commission / side | adverse ticks / side | extra delay minutes |
| --- | ---: | ---: | ---: |
| base | 2.5 | 1 | 1 |
| gross_reference | 0 | 0 | 1 |
| cost_stress | 5 | 2 | 1 |
| delay_stress | 2.5 | 1 | 5 |
| combined_stress | 5 | 2 | 5 |

partial windows remain visible in the source audit and aren't scored. missing warmup or terminal minutes aren't filled. successful ledgers end flat and reconcile gross minus commission/slippage to net; failures retain no completed score.

common complete dates: 1,901. the paired common-date intervals are saved in `summary.json`, with the actual denominators.

the actual run checked 17,335,808 source rows, evaluated 1,585,920 minute observations and cached features once per setting/date before the five scenarios. total measured time: 325.3s; sampled peak RSS: 452.9 MiB. this is one machine, not a throughput guarantee.

[unscored source price variation](descriptive-price-variation.json) · [the frozen plan](https://github.com/50kfunded/does-the-edge-hold/blob/main/research/intraday/plan.json) · [within-day methods](https://github.com/50kfunded/does-the-edge-hold/blob/main/docs/intraday-plan.md)

[post-results trade economics and source identities](trade-economics.json)
