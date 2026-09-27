# YM

i kept the NQ development pick: `revert-6-1.5`. all 55 cases use this market's same complete-window mask. no later reselection.

this is conditional historical P&L under the within-date source-rule inference, with unknown contract identity.

| part | complete / candidate weekdays | gross $ | net $ | mean $ / window | scaled annual mean | Sharpe | entries | exposure |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| development | 1026 / 1406 | 7,525.00 | -17,135.00 | -16.70 | -4.209% | -1.204 | 1644 | 15.314% |
| validation | 470 / 520 | -6,005.00 | -16,925.00 | -36.01 | -9.075% | -3.093 | 728 | 15.452% |
| historical_final | 467 / 680 | -8,085.00 | -19,440.00 | -41.63 | -10.490% | -2.238 | 757 | 16.412% |

252 is a convention applied to eligible windows. scaled means aren't realized annual returns or CAGR. no skipped date is filled with zero. exposure is held minutes / observed window minutes. one full contract has different dollar risk across markets; $100,000 is a reporting convention, with no margin or equal-risk sizing claim.

## all base settings

| setting | dev net $ | val net $ | final net $ | dev Sharpe | val Sharpe | final Sharpe |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| mom-3 | -66,350.00 | -32,980.00 | -26,545.00 | -4.146 | -4.060 | -2.416 |
| mom-6 | -51,170.00 | -17,055.00 | -20,135.00 | -3.042 | -2.043 | -1.691 |
| mom-12 | -33,305.00 | -15,165.00 | -17,395.00 | -2.048 | -1.785 | -1.494 |
| revert-6-0.5 | -35,870.00 | -23,420.00 | -25,050.00 | -1.941 | -3.034 | -2.281 |
| revert-6-1 | -23,735.00 | -19,455.00 | -24,545.00 | -1.416 | -2.824 | -2.362 |
| revert-6-1.5 | -17,135.00 | -16,925.00 | -19,440.00 | -1.204 | -3.093 | -2.238 |
| revert-12-0.5 | -28,565.00 | -12,995.00 | -17,285.00 | -1.701 | -1.672 | -1.523 |
| revert-12-1 | -25,805.00 | -12,880.00 | -11,805.00 | -1.700 | -1.758 | -1.067 |
| revert-12-1.5 | -13,190.00 | -12,150.00 | -9,860.00 | -0.953 | -1.930 | -0.930 |
| flat | 0.00 | 0.00 | 0.00 | n/a | n/a | n/a |
| intraday_long | 590.00 | -9,235.00 | -7,555.00 | 0.023 | -0.765 | -0.432 |

## did the gross winners survive costs?

| part | positive gross settings | positive after base costs | median scaled mean | pick rank among eligible settings |
| --- | ---: | ---: | ---: | ---: |
| development | 7 | 0 | -7.016% | 2 |
| validation | 3 | 0 | -9.075% | 8 |
| historical_final | 4 | 0 | -10.490% | 6 |

## costs and waiting

| part | scenario | comparison | net $ change from base | gross $ change | fill change |
| --- | --- | --- | ---: | ---: | ---: |
| development | gross_reference | cost only | 24,660.00 | 0.00 | 0 |
| development | cost_stress | cost only | -24,660.00 | 0.00 | 0 |
| development | delay_stress | delay only | -190.00 | -1,030.00 | -112 |
| development | combined_stress | combined cost and delay | -24,010.00 | -1,030.00 | -112 |
| validation | gross_reference | cost only | 10,920.00 | 0.00 | 0 |
| validation | cost_stress | cost only | -10,920.00 | 0.00 | 0 |
| validation | delay_stress | delay only | 3,895.00 | 3,700.00 | -26 |
| validation | combined_stress | combined cost and delay | -6,830.00 | 3,700.00 | -26 |
| historical_final | gross_reference | cost only | 11,355.00 | 0.00 | 0 |
| historical_final | cost_stress | cost only | -11,355.00 | 0.00 | 0 |
| historical_final | delay_stress | delay only | -2,660.00 | -2,930.00 | -36 |
| historical_final | combined_stress | combined cost and delay | -13,745.00 | -2,930.00 | -36 |

