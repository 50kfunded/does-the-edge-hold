# NQ

i kept the NQ development pick: `revert-6-1.5`. all 55 cases use this market's same complete-window mask. no later reselection.

this is conditional historical P&L under the within-date source-rule inference, with unknown contract identity.

| part | complete / candidate weekdays | gross $ | net $ | mean $ / window | scaled annual mean | Sharpe | entries | exposure |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| development | 1122 / 1406 | 8,900.00 | -18,895.00 | -16.84 | -4.244% | -0.727 | 1853 | 16.009% |
| validation | 503 / 520 | 2,780.00 | -10,000.00 | -19.88 | -5.010% | -0.700 | 852 | 16.890% |
| historical_final | 642 / 680 | -5,250.00 | -20,460.00 | -31.87 | -8.031% | -0.699 | 1014 | 15.216% |

252 is a convention applied to eligible windows. scaled means aren't realized annual returns or CAGR. no skipped date is filled with zero. exposure is held minutes / observed window minutes. one full contract has different dollar risk across markets; $100,000 is a reporting convention, with no margin or equal-risk sizing claim.

## all base settings

| setting | dev net $ | val net $ | final net $ | dev Sharpe | val Sharpe | final Sharpe |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| mom-3 | -75,850.00 | -39,935.00 | -50,175.00 | -2.730 | -2.119 | -1.186 |
| mom-6 | -68,315.00 | -27,435.00 | -4,610.00 | -2.375 | -1.407 | -0.109 |
| mom-12 | -39,985.00 | -32,110.00 | -22,010.00 | -1.415 | -1.664 | -0.589 |
| revert-6-0.5 | -61,235.00 | -22,130.00 | -31,805.00 | -1.909 | -1.146 | -0.915 |
| revert-6-1 | -48,905.00 | -12,670.00 | -16,090.00 | -1.658 | -0.717 | -0.499 |
| revert-6-1.5 | -18,895.00 | -10,000.00 | -20,460.00 | -0.727 | -0.700 | -0.699 |
| revert-12-0.5 | -48,415.00 | -13,515.00 | -32,100.00 | -1.514 | -0.690 | -0.914 |
| revert-12-1 | -43,015.00 | -20,145.00 | -26,920.00 | -1.409 | -1.111 | -0.801 |
| revert-12-1.5 | -30,260.00 | -15,570.00 | -17,810.00 | -1.125 | -0.957 | -0.564 |
| flat | 0.00 | 0.00 | 0.00 | n/a | n/a | n/a |
| intraday_long | -22,400.00 | -19,655.00 | 8,670.00 | -0.502 | -0.673 | 0.154 |

## did the gross winners survive costs?

| part | positive gross settings | positive after base costs | median scaled mean | pick rank among eligible settings |
| --- | ---: | ---: | ---: | ---: |
| development | 3 | 0 | -10.874% | 1 |
| validation | 4 | 0 | -10.093% | 2 |
| historical_final | 3 | 0 | -8.639% | 5 |

## costs and waiting

| part | scenario | comparison | net $ change from base | gross $ change | fill change |
| --- | --- | --- | ---: | ---: | ---: |
| development | gross_reference | cost only | 27,795.00 | 0.00 | 0 |
| development | cost_stress | cost only | -27,795.00 | 0.00 | 0 |
| development | delay_stress | delay only | -4,970.00 | -5,720.00 | -100 |
| development | combined_stress | combined cost and delay | -32,015.00 | -5,720.00 | -100 |
| validation | gross_reference | cost only | 12,780.00 | 0.00 | 0 |
| validation | cost_stress | cost only | -12,780.00 | 0.00 | 0 |
| validation | delay_stress | delay only | -1,125.00 | -1,515.00 | -52 |
| validation | combined_stress | combined cost and delay | -13,515.00 | -1,515.00 | -52 |
| historical_final | gross_reference | cost only | 15,210.00 | 0.00 | 0 |
| historical_final | cost_stress | cost only | -15,210.00 | 0.00 | 0 |
| historical_final | delay_stress | delay only | 2,130.00 | 1,695.00 | -58 |
| historical_final | combined_stress | combined cost and delay | -12,645.00 | 1,695.00 | -58 |

