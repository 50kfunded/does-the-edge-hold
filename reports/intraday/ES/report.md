# ES

i kept the NQ development pick: `revert-6-1.5`. all 55 cases use this market's same complete-window mask. no later reselection.

this is conditional historical P&L under the within-date source-rule inference, with unknown contract identity.

| part | complete / candidate weekdays | gross $ | net $ | mean $ / window | scaled annual mean | Sharpe | entries | exposure |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| development | 1221 / 1406 | 6,387.50 | -53,252.50 | -43.61 | -10.991% | -2.789 | 1988 | 15.337% |
| validation | 504 / 520 | -5,000.00 | -29,330.00 | -58.19 | -14.665% | -3.159 | 811 | 15.881% |
| historical_final | 653 / 680 | -1,287.50 | -32,097.50 | -49.15 | -12.387% | -2.069 | 1027 | 15.231% |

252 is a convention applied to eligible windows. scaled means aren't realized annual returns or CAGR. no skipped date is filled with zero. exposure is held minutes / observed window minutes. one full contract has different dollar risk across markets; $100,000 is a reporting convention, with no margin or equal-risk sizing claim.

## all base settings

| setting | dev net $ | val net $ | final net $ | dev Sharpe | val Sharpe | final Sharpe |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| mom-3 | -163,902.50 | -70,535.00 | -84,200.00 | -7.733 | -5.606 | -3.528 |
| mom-6 | -126,975.00 | -47,562.50 | -56,402.50 | -5.595 | -3.875 | -2.276 |
| mom-12 | -83,660.00 | -39,675.00 | -45,227.50 | -3.807 | -3.136 | -2.014 |
| revert-6-0.5 | -108,652.50 | -50,895.00 | -52,417.50 | -4.781 | -4.144 | -2.856 |
| revert-6-1 | -80,735.00 | -39,535.00 | -45,937.50 | -3.790 | -3.608 | -2.799 |
| revert-6-1.5 | -53,252.50 | -29,330.00 | -32,097.50 | -2.789 | -3.159 | -2.069 |
| revert-12-0.5 | -76,767.50 | -34,892.50 | -36,892.50 | -3.174 | -2.844 | -1.953 |
| revert-12-1 | -64,672.50 | -32,155.00 | -32,365.00 | -3.036 | -2.767 | -1.788 |
| revert-12-1.5 | -41,400.00 | -25,250.00 | -22,705.00 | -2.145 | -2.503 | -1.334 |
| flat | 0.00 | 0.00 | 0.00 | n/a | n/a | n/a |
| intraday_long | -24,205.00 | -23,357.50 | -3,990.00 | -0.699 | -1.254 | -0.129 |

## what each completed trade earned

these are aggregate dollars divided by actual completed round trips, not averages of yearly ratios. frequency means entries or filled sides per eligible window; it isn't portfolio notional turnover.

| part | round trips | entries / window | fills / window | gross $ / trip | commission $ / trip | tick cost $ / trip | rounding $ / trip | net $ / trip |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| development | 1,988 | 1.63 | 3.26 | 3.21 | 5.00 | 25.00 | 0.00 | -26.79 |
| validation | 811 | 1.61 | 3.22 | -6.17 | 5.00 | 25.00 | 0.00 | -36.17 |
| historical_final | 1,027 | 1.57 | 3.15 | -1.25 | 5.00 | 25.00 | 0.00 | -31.25 |

the recorded tick value is $12.50. base uses two $2.50 commissions and 2 adverse ticks per round trip: $30.00 before any rounding residual. the rounding column is recorded slippage minus that declared tick cost.

## all candidates per trade

each cell shows gross / total costs / net dollars per round trip. the adjacent frequency is completed trips per eligible window. totals and sample counts remain above.

