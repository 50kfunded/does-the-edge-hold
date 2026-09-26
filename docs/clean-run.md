# the clean checkout

i cloned the public repair branch at `2770e86`, built a wheel there and installed it in a fresh Python 3.12 environment. system packages were disabled. no vendor files were copied and Databento wasn't installed.

all 55 tests passed. the installed command ran 55 synthetic cases on 43,200 minute bars, with no failures, and generated the report and three plots in about 21.4 seconds. package source digests matched the development code; every financial metric matched within the declared numerical tolerance. the input Parquet hash differed with the pandas writer version, so i compared the financial results and recorded both environments.

i then fetched `a5c53c1` and passed its extra stale-seal regression. that change added test assertions, with no package-code change. [GitHub's check](https://github.com/50kfunded/does-the-edge-hold/actions/runs/36275256718) passed on Python 3.11 and 3.12.

the same wheel ran `local-report` against `G:\localview\data\bars` and the local cache. all six source hashes still matched the frozen lock. it regenerated the audit and stayed blocked before empirical futures P&L.

the tracked-file and reachable-history scan found no vendor bars, mapping/instruction files, keys or per-bar audit samples. raw public responses also stayed local. the final publishing scan uses `python scripts/check_public.py`.

[reproducibility.json](../reports/reproducibility.json) records the wheel, package versions, source digests and checked revisions. [the older receipt](../reports/repair/pre-review-reproducibility.json) remains separate evidence for the original pre-Push-5 check.

later commits update docs and derived sample artifacts. they don't turn synthetic checks into futures validation.
