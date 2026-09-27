# NQ

i kept the NQ development pick: `revert-12-1.5`. all 55 cases use this market's same complete-window mask. no later reselection.

these are made-up prices and software checks.

| part | complete / candidate weekdays | gross $ | net $ | mean $ / window | scaled annual mean | Sharpe | entries | exposure |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| development | 30 / 30 | 240.00 | -405.00 | -13.50 | -3.402% | -2.968 | 43 | 20.972% |
| validation | 29 / 30 | -480.00 | -1,110.00 | -38.28 | -9.646% | -6.888 | 42 | 25.359% |
| historical_final | 30 / 30 | 725.00 | 65.00 | 2.17 | 0.546% | 0.357 | 44 | 23.681% |

252 is a convention applied to eligible windows. scaled means aren't realized annual returns or CAGR. no skipped date is filled with zero. exposure is held minutes / observed window minutes. one full contract has different dollar risk across markets; $100,000 is a reporting convention, with no margin or equal-risk sizing claim.

## all base settings

| setting | dev net $ | val net $ | final net $ | dev Sharpe | val Sharpe | final Sharpe |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| mom-3 | -2,260.00 | -2,755.00 | -2,385.00 | -13.414 | -11.470 | -10.099 |
| mom-6 | -1,600.00 | -2,520.00 | -1,400.00 | -9.466 | -12.582 | -6.205 |
| mom-12 | -1,885.00 | -1,710.00 | -465.00 | -9.277 | -9.373 | -2.003 |
| revert-6-0.5 | -1,725.00 | -2,245.00 | -890.00 | -8.484 | -11.339 | -4.448 |
| revert-6-1 | -1,545.00 | -2,115.00 | -1,065.00 | -9.616 | -10.801 | -5.526 |
| revert-6-1.5 | -1,340.00 | -1,930.00 | -150.00 | -10.126 | -10.684 | -1.066 |
| revert-12-0.5 | -1,415.00 | -1,585.00 | -945.00 | -7.651 | -9.469 | -5.067 |
| revert-12-1 | -865.00 | -1,355.00 | -670.00 | -4.684 | -8.025 | -3.817 |
| revert-12-1.5 | -405.00 | -1,110.00 | 65.00 | -2.968 | -6.888 | 0.357 |
| flat | 0.00 | 0.00 | 0.00 | n/a | n/a | n/a |
| intraday_long | -1,115.00 | -1,770.00 | -255.00 | -4.314 | -5.747 | -0.860 |

## did the gross winners survive costs?

| part | positive gross settings | positive after base costs | median scaled mean | pick rank among eligible settings |
| --- | ---: | ---: | ---: | ---: |
| development | 1 | 0 | -12.978% | 1 |
| validation | 0 | 0 | -16.771% | 1 |
| historical_final | 7 | 1 | -7.476% | 1 |

## costs and waiting

| part | scenario | comparison | net $ change from base | gross $ change | fill change |
| --- | --- | --- | ---: | ---: | ---: |
| development | gross_reference | cost only | 645.00 | 0.00 | 0 |
| development | cost_stress | cost only | -645.00 | 0.00 | 0 |
| development | delay_stress | delay only | -470.00 | -485.00 | -2 |
| development | combined_stress | combined cost and delay | -1,100.00 | -485.00 | -2 |
| validation | gross_reference | cost only | 630.00 | 0.00 | 0 |
| validation | cost_stress | cost only | -630.00 | 0.00 | 0 |
| validation | delay_stress | delay only | -190.00 | -205.00 | -2 |
| validation | combined_stress | combined cost and delay | -805.00 | -205.00 | -2 |
| historical_final | gross_reference | cost only | 660.00 | 0.00 | 0 |
| historical_final | cost_stress | cost only | -660.00 | 0.00 | 0 |
| historical_final | delay_stress | delay only | -130.00 | -160.00 | -4 |
| historical_final | combined_stress | combined cost and delay | -760.00 | -160.00 | -4 |

each cost-only comparison keeps delay fixed. delay-only keeps cost rates fixed; it changes entry and terminal execution. a better delayed result can happen by chance. these minute opens are assumed first-trade proxies, not quotes or guaranteed fills.

## later uncertainty

| part | pick minus baseline | block observations | paired windows | scaled mean difference | 95% interval |
| --- | --- | ---: | ---: | ---: | --- |
| validation | flat | 3 | 29 | too_few_days | |
| validation | flat | 5 | 29 | too_few_days | |
| validation | flat | 10 | 29 | too_few_days | |
| validation | intraday_long | 3 | 29 | too_few_days | |
| validation | intraday_long | 5 | 29 | too_few_days | |
| validation | intraday_long | 10 | 29 | too_few_days | |
| historical_final | flat | 3 | 30 | 0.546% | -6.855% to 9.450% |
| historical_final | flat | 5 | 30 | 0.546% | -6.554% to 6.779% |
| historical_final | flat | 10 | 30 | 0.546% | -3.449% to 4.003% |
| historical_final | intraday_long | 3 | 30 | 2.688% | -10.734% to 18.736% |
| historical_final | intraday_long | 5 | 30 | 2.688% | -10.544% to 14.363% |
| historical_final | intraday_long | 10 | 30 | 2.688% | -9.870% to 17.612% |

i use paired circular 3/5/10-observation blocks, 200 draws and seed 1729, with at least 30 paired windows. blocks follow ordered eligible observations, including calendar gaps. they don't restore missing days, correct selection or capture arbitrary long memory.

## same dates across markets

| part | common windows | pick net $ | pick Sharpe | intraday long net $ |
| --- | ---: | ---: | ---: | ---: |
| development | 30 | -405.00 | -2.968 | -1,115.00 |
| validation | 29 | -1,110.00 | -6.888 | -1,770.00 |
| historical_final | 30 | 65.00 | 0.357 | -255.00 |

the common population has 89 complete UTC dates in every included market. it is a separate coverage-conditioned comparison; the headline pick still comes from NQ's own development windows. [common outcomes](common-results.csv) retain all cases.

## yearly check of the fixed pick

| year | windows | pick net $ | pick Sharpe | intraday long net $ |
| --- | ---: | ---: | ---: | ---: |
| 2020 | 89 | -1,450.00 | -2.980 | -3,140.00 |

i don't execute a switching or newly reselected yearly portfolio.

protocol: `09d0b4e88f1c004a9e8be39eb874d41060e66ed302ba974289560d0533eaf57a`. semantic source: `c11dc66add6d1079e3b3f015950440c1485c2b27250fcbaaf796380b94b26b69`. execution: `69f0ad5e89bf5a25df8f38dbc276ec7b232dab4b3f32e9a8e5cd11779c78c784`. the manifest retains the input file hash separately.

![scaled means for every candidate](grid.png)

![conditional complete-window sum; no live equity claim](equity.png)

![displayed candidate ranks only](ranks.png)

[all outcomes](all-results.csv) · [every scenario's eligible-window P&L](daily-pnl-all-scenarios.csv) · [rank figure numbers](rank-chart-table.csv)
