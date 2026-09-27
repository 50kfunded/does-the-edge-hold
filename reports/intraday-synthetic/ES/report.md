# ES

i kept the NQ development pick: `revert-12-1.5`. all 55 cases use this market's same complete-window mask. no later reselection.

these are made-up prices and software checks.

| part | complete / candidate weekdays | gross $ | net $ | mean $ / window | scaled annual mean | Sharpe | entries | exposure |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| development | 30 / 30 | 1,487.50 | 467.50 | 15.58 | 3.927% | 1.159 | 34 | 17.500% |
| validation | 29 / 30 | -250.00 | -1,390.00 | -47.93 | -12.079% | -2.856 | 38 | 24.138% |
| historical_final | 30 / 30 | 1,200.00 | -60.00 | -2.00 | -0.504% | -0.160 | 42 | 22.708% |

252 is a convention applied to eligible windows. scaled means aren't realized annual returns or CAGR. no skipped date is filled with zero. exposure is held minutes / observed window minutes. one full contract has different dollar risk across markets; $100,000 is a reporting convention, with no margin or equal-risk sizing claim.

## all base settings

| setting | dev net $ | val net $ | final net $ | dev Sharpe | val Sharpe | final Sharpe |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| mom-3 | -1,652.50 | -3,770.00 | -6,612.50 | -2.560 | -6.379 | -11.734 |
| mom-6 | 17.50 | -2,440.00 | -6,270.00 | 0.033 | -3.859 | -10.518 |
| mom-12 | -565.00 | -4,382.50 | -5,637.50 | -0.810 | -5.964 | -10.727 |
| revert-6-0.5 | -2,082.50 | -3,807.50 | -1,580.00 | -4.277 | -7.726 | -4.367 |
| revert-6-1 | -1,332.50 | -2,745.00 | -1,477.50 | -2.636 | -6.125 | -4.359 |
| revert-6-1.5 | -2,095.00 | -1,697.50 | -1,460.00 | -5.082 | -4.352 | -4.733 |
| revert-12-0.5 | -367.50 | -1,622.50 | -655.00 | -0.803 | -2.913 | -1.695 |
| revert-12-1 | 102.50 | -1,592.50 | -1,082.50 | 0.226 | -2.981 | -2.796 |
| revert-12-1.5 | 467.50 | -1,390.00 | -60.00 | 1.159 | -2.856 | -0.160 |
| flat | 0.00 | 0.00 | 0.00 | n/a | n/a | n/a |
| intraday_long | 3,800.00 | -1,620.00 | -2,175.00 | 4.288 | -1.966 | -3.767 |

## what each completed trade earned

these are aggregate dollars divided by actual completed round trips, not averages of yearly ratios. frequency means entries or filled sides per eligible window; it isn't portfolio notional turnover.

| part | round trips | entries / window | fills / window | gross $ / trip | commission $ / trip | tick cost $ / trip | rounding $ / trip | net $ / trip |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| development | 34 | 1.13 | 2.27 | 43.75 | 5.00 | 25.00 | 0.00 | 13.75 |
| validation | 38 | 1.31 | 2.62 | -6.58 | 5.00 | 25.00 | 0.00 | -36.58 |
| historical_final | 42 | 1.40 | 2.80 | 28.57 | 5.00 | 25.00 | 0.00 | -1.43 |

the recorded tick value is $12.50. base uses two $2.50 commissions and 2 adverse ticks per round trip: $30.00 before any rounding residual. the rounding column is recorded slippage minus that declared tick cost.

## all candidates per trade

each cell shows gross / total costs / net dollars per round trip. the adjacent frequency is completed trips per eligible window. totals and sample counts remain above.

| setting | dev gross / cost / net | dev trips / window | val gross / cost / net | val trips / window | final gross / cost / net | final trips / window |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| mom-3 | 17.58 / 30.00 / -12.42 | 4.43 | -0.40 / 30.00 / -30.40 | 4.28 | -18.98 / 30.00 / -48.98 | 4.50 |
| mom-6 | 30.17 / 30.00 / 0.17 | 3.47 | 0.60 / 30.00 / -29.40 | 2.86 | -33.33 / 30.00 / -63.33 | 3.30 |
| mom-12 | 22.76 / 30.00 / -7.24 | 2.60 | -29.22 / 30.00 / -59.22 | 2.55 | -45.17 / 30.00 / -75.17 | 2.50 |
| revert-6-0.5 | 6.60 / 30.00 / -23.40 | 2.97 | -10.51 / 30.00 / -40.51 | 3.24 | 15.77 / 30.00 / -14.23 | 3.70 |
| revert-6-1 | 10.69 / 30.00 / -19.31 | 2.30 | -4.75 / 30.00 / -34.75 | 2.72 | 14.11 / 30.00 / -15.89 | 3.10 |
| revert-6-1.5 | -23.72 / 30.00 / -53.72 | 1.30 | 0.22 / 30.00 / -29.78 | 1.97 | 1.92 / 30.00 / -28.08 | 1.73 |
| revert-12-0.5 | 23.98 / 30.00 / -6.02 | 2.03 | 3.83 / 30.00 / -26.17 | 2.14 | 21.38 / 30.00 / -8.62 | 2.53 |
| revert-12-1 | 32.44 / 30.00 / 2.44 | 1.40 | -1.23 / 30.00 / -31.23 | 1.76 | 11.65 / 30.00 / -18.35 | 1.97 |
| revert-12-1.5 | 43.75 / 30.00 / 13.75 | 1.13 | -6.58 / 30.00 / -36.58 | 1.31 | 28.57 / 30.00 / -1.43 | 1.40 |

