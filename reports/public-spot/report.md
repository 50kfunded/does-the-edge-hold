# what held up

i ran a separate public spot study because the futures contract mapping is still missing. this uses real Coinbase BTC and ETH daily bars, not the Databento futures files.

i froze 14 settings and six scenarios before running the grid. both coins have 3,530 days from 2017-01-01 through 2026-08-31, with no missing days. all 192 runs finished. the BTC development pick was `mom-30`, and i kept it for ETH too.

| market / part | pick annual mean | median setting | pick Sharpe | positive gross → still positive net |
| --- | ---: | ---: | ---: | --- |
| BTC-USD / development | 1.224% | -0.043% | 0.956 | 7 → 6 |
| BTC-USD / validation | 0.072% | -0.353% | 0.064 | 5 → 4 |
| BTC-USD / historical_final | 1.794% | 0.308% | 0.674 | 10 → 8 |
| ETH-USD / development | 0.059% | 0.003% | 0.499 | 10 → 9 |
| ETH-USD / validation | 0.034% | -0.058% | 0.386 | 3 → 1 |
| ETH-USD / historical_final | 0.071% | -0.033% | 0.489 | 5 → 4 |

the BTC pick looked weaker in 2022–2023: Sharpe fell from 0.956 in development to 0.064. it recovered to 0.674 in the final historical period. the pick beat the median candidate later, but that alone doesn't establish an edge.

every declared 3/5/10-day paired interval against flat and always long includes zero for both coins in both later parts. for BTC vs flat, the five-day annual mean difference interval is −1.580% to 1.665% in validation, and −1.293% to 4.909% in the final part. i can't distinguish these results confidently from no advantage under those assumptions.

cost-only stress kept fills and gross P&L fixed and reduced net P&L. delay-only stress sometimes helped and sometimes hurt. i didn't use those changes to pick a new setting. the per-market reports show every matched effect, rank change and yearly selection.

i used one coin unit with $1m cash each, zero interest, assumed 10 bps fees and 5 bps slippage per side, and one extra day of order delay. these returns are annualized daily means on that capital, not CAGR. one BTC and one ETH have different dollar risk. OHLCV doesn't prove the assumed fills; prior knowledge and strategy selection still limit the intervals.

[BTC details](BTC-USD/report.md) · [ETH details](ETH-USD/report.md) · [frozen plan](../../research/public-spot/plan.json) · [snapshot requests and hashes](snapshot-manifest.json)

the futures study remains blocked. i need date-valid instrument identities for the actual continuous exports and independently supported advance roll instructions. this spot result doesn't resolve that.