| setting | dev gross / cost / net | dev trips / window | val gross / cost / net | val trips / window | final gross / cost / net | final trips / window |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| mom-3 | 0.03 / 30.00 / -29.97 | 4.48 | -1.25 / 30.00 / -31.25 | 4.48 | 1.21 / 30.00 / -28.79 | 4.48 |
| mom-6 | -1.08 / 30.00 / -31.08 | 3.35 | 0.82 / 30.00 / -29.18 | 3.23 | 4.34 / 30.00 / -25.66 | 3.37 |
| mom-12 | 2.68 / 30.00 / -27.32 | 2.51 | -1.74 / 30.00 / -31.74 | 2.48 | 2.89 / 30.00 / -27.11 | 2.55 |
| revert-6-0.5 | 3.26 / 30.00 / -26.74 | 3.33 | 0.13 / 30.00 / -29.87 | 3.38 | 5.86 / 30.00 / -24.14 | 3.32 |
| revert-6-1 | 5.17 / 30.00 / -24.83 | 2.66 | 0.54 / 30.00 / -29.46 | 2.66 | 2.90 / 30.00 / -27.10 | 2.60 |
| revert-6-1.5 | 3.21 / 30.00 / -26.79 | 1.63 | -6.17 / 30.00 / -36.17 | 1.61 | -1.25 / 30.00 / -31.25 | 1.57 |
| revert-12-0.5 | 1.37 / 30.00 / -28.63 | 2.20 | -1.69 / 30.00 / -31.69 | 2.18 | 4.40 / 30.00 / -25.60 | 2.21 |
| revert-12-1 | -1.52 / 30.00 / -31.52 | 1.68 | -7.56 / 30.00 / -37.56 | 1.70 | 0.12 / 30.00 / -29.88 | 1.66 |
| revert-12-1.5 | 2.03 / 30.00 / -27.97 | 1.21 | -9.15 / 30.00 / -39.15 | 1.28 | 1.48 / 30.00 / -28.52 | 1.22 |

### baselines on the same windows

| setting | dev gross / cost / net | dev trips / window | val gross / cost / net | val trips / window | final gross / cost / net | final trips / window |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| flat | n/a / n/a / n/a | 0.00 | n/a / n/a / n/a | 0.00 | n/a / n/a / n/a | 0.00 |
| intraday_long | 10.18 / 30.00 / -19.82 | 1.00 | -16.34 / 30.00 / -46.34 | 1.00 | 23.89 / 30.00 / -6.11 | 1.00 |

flat has no completed trades, so its per-trade ratios are undefined. missing, failed or inconsistent accounting also gives n/a; the diagnostic artifact records the reason.

## the pick versus intraday long

these differences use the same market's eligible windows: pick minus baseline. net difference equals gross difference minus the extra modelled costs. this is an accounting decomposition, not a claim about the cause of a market regime.

| part | pick trips / window | long trips / window | gross difference $ / window | cost difference $ / window | net difference $ / window |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| development | 1.63 | 1.00 | -4.94 | 18.85 | -23.79 |
| validation | 1.61 | 1.00 | 6.42 | 18.27 | -11.85 |
| historical_final | 1.57 | 1.00 | -25.86 | 17.18 | -43.04 |

[saved trade economics for every scenario and sample](../trade-economics.json). this is post-results descriptive arithmetic; the original evaluation identities stay unchanged.

## did the gross winners survive costs?

| part | positive gross settings | positive after base costs | median scaled mean | pick rank among eligible settings |
| --- | ---: | ---: | ---: | ---: |
| development | 7 | 0 | -16.663% | 2 |
| validation | 3 | 0 | -19.767% | 5 |
| historical_final | 8 | 0 | -17.454% | 5 |

## costs and waiting

| part | scenario | comparison | net $ change from base | gross $ change | fill change |
| --- | --- | --- | ---: | ---: | ---: |
| development | gross_reference | cost only | 59,640.00 | 0.00 | 0 |
| development | cost_stress | cost only | -59,640.00 | 0.00 | 0 |
| development | delay_stress | delay only | -1,027.50 | -3,487.50 | -164 |
| development | combined_stress | combined cost and delay | -58,207.50 | -3,487.50 | -164 |
| validation | gross_reference | cost only | 24,330.00 | 0.00 | 0 |
| validation | cost_stress | cost only | -24,330.00 | 0.00 | 0 |
| validation | delay_stress | delay only | 172.50 | -487.50 | -44 |
| validation | combined_stress | combined cost and delay | -23,497.50 | -487.50 | -44 |
| historical_final | gross_reference | cost only | 30,810.00 | 0.00 | 0 |
| historical_final | cost_stress | cost only | -30,810.00 | 0.00 | 0 |
| historical_final | delay_stress | delay only | -1,357.50 | -2,287.50 | -62 |
| historical_final | combined_stress | combined cost and delay | -31,237.50 | -2,287.50 | -62 |

