# how i count it

i use the minute bar's timestamp as its start. [Databento's OHLCV notes](https://databento.com/docs/knowledge-base) confirm that convention. an hourly close is known at the scheduled hour end. orders use the first observed minute open at or after that time plus the delay. missing minutes aren't filled, and an hour split across two contracts isn't a signal bar.

momentum is long when the completed close is above the close `n` observed hourly bars earlier; otherwise it's flat. mean reversion compares the completed close with the mean and sample standard deviation of the previous `n` bars. it enters below the chosen negative z-score and exits at the prior mean. both restart at each contract transition.

P&L is the price difference times the contract multiplier. commissions are dollars per side; slippage is ticks per side. cash holds realised P&L less commissions, and equity adds the marked open position. a roll exits at the final old-contract minute's open and re-enters at the first new-contract minute's open. both sides cost money. zero and negative prices still work because nothing divides by the futures price.

| market | dollars per 1.0 price move | tick size | CME reference |
| --- | ---: | ---: | --- |
| NQ | 20 | 0.25 | [Nasdaq-100](https://www.cmegroup.com/markets/equities/nasdaq/e-mini-nasdaq-100.contractSpecs.html) |
| ES | 50 | 0.25 | [E-mini equity indexes](https://www.cmegroup.com/trading/equity-index/eminifaq.html) |
| YM | 5 | 1 | [Dow](https://www.cmegroup.com/trading/equity-index/files/EQ-159_DowJonesFinal.pdf) |
| GC | 100 | 0.1 | [gold](https://www.cmegroup.com/education/courses/event-contracts-underlying-markets/product-gold) |
| CL | 1000 | 0.01 | [WTI](https://www.cmegroup.com/education/courses/master-the-trade-futures/expanding-your-futures-knowledge/master-the-trade-contract-specifications.hideSubnav.educationIframe.html?hideAddThisExt=y&hideFooter=y&hideHeader=y&hideRightRail=y) |

returns are daily net P&L divided by the stated $100,000 starting capital. Sharpe uses the daily mean, sample standard deviation and `sqrt(252)`; volatility uses the same scaling. zero-volatility Sharpe is undefined. drawdown uses daily equity marks, so it misses intraday lows. each reported period starts its drawdown path at the stated capital. exposure is the fraction of observed hourly marks held long; turnover counts contract sides traded. open positions are marked, not automatically liquidated at the end.

i select on NQ development data, then keep that setting for later periods and other markets. independent rankings and three-year/next-year walk-forward results are diagnostics. paired circular five-day blocks keep strategy and baseline days together in 2,000 bootstrap draws, with seed 1729. an interval doesn't account for all my earlier research or prove an edge will last.

## what this can't establish yet

the real contract mapping is unresolved, so there are no empirical strategy returns here. the second bars have only been audited; i haven't used them to validate fills. bar data can't tell me the historical spread, queue position or market impact. the cost and delay cases are assumptions, and even a longer delay can help by chance.

the session check uses a regular weekly template and tentative holiday labels, not a complete product calendar. NQ, ES and YM share equity-index exposure, and the second bars overlap the minute data. nine settings are counted in this study; the number of choices tried in my older research is unknown.

## later data

for a prospective test, i'd commit a new version of the plan and exact future dates before those results exist, keeping the signal and selection choices fixed. when the licensed data arrives, i'd audit it, supply reviewed roll evidence, then use `edge-hold freeze --plan prospective-plan.json --audit runs/new-audit.json --output prospective-plan.lock.json`. `edge-hold research` accepts those files with `--plan` and `--lock`. the old plan and results stay archived.
