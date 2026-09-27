# what held up

i ran the locked 165 cases. none of the nine NQ rules made money after base costs in development, validation or the final historical period.

the chosen rule was `revert-6-1.5`: six completed five-minute closes and a 1.5 entry threshold. it was the least-negative eligible development Sharpe. the plan didn't require a positive winner, so i kept it.

| NQ part | complete windows | gross $ | net $ | Sharpe |
| --- | ---: | ---: | ---: | ---: |
| development | 1,122 | 8,900 | -18,895 | -0.727 |
| validation | 503 | 2,780 | -10,000 | -0.700 |
| historical final | 642 | -5,250 | -20,460 | -0.699 |

gross-positive NQ candidates numbered 3, 4 and 3 across those splits. none survived base costs. the intraday-long baseline made $8,670 net in the final period; the selected rule lost $20,460 there.

i carried that same rule to ES and YM. it lost in all their splits too. of 36 declared later paired intervals on each market's own complete dates, 24 include zero and 12 are wholly below zero. none is wholly above zero. the 1,901 common-date check gives the same counts. these are descriptive intervals, not a correction for selection or prior exposure.

i already knew related research through 2026. the complete-window filter is only known after noon, minute opens are assumed fills, and one full contract doesn't give equal risk across markets. the curves sum conditional eligible windows, not a live investment account. i didn't run a reselected walk-forward portfolio.

i still don't have real contract IDs. historical source-rule evidence and exact local cache matching support this narrower within-date comparison. they don't validate roll returns. the original roll-aware study remains blocked; GC and CL have only descriptive price-variation summaries.

[full report](report.md) · [NQ](NQ/report.md) · [ES](ES/report.md) · [YM](YM/report.md) · [frozen choices](../../research/intraday/plan.json)