each cost-only comparison keeps delay fixed. delay-only keeps cost rates fixed; it changes entry and terminal execution. a better delayed result can happen by chance. these minute opens are assumed first-trade proxies, not quotes or guaranteed fills.

## later uncertainty

| part | pick minus baseline | block observations | paired windows | scaled mean difference | 95% interval |
| --- | --- | ---: | ---: | ---: | --- |
| validation | flat | 3 | 503 | -5.010% | -15.233% to 5.058% |
| validation | flat | 5 | 503 | -5.010% | -14.658% to 3.983% |
| validation | flat | 10 | 503 | -5.010% | -14.224% to 4.281% |
| validation | intraday_long | 3 | 503 | 4.837% | -11.776% to 21.211% |
| validation | intraday_long | 5 | 503 | 4.837% | -11.143% to 21.279% |
| validation | intraday_long | 10 | 503 | 4.837% | -10.827% to 20.031% |
| historical_final | flat | 3 | 642 | -8.031% | -22.787% to 6.430% |
| historical_final | flat | 5 | 642 | -8.031% | -21.875% to 6.405% |
| historical_final | flat | 10 | 642 | -8.031% | -23.779% to 7.006% |
| historical_final | intraday_long | 3 | 642 | -11.434% | -33.765% to 10.255% |
| historical_final | intraday_long | 5 | 642 | -11.434% | -32.758% to 9.180% |
| historical_final | intraday_long | 10 | 642 | -11.434% | -30.586% to 10.284% |

i use paired circular 3/5/10-observation blocks, 2,000 draws and seed 1729, with at least 30 paired windows. blocks follow ordered eligible observations, including calendar gaps. they don't restore missing days, correct selection or capture arbitrary long memory.

## same dates across markets

| part | common windows | pick net $ | pick Sharpe | intraday long net $ |
| --- | ---: | ---: | ---: | ---: |
| development | 970 | -17,080.00 | -0.718 | -17,580.00 |
| validation | 467 | -9,385.00 | -0.720 | -14,370.00 |
| historical_final | 464 | -27,345.00 | -1.229 | -26,875.00 |

the common population has 1,901 complete UTC dates in every included market. it is a separate coverage-conditioned comparison; the headline pick still comes from NQ's own development windows. [common outcomes](common-results.csv) retain all cases.

## yearly check of the fixed pick

| year | windows | pick net $ | pick Sharpe | intraday long net $ |
| --- | ---: | ---: | ---: | ---: |
| 2016 | 39 | -2,310.00 | -9.688 | -1,740.00 |
| 2017 | 117 | -2,615.00 | -4.613 | 500.00 |
| 2018 | 228 | -7,610.00 | -2.413 | -1,280.00 |
| 2019 | 244 | -5,615.00 | -1.659 | -1,685.00 |
| 2020 | 245 | 2,760.00 | 0.309 | -6,830.00 |
| 2021 | 249 | -3,505.00 | -0.520 | -11,365.00 |
| 2022 | 252 | -350.00 | -0.044 | -3,660.00 |
| 2023 | 251 | -9,650.00 | -1.525 | -15,995.00 |
| 2024 | 251 | -4,940.00 | -0.663 | 4,300.00 |
| 2025 | 244 | -28,950.00 | -2.219 | -19,485.00 |
| 2026 | 147 | 13,430.00 | 1.746 | 23,855.00 |

i don't execute a switching or newly reselected yearly portfolio.

protocol: `71cbc574f4f600b13617517c5b6808fd43bcd2d80608cc4c17588156f827e522`. semantic source: `31730f2167fe84b8f8e8b5b729a9805062db7fd4f015d6ad02bc7af19566cfaf`. execution: `2354060058c8498ad69c397726d3d77068989c4f3a2a03df8d7cb42b93007edb`. the manifest retains the input file hash separately.

![scaled means for every candidate](grid.png)

![conditional complete-window sum; no live equity claim](equity.png)

![displayed candidate ranks only](ranks.png)

[all outcomes](all-results.csv) · [every scenario's eligible-window P&L](daily-pnl-all-scenarios.csv) · [rank figure numbers](rank-chart-table.csv)