### baselines on the same windows

| setting | dev gross / cost / net | dev trips / window | val gross / cost / net | val trips / window | final gross / cost / net | final trips / window |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| flat | n/a / n/a / n/a | 0.00 | n/a / n/a / n/a | 0.00 | n/a / n/a / n/a | 0.00 |
| intraday_long | 156.67 / 30.00 / 126.67 | 1.00 | -25.86 / 30.00 / -55.86 | 1.00 | -42.50 / 30.00 / -72.50 | 1.00 |

flat has no completed trades, so its per-trade ratios are undefined. missing, failed or inconsistent accounting also gives n/a; the diagnostic artifact records the reason.

## the pick versus intraday long

these differences use the same market's eligible windows: pick minus baseline. net difference equals gross difference minus the extra modelled costs. this is an accounting decomposition, not a claim about the cause of a market regime.

| part | pick trips / window | long trips / window | gross difference $ / window | cost difference $ / window | net difference $ / window |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| development | 1.13 | 1.00 | -107.08 | 4.00 | -111.08 |
| validation | 1.31 | 1.00 | 17.24 | 9.31 | 7.93 |
| historical_final | 1.40 | 1.00 | 82.50 | 12.00 | 70.50 |

[saved trade economics for every scenario and sample](../trade-economics.json). this is post-results descriptive arithmetic; the original evaluation identities stay unchanged.

## did the gross winners survive costs?

| part | positive gross settings | positive after base costs | median scaled mean | pick rank among eligible settings |
| --- | ---: | ---: | ---: | ---: |
| development | 8 | 3 | -4.746% | 1 |
| validation | 3 | 0 | -21.203% | 1 |
| historical_final | 6 | 0 | -12.411% | 1 |

## costs and waiting

| part | scenario | comparison | net $ change from base | gross $ change | fill change |
| --- | --- | --- | ---: | ---: | ---: |
| development | gross_reference | cost only | 1,020.00 | 0.00 | 0 |
| development | cost_stress | cost only | -1,020.00 | 0.00 | 0 |
| development | delay_stress | delay only | 255.00 | 225.00 | -2 |
| development | combined_stress | combined cost and delay | -735.00 | 225.00 | -2 |
| validation | gross_reference | cost only | 1,140.00 | 0.00 | 0 |
| validation | cost_stress | cost only | -1,140.00 | 0.00 | 0 |
| validation | delay_stress | delay only | 435.00 | 375.00 | -4 |
| validation | combined_stress | combined cost and delay | -645.00 | 375.00 | -4 |
| historical_final | gross_reference | cost only | 1,260.00 | 0.00 | 0 |
| historical_final | cost_stress | cost only | -1,260.00 | 0.00 | 0 |
| historical_final | delay_stress | delay only | 155.00 | 125.00 | -2 |
| historical_final | combined_stress | combined cost and delay | -1,075.00 | 125.00 | -2 |

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
| historical_final | flat | 3 | 30 | -0.504% | -14.204% to 13.215% |
| historical_final | flat | 5 | 30 | -0.504% | -13.988% to 12.379% |
| historical_final | flat | 10 | 30 | -0.504% | -16.433% to 14.363% |
| historical_final | intraday_long | 3 | 30 | 17.766% | -1.499% to 40.346% |
| historical_final | intraday_long | 5 | 30 | 17.766% | -0.993% to 37.181% |
| historical_final | intraday_long | 10 | 30 | 17.766% | 5.041% to 30.082% |

i use paired circular 3/5/10-observation blocks, 200 draws and seed 1729, with at least 30 paired windows. blocks follow ordered eligible observations, including calendar gaps. they don't restore missing days, correct selection or capture arbitrary long memory.

## same dates across markets

| part | common windows | pick net $ | pick Sharpe | intraday long net $ |
| --- | ---: | ---: | ---: | ---: |
| development | 30 | 467.50 | 1.159 | 3,800.00 |
| validation | 29 | -1,390.00 | -2.856 | -1,620.00 |
| historical_final | 30 | -60.00 | -0.160 | -2,175.00 |

the common population has 89 complete UTC dates in every included market. it is a separate coverage-conditioned comparison; the headline pick still comes from NQ's own development windows. [common outcomes](common-results.csv) retain all cases.

## yearly check of the fixed pick

| year | windows | pick net $ | pick Sharpe | intraday long net $ |
| --- | ---: | ---: | ---: | ---: |
| 2020 (partial: 2020-01-02 to 2020-05-07, end exclusive) | 89 | -982.50 | -0.774 | 5.00 |

partial labels describe the protocol's calendar span, not full observed coverage. profitable individual years remain visible; they don't replace the frozen split conclusion. i don't execute a switching or newly reselected yearly portfolio.

protocol: `09d0b4e88f1c004a9e8be39eb874d41060e66ed302ba974289560d0533eaf57a`. semantic source: `d38c8f11750b6f2ae3c8f36c7a8419c81a1822f3442218bfa7e92cebce8764a1`. execution: `f633acbb8b57ab059f8d09f13419b2442432f47087ba3dd06081603cf504354f`. the manifest retains the input file hash separately.

![scaled means for every candidate](grid.png)

![conditional complete-window sum; no live equity claim](equity.png)

![displayed candidate ranks only](ranks.png)

[all outcomes](all-results.csv) · [every scenario's eligible-window P&L](daily-pnl-all-scenarios.csv) · [rank figure numbers](rank-chart-table.csv)
