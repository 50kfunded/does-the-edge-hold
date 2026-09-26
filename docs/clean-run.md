# clean run

i cloned the public repo into a separate folder and installed a wheel in a fresh Python 3.12 environment. i then fetched the final timestamp and roll-gate fixes locally, before Push 5. no market files were copied into that checkout, and Databento wasn't installed.

all 30 tests passed. `edge-hold example` ran 44 cases on 43,200 synthetic minutes, with no failed runs, and generated the tables and plots in about 9.3 seconds. its metrics matched the development run; the Parquet file hash can differ when writer metadata changes between library versions.

i used the same installed code with `local-report --data-root G:\localview\data\bars --cache-root G:\nq-powell\data\cache`. the six source hashes still matched the frozen lock. the audit took about 35 seconds; the regenerated study stayed blocked because the mapping and a causal volume-roll policy were missing.

i also checked the tracked files and reachable Git history for vendor bars, mapping files, keys and per-bar audit samples. the public audit only has aggregate metadata. the detailed samples are in an ignored local folder.

[reproducibility.json](../reports/reproducibility.json) records the checked revision and package versions. the [GitHub check](../.github/workflows/check.yml) repeats the tests, synthetic example and public-file scan on Python 3.11 and 3.12.

to repeat the local publishing check, run `python scripts/check_public.py` from the repo root. the empirical runner still needs real roll evidence before it can be tested on the full market history.
