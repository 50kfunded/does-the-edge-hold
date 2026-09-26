# how i count it

a source timestamp is the start of its bar. a minute close is known at its end; an hourly signal is known at the scheduled hour end. the first eligible observed open is at or after that time plus the declared delay. missing bars aren't filled. a mixed-contract hour isn't used as a signal bar.

momentum compares a completed close with the completed close n observed bars earlier. mean reversion uses the previous n closes' mean and sample standard deviation, enters below negative entry z and exits at the prior mean. both are long or flat, with warmup flat and resets at contract changes.

## accounting and time

futures P&L uses price differences times the contract multiplier, including zero and negative prices. commissions are dollars and slippage is ticks per side. rolls use advance instructions and actual eligible observations, as described in [the gate](roll-gate.md); the synthetic tests don't establish real mapping.

spot pays the inventory's purchase price from cash, then marks cash plus inventory. quantity is fixed at one coin. fees use executed notional and slippage is an assumed adverse bps price change. a buy fails if cash is insufficient; there's no borrowing.

fees and open-price changes belong to the execution timestamp. interval-close changes belong to the interval that ended. futures group by New York session date: 18:00 starts the next date, including Sunday night and DST changes, with conventional 252-session scaling. spot uses UTC calendar days and 365. all metrics, selection, baselines, bootstrap and yearly diagnostics use that same declared clock.

returns divide daily P&L by stated starting capital. annual mean scales that daily mean; it isn't CAGR. volatility and Sharpe use the sample standard deviation. zero-volatility Sharpe is undefined. drawdown uses observed daily marks and restarts each split at stated capital. exposure is the fraction of sampled marks held long, not elapsed time. final inventory is marked without an invented sale.

## what these checks mean

the paired circular bootstrap resamples the strategy and baseline together in blocks. 3/5/10-day sensitivity keeps every interval, including those crossing zero. it doesn't correct earlier selection, make historical data pristine or establish a future edge.

walk-forward selects from the previous three calendar years and inspects the next year's continuously simulated candidate. it doesn't reset positions or execute switching orders. rankings use only earlier data and the declared fill-count tie break.

the local gap labels are closure/no-trade/missing **candidates**. the weekly template and US federal holidays aren't a verified product calendar. bad OHLC, missing values, duplicates and order errors block P&L. gaps remain visible under the declared policy; no silent filling or jump-based roll detection.

the public spot case blocks any missing calendar day. [Coinbase's candle notes](https://docs.cdp.coinbase.com/api-reference/exchange-api/rest-api/products/get-product-candles) say missing intervals can have no ticks, so that choice is stricter than merely accepting the API response.

bar opens are assumed execution prices. OHLCV doesn't measure spread, queue position, impact or the exact timing of the first trade inside a bucket. the second data remains an overlapping audit source, not independent evidence or a validated fill study.
