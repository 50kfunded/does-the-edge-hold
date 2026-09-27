# after the second review

i started from `a690ef7`. the review reproduced the 192 spot cases and found five remaining issues. i fixed those and added a separate within-day case. the original roll-aware futures study is still blocked.

| issue | change | evidence / limit |
| --- | --- | --- |
| mutable setting missing from identity | declare global state and helpers; capture defaults and closures | `test_extension_review.py` rejects undeclared state, stale seals and settings changed inside a signal |
| custom signal reads future prices | repeat, prefix and future-perturbation checks | the next-close callback fails; checks are sampled on larger inputs and Python isn't a sandbox |
| chart ranks a hidden baseline | rank exactly the displayed candidates; save the rank table | `test_rank_chart.py`; [replacement spot figures](../public-spot/corrections/report.md); original P&L and selection unchanged |
| helpers and reports ignore the plan | use actual primary, declared subset, costs, clock and report metadata | `test_empirical_integration.py` uses ES as primary, different capital/costs and an excluded optional market |
| file bytes stand in for observations | versioned exact semantic hashes, artifact hashes retained separately | `test_semantic.py`; equivalent writers retain identity and results; changed observations fail; [post-results spot migration](../../research/public-spot/semantic-migration.json) preserves the old lock |

the clean checkout passed 82 tests and generated the 165-case synthetic example. the separate 165-case empirical replay retained the locked masks and reproduced the outcomes. [the clean-run receipt](../../docs/clean-run.md) records the exact revision and checks.

NQ is required. ES and YM are related checks. GC and CL stay descriptive. completeness is retrospective, fills are assumed minute opens, and real contract identities remain unknown. no positive edge claim follows from this work.