each cost-only comparison keeps delay fixed. delay-only keeps cost rates fixed; it changes entry and terminal execution. a better delayed result can happen by chance. these minute opens are assumed first-trade proxies, not quotes or guaranteed fills.

## later uncertainty

| part | pick minus baseline | block observations | paired windows | scaled mean difference | 95% interval |
| --- | --- | ---: | ---: | ---: | --- |
| validation | flat | 3 | 470 | -9.075% | -13.534% to -4.617% |
| validation | flat | 5 | 470 | -9.075% | -13.346% to -4.726% |
| validation | flat | 10 | 470 | -9.075% | -13.367% to -4.640% |
| validation | intraday_long | 3 | 470 | -4.123% | -11.949% to 3.386% |
| validation | intraday_long | 5 | 470 | -4.123% | -12.171% to 4.435% |
| validation | intraday_long | 10 | 470 | -4.123% | -13.121% to 4.615% |
| historical_final | flat | 3 | 467 | -10.490% | -17.125% to -4.208% |
| historical_final | flat | 5 | 467 | -10.490% | -17.255% to -4.504% |
| historical_final | flat | 10 | 467 | -10.490% | -16.889% to -4.217% |
| historical_final | intraday_long | 3 | 467 | -6.413% | -16.504% to 3.311% |
| historical_final | intraday_long | 5 | 467 | -6.413% | -16.824% to 3.490% |
| historical_final | intraday_long | 10 | 467 | -6.413% | -16.362% to 4.144% |

i use paired circular 3/5/10-observation blocks, 2,000 draws and seed 1729, with at least 30 paired windows. blocks follow ordered eligible observations, including calendar gaps. they don't restore missing days, correct selection or capture arbitrary long memory.

## same dates across markets

| part | common windows | pick net $ | pick Sharpe | intraday long net $ |
| --- | ---: | ---: | ---: | ---: |
| development | 970 | -16,440.00 | -1.189 | -1,215.00 |
| validation | 467 | -17,010.00 | -3.120 | -9,205.00 |
| historical_final | 464 | -19,440.00 | -2.246 | -7,515.00 |

the common population has 1,901 complete UTC dates in every included market. it is a separate coverage-conditioned comparison; the headline pick still comes from NQ's own development windows. [common outcomes](common-results.csv) retain all cases.

## yearly check of the fixed pick

| year | windows | pick net $ | pick Sharpe | intraday long net $ |
| --- | ---: | ---: | ---: | ---: |
| 2016 | 39 | -1,420.00 | -8.684 | -1,290.00 |
| 2017 | 67 | -1,700.00 | -6.629 | 490.00 |
| 2018 | 220 | -4,590.00 | -1.882 | 845.00 |
| 2019 | 232 | -6,150.00 | -3.127 | -1,205.00 |
| 2020 | 235 | -2,315.00 | -0.423 | -1,410.00 |
| 2021 | 233 | -960.00 | -0.396 | 3,160.00 |
| 2022 | 239 | -7,875.00 | -2.478 | -1,915.00 |
| 2023 | 231 | -9,050.00 | -4.056 | -7,320.00 |
| 2024 | 216 | -6,820.00 | -2.522 | -7,235.00 |
| 2025 | 142 | -9,880.00 | -2.798 | -9,825.00 |
| 2026 | 109 | -2,740.00 | -1.311 | 9,505.00 |

i don't execute a switching or newly reselected yearly portfolio.

protocol: `71cbc574f4f600b13617517c5b6808fd43bcd2d80608cc4c17588156f827e522`. semantic source: `55a86372f17ce7ee52edb4f9e44881f0d74152d80ea9d87ab311a9cbc075f306`. execution: `84650db70559423ed6d3a99343cb21b9906380b1caa22c206bd1824738b9e5a1`. the manifest retains the input file hash separately.

![scaled means for every candidate](grid.png)

![conditional complete-window sum; no live equity claim](equity.png)

![displayed candidate ranks only](ranks.png)

[all outcomes](all-results.csv) · [every scenario's eligible-window P&L](daily-pnl-all-scenarios.csv) · [rank figure numbers](rank-chart-table.csv)
