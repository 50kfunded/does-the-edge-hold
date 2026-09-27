# the clean checkout

i cloned the public feature branch and installed its wheel in a fresh Python 3.12 environment, with system packages disabled. the empirical package check used `72c0a9e`. no vendor files were copied into that checkout and Databento wasn't installed.

all 82 tests passed in 73.45 seconds. the installed `intraday-example` command made its own bars and plan, ran all 165 cases with no failed windows, and generated the sample report and plots. this took 29.85 seconds, including overlap with the test run. the example is a software check, not a market result.

separately, i pointed that installation at the read-only backup and cache. it verified the frozen plan, source observations, cache artifacts and eligibility masks before running the empirical study. the full 165-case replay matched the earlier run's outcomes, common-date results, uncertainty and all 55 daily scenario panels per market. code and dependency identities are allowed to differ; the comparison names its excluded metadata and numerical tolerance.

i also replayed all 192 spot cases using the semantic migration lock. all 2,688 result rows, daily base panels, uncertainty, ranks, walk-forward records and the carried choice matched the original study. the original spot plan, byte lock and results remain separate.

[the new receipt](../reports/repair/source-day-reproducibility.json) records revisions, wheel identity, dependencies and comparisons. the final publishing scan checks tracked files and reachable history with `python scripts/check_public.py`. raw bars, mappings and response snapshots remain local.

a report-only follow-up at `0ab8799` corrected the sample labels and interval counts. three integration/report tests passed, and its fresh wheel regenerated all 165 sample cases with matching outcomes. the empirical results keep the execution identities of the code that actually ran them.

## earlier check

i cloned the public repair branch at `2770e86`, built a wheel there and installed it in a fresh Python 3.12 environment. system packages were disabled. no vendor files were copied and Databento wasn't installed.

all 55 tests passed. the installed command ran 55 synthetic cases on 43,200 minute bars, with no failures, and generated the report and three plots in about 21.4 seconds. package source digests matched the development code; every financial metric matched within the declared numerical tolerance. the input Parquet hash differed with the pandas writer version, so i compared the financial results and recorded both environments.

i then fetched `a5c53c1` and passed its extra stale-seal regression. that change added test assertions, with no package-code change. [GitHub's check](https://github.com/50kfunded/does-the-edge-hold/actions/runs/36275256718) passed on Python 3.11 and 3.12.

the same wheel ran `local-report` against `G:\localview\data\bars` and the local cache. all six source hashes still matched the frozen lock. it regenerated the audit and stayed blocked before empirical futures P&L.

the tracked-file and reachable-history scan found no vendor bars, mapping/instruction files, keys or per-bar audit samples. raw public responses also stayed local. the final publishing scan uses `python scripts/check_public.py`.

[reproducibility.json](../reports/reproducibility.json) records the wheel, package versions, source digests and checked revisions. [the older receipt](../reports/repair/pre-review-reproducibility.json) remains separate evidence for the original pre-Push-5 check.

later commits update docs and derived sample artifacts. they don't turn synthetic checks into futures validation.
