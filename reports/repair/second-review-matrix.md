# after the second review

i started from `a690ef7`. the reviewer reproduced all 192 spot cases and found five remaining issues. the original roll-aware futures study is still blocked. this round adds a separate within-day study; it doesn't change that decision.

| issue | change | evidence / status |
| --- | --- | --- |
| mutable global setting missing from identity | declared extension state and dependencies | `test_extension_review.py`: undeclared setting rejected; changed setting rejects the old seal |
| custom signal reads future prices | deterministic output, prefix and future perturbation checks | next-close callback rejected; sampled checks have stated limits |
| rank chart includes a hidden baseline | pending | saved P&L and selection were unaffected |
| helpers and reports ignore parts of the plan | pending | use actual primary, universe and assumptions |
| file-format bytes stand in for data identity | pending | add a versioned semantic identity without changing old locks |

the new study will use exact-precision backup minutes, a fixed 08:00–12:00 UTC weekday window and daily resets. NQ is the required primary. ES and YM are related-market checks. GC and CL remain descriptive. complete-window eligibility is retrospective and conditional; it isn't a live signal available at 09:00.