each cost-only comparison keeps delay fixed. delay-only keeps cost rates fixed; it changes entry and terminal execution. a better delayed result can happen by chance. these minute opens are assumed first-trade proxies, not quotes or guaranteed fills.

## later uncertainty

| part | pick minus baseline | block observations | paired windows | scaled mean difference | 95% interval |
| --- | --- | ---: | ---: | ---: | --- |
| validation | flat | 3 | 504 | -14.665% | -21.297% to -8.395% |
| validation | flat | 5 | 504 | -14.665% | -20.988% to -8.540% |
| validation | flat | 10 | 504 | -14.665% | -21.463% to -8.146% |
| validation | intraday_long | 3 | 504 | -2.986% | -13.943% to 7.466% |
| validation | intraday_long | 5 | 504 | -2.986% | -14.114% to 7.629% |
| validation | intraday_long | 10 | 504 | -2.986% | -13.855% to 7.790% |
| historical_final | flat | 3 | 653 | -12.387% | -19.718% to -5.104% |
| historical_final | flat | 5 | 653 | -12.387% | -19.598% to -4.958% |
| historical_final | flat | 10 | 653 | -12.387% | -20.705% to -4.657% |
| historical_final | intraday_long | 3 | 653 | -10.847% | -21.837% to 1.225% |
| historical_final | intraday_long | 5 | 653 | -10.847% | -21.384% to 0.200% |
| historical_final | intraday_long | 10 | 653 | -10.847% | -21.591% to 0.546% |

i use paired circular 3/5/10-observation blocks, 2,000 draws and seed 1729, with at least 30 paired windows. blocks follow ordered eligible observations, including calendar gaps. they don't restore missing days, correct selection or capture arbitrary long memory.

## same dates across markets

| part | common windows | pick net $ | pick Sharpe | intraday long net $ |
| --- | ---: | ---: | ---: | ---: |
| development | 970 | -39,342.50 | -2.404 | -18,337.50 |
| validation | 467 | -25,445.00 | -3.174 | -18,147.50 |
| historical_final | 464 | -24,320.00 | -2.154 | -21,095.00 |

the common population has 1,901 complete UTC dates in every included market. it is a separate coverage-conditioned comparison; the headline pick still comes from NQ's own development windows. [common outcomes](common-results.csv) retain all cases.

## yearly check of the fixed pick

| year | windows | pick net $ | pick Sharpe | intraday long net $ |
| --- | ---: | ---: | ---: | ---: |
| 2016 (partial: 2016-08-12 to 2017-01-01, end exclusive) | 84 | -5,260.00 | -11.862 | -3,507.50 |
| 2017 | 175 | -8,527.50 | -12.075 | -887.50 |
| 2018 | 236 | -10,205.00 | -3.433 | -2,580.00 |
| 2019 | 232 | -10,217.50 | -4.738 | -3,785.00 |
| 2020 | 247 | -10,467.50 | -1.507 | -9,397.50 |
| 2021 | 247 | -8,575.00 | -2.682 | -4,047.50 |
| 2022 | 255 | -14,445.00 | -2.892 | -6,287.50 |
| 2023 | 249 | -14,885.00 | -3.480 | -17,070.00 |
| 2024 | 249 | -7,700.00 | -2.148 | -982.50 |
| 2025 | 249 | -23,562.50 | -3.423 | -13,220.00 |
| 2026 (partial: 2026-01-01 to 2026-08-10, end exclusive) | 155 | -835.00 | -0.190 | 10,212.50 |

partial labels describe the protocol's calendar span, not full observed coverage. profitable individual years remain visible; they don't replace the frozen split conclusion. i don't execute a switching or newly reselected yearly portfolio.

protocol: `71cbc574f4f600b13617517c5b6808fd43bcd2d80608cc4c17588156f827e522`. semantic source: `9b39f85c03df363ba4ec3fd9c8d9d9ea40a7d9fe7ada204984aa02e97e9e159c`. execution: `a646df6c30c316ab957667aae6ae623a1f9d6dbc780538aeffd631c21784c53e`. the manifest retains the input file hash separately.

![scaled means for every candidate](grid.png)

![conditional complete-window sum; no live equity claim](equity.png)

![displayed candidate ranks only](ranks.png)

[all outcomes](all-results.csv) · [every scenario's eligible-window P&L](daily-pnl-all-scenarios.csv) · [rank figure numbers](rank-chart-table.csv)
