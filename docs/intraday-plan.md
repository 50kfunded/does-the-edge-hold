# the within-day plan

i froze [this separate plan](../research/intraday/plan.json) before running its strategy grid. it uses original-precision backup minutes. NQ is the primary; ES and YM are related-market checks. GC and CL stay descriptive. the original roll-aware study is still blocked.

i use 08:00–12:00 UTC weekdays. the first hour is warmup. decisions start at 09:00, entries must fill before 11:30, and a fixed 11:50 instruction closes the position after the scenario delay, before noon. each date starts and ends flat. a missing exit fails; i don't move it backwards or carry the position to tomorrow.

i build five-minute bars from five observed minutes. momentum compares the latest close with the first open of its last 3, 6 or 12 completed bars. this fits twelve bars into the one-hour warmup. mean reversion uses 6 or 12 completed closes, including the latest, with sample standard deviation and entry thresholds 0.5/1/1.5. warmup never creates a latent position. these definitions differ from the older hourly and spot signals and have separate code.

i choose the highest development base Sharpe with at least 20 filled entries. ties use fewer entries, then the setting name. i keep that NQ choice in later periods and the other markets. nine rules and two baselines across five cost/delay scenarios make 55 cases per market. the JSON keeps the exact assumptions and dates.

the complete-window mask is an ex-post condition shared by every case. NQ has 2,267 complete windows out of 2,606 weekday candidates; ES has 2,378 and YM has 1,963. the earlier review clipped candidates to each source's start. my fixed population also includes 2016-08-12 for YM/GC/CL, adding one empty candidate each. no strategy result drove this difference. empty weekdays aren't labelled exchange holidays without calendar evidence.

historical [continuous-symbol rules](https://databento.com/docs/standards-and-conventions/symbology) and [UTC date validity](https://databento.com/docs/api-reference-historical/symbology/symbology-resolve), plus an exact local cache match, support the within-date calendar-source inference. i use opaque source/date segment labels. i haven't recovered real contract IDs or authenticated the vendor delivery. this evidence cannot authorize cross-date or roll returns.

returns use $100,000 stated capital and one full contract. 252 is a conventional scaling for eligible windows, not a measured annual investment return. the uncertainty check pairs the same observations, with 3/5/10-observation circular blocks, 2,000 draws and seed 1729. gaps, selection, prior research through 2026 and assumed minute-open fills still limit what i can conclude.
