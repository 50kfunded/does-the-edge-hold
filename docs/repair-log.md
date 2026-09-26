# repair log

i reproduced the review's five focused examples at `f2fd1a1`. the old roll exit moved from 00:04 to 00:03 when i removed a future bar. the documented instrument-ID response and a revised ten-setting grid were rejected. replacing the signal kept the same run ID while P&L changed. NQ had 312 observed UTC dates in 2025, including 52 Sundays. [the baseline](../reports/repair/baseline.json) records those checks.

the independent review also passed the 30 existing tests, regenerated the synthetic example and inspected its plots. it didn't repeat the full large-data audit or clean installation. the previous audit and installation measurements remain separate evidence.

| brief | finding | action / evidence | status |
| --- | --- | --- | --- |
| 1 | futures study unfinished; global gate blocks valid subsets | declare roles and exclusions, gate each included market; public case if the primary stays blocked | pending |
| 2 | last-observed roll exits use future availability | executable roll instructions and missing-fill failure | pending |
| 3 | resolver rejects the documented route | date-valid instrument IDs, raw response evidence and offline fixtures | pending |
| 4 | UTC dates and 252 scaling disagree | one declared daily clock for all diagnostics | pending |
| 5 | protocol lock doesn't identify executed code | seal code, actual callables, data, mappings, specs and environment | pending |
| 6 | counts and market roles are hardcoded | validate the declared grid and prove an external input | pending |
| 7 | no real research result | predeclare questions, run supported real data, retain every trial | pending |
| 8 | costs and delays change together | matched cost-only and delay-only scenarios | pending |
| 9 | plots don't explain period lengths or survival | normalized summaries, rank/distribution evidence and failures | pending |
| 10 | walk-forward isn't an executed switching portfolio | label and report a candidate-selection diagnostic | pending |
| 11 | audit scale doesn't establish evaluator scale | separate measured ingestion, audit, provenance, evaluation and report benchmarks | pending |
| 12 | bootstrap isn't a cure for selection | paired circular blocks and predeclared length sensitivity | pending |
| 13 | successful empirical-command integration is untested | wholly synthetic source/cache fixture through the full path | pending |
| 14 | closure labels aren't verified product calendars | explicit uncertain labels and predeclared quality gates | pending |
| 15 | independent input use isn't demonstrated | public extension walkthrough and reproduction route | pending |
| 16 | completion and CV claims need to match evidence | this matrix, prototype status and measured handover | in progress |

the original review's requirement table maps to these rows: adapters/provenance and scale → 11/14/15; accounting/timing → 2/4/8/13; frozen choices → 5/6; empirical and cross-market evidence → 1/7/9; selection and uncertainty → 7/12; public reproducibility → 13/15; CV limits → 16. synthetic checks stay separate from market findings.

the push sequence is awaiting the requested review. local repairs can continue. no paid data request or new account is part of this work.
