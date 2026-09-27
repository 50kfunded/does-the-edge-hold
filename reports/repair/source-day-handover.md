# where i left it

i finished the approved source-day branch in separate commits. the spot results remain separate, the within-day case is complete under its stated condition, and the original roll-aware futures study is still blocked.

- i froze [the new plan](../../research/intraday/plan.json) before the grid at `2a6eb45`. its lock was made on 2026-09-26 at 23:07:48 UTC. plan hash: `71cbc574f4f600b13617517c5b6808fd43bcd2d80608cc4c17588156f827e522`.
- i used the exact-precision backup minutes and local cache read-only. NQ/ES/YM were scored within individual UTC dates; GC/CL were descriptive. no contract IDs were invented. [coverage](../intraday/source-audit) keeps every complete, partial and empty candidate.
- all 165 cases finished without failed windows. none of the nine NQ rules survived base costs in any split. the carried pick lost in every ES/YM split. [the conclusion](../intraday/conclusions.md) keeps the amounts, comparisons and limits.
- the fresh wheel passed 82 tests and generated the public synthetic report without vendor files. its empirical replay matched all 2,475 own-date rows, 2,475 common-date rows, scenario panels and paired intervals. all 192 spot cases also matched the original results under the separate semantic migration.
- [the review matrix](second-review-matrix.md) records all five fixes. declared signal state and sampled causal checks don't make arbitrary Python safe or prove causality.
- [the reproduction receipt](source-day-reproducibility.json) and [measured runs](../../docs/benchmarks.md) keep exact versions and evidence. the empirical package revision is `72c0a9e`; a later report-only fix labels synthetic evidence and incomplete intervals correctly.

the public commands and read-only empirical command are in the [README](../../README.md). output folders must be new. the empirical files aren't redistributed; someone without them can regenerate the synthetic report but not the empirical case.

i still need genuine date-valid contract identities and advance roll instructions before the original futures objective can run. this narrower case doesn't close that gap. new research should get a separately frozen protocol and disclose these results as prior exposure.

## after the trade-economics review

i added a descriptive analysis of the saved paths, not a new strategy study. the NQ pick's gross gain per completed trip was $4.8030, $3.2629 and -$5.1775 across the three splits, versus $15 base costs. commission alone left the first two paths negative; the final path was negative before any cost. profitable years such as 2020 and partial 2026 remain visible.

- [trade-economics.json](../intraday/trade-economics.json) has schema version 1 and 4,950 own/common result rows: 4,500 validated traded paths and 450 flat paths with undefined per-trade ratios. it names source result pointers, plan/evaluation identities and reporting-code digests. raw checkout hashes are separate from normalized UTF-8/LF source hashes.
- [the fixed-path figure](../intraday/NQ/cost-budget.png) uses only nonnegative total costs and distinguishes positive break-even budgets from the already-negative final gross path. i visually checked it and the labelled made-up example.
- the [NQ](../intraday/NQ/report.md), [ES](../intraday/ES/report.md) and [YM](../intraday/YM/report.md) reports show trade frequency, cost decomposition, all candidates, separate baselines and pick-minus-long arithmetic. their original window and common-date results stay intact.
- `edge-hold intraday-report --study reports/intraday` regenerates this analysis from saved results without vendor files. the synthetic path uses the same calculations. [the guide](../../docs/intraday-execution.md#explaining-the-choices) helps a reader work through the assumptions; it doesn't assert anyone's understanding.
- 12 focused checks passed during this change, including the 165-case, 36-date synthetic integration. the final nine core/figure checks also passed. i checked all 46 protected result/protocol files against `e71008d` after Git newline normalization. the publishing scan found no vendor data or mapping files among 252 tracked files and reachable history.

the overseeing review's independent 82-test check and the earlier clean-checkout empirical replay remain earlier evidence. i didn't repeat the full G: audit/grid in this follow-up, change locks, replace the selected rule or open/mutate the G: sources. the strengthened [conclusion](../intraday/conclusions.md) supports reporting a negative experiment, with the original mapping and execution limitations still in place.
