# ETH-USD audit

i ran 14 settings and two baselines across 6 cost and delay cases on historical public spot data. all 96 runs are in [the CSV](all-results.csv), including any failures.

this is a historical evaluation. the primary development pick stays fixed in later periods and other markets. it isn't an untouched holdout.

the development pick is `mom-30`.

| setting | development net $ | validation net $ | final net $ |
| --- | ---: | ---: | ---: |
| mom-7 | 2,830.61 | -628.95 | -1,274.19 |
| mom-14 | 3,922.92 | -171.39 | -144.35 |
| mom-30 | 2,928.89 | 689.51 | 1,907.84 |
| mom-60 | 3,351.74 | -891.37 | 2,301.99 |
| mom-120 | 3,571.12 | -43.11 | 254.51 |
| revert-14-0.5 | 18.60 | -1,619.07 | -1,028.85 |
| revert-14-1 | 187.98 | -1,149.79 | -724.79 |
| revert-14-1.5 | -707.30 | -1,152.82 | 216.37 |
| revert-30-0.5 | 328.21 | -1,466.09 | -744.80 |
| revert-30-1 | -81.80 | -1,626.19 | -1,389.33 |
| revert-30-1.5 | 135.80 | -1,649.03 | -1,435.03 |
| revert-60-0.5 | -353.31 | -1,666.86 | -1,093.36 |
| revert-60-1 | -67.26 | -1,332.65 | -1,773.14 |
| revert-60-1.5 | -121.52 | -924.69 | -1,711.44 |
| flat | 0.00 | 0.00 | 0.00 |
| always_long | 3,667.59 | -1,394.73 | 186.22 |

## costs and delay

| case | gross $ | net $ | fills |
| --- | ---: | ---: | ---: |
| gross_reference | 6,107.74 | 6,107.74 | 241 |
| base | 6,107.74 | 5,526.24 | 241 |
| higher_cost | 6,107.74 | 4,944.74 | 241 |
| two_days_late | 6,411.06 | 5,827.50 | 241 |
| three_days_late | 6,854.65 | 6,268.84 | 241 |
| combined_stress | 6,854.65 | 5,683.03 | 241 |

## later results against the baselines

| part | baseline | annual return difference | 95% bootstrap interval |
| --- | --- | ---: | --- |
| validation | flat | 0.03% | -0.08% to 0.15% |
| validation | flat | 0.03% | -0.08% to 0.14% |
| validation | flat | 0.03% | -0.08% to 0.14% |
| validation | always_long | 0.10% | -0.04% to 0.26% |
| validation | always_long | 0.10% | -0.05% to 0.27% |
| validation | always_long | 0.10% | -0.05% to 0.27% |
| historical_final | flat | 0.07% | -0.11% to 0.25% |
| historical_final | flat | 0.07% | -0.11% to 0.25% |
| historical_final | flat | 0.07% | -0.11% to 0.25% |
| historical_final | always_long | 0.06% | -0.10% to 0.23% |
| historical_final | always_long | 0.06% | -0.09% to 0.22% |
| historical_final | always_long | 0.06% | -0.08% to 0.22% |

i used paired circular blocks at the declared lengths, 2,000 bootstrap draws and seed 1729. the intervals depend on these days being a useful sample; they don't remove selection bias or predict future returns.

the JSON and CSV keep gross/net P&L, return on stated capital, daily volatility and Sharpe, daily drawdown, hourly exposure, fills, costs, years and splits. prices are marked at the end; an open position isn't forced closed just to improve a result.

![results across the grid](grid.png)

![net P&L through the run](equity.png)
