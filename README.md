# does the edge hold?

i made a small Python tool to check whether a backtest holds up on later data, other markets, costs and slower orders.

## what i found

i finished two historical cases. neither establishes a lasting tradable edge.

- [BTC/ETH spot](reports/public-spot/report.md): 192 cases. the BTC pick's Sharpe was 0.956 in development, 0.064 in validation and 0.674 in the final period. all 24 later advantage intervals include zero. i kept the original results and added [corrected rank figures](reports/public-spot/corrections/report.md).
- [within-day NQ/ES/YM](reports/intraday/report.md): 165 cases on complete 08:00â€“12:00 UTC windows. none of the nine NQ rules made money after base costs in any split. the selected rule also lost in every ES/YM split. [what survived](reports/intraday/conclusions.md) keeps the numbers and limits.
- the [original roll-aware futures study](reports/local-study.md) is still blocked. i matched the local minute exports to their cache, but real contract IDs and advance roll evidence are unresolved.

the within-day case is conditional on complete windows, which i only know after noon. it uses a narrower inference about each UTC date, not recovered contract IDs. GC and CL stay descriptive. i already knew related research through 2026, so the final periods aren't untouched holdouts.

## try it

Python 3.11 or newer, in PowerShell:

```powershell
git clone https://github.com/50kfunded/does-the-edge-hold.git
cd does-the-edge-hold
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\edge-hold.exe intraday-example --output runs/intraday-example
```

the example needs no account or market files. it generates made-up bars, freezes its own plan and runs the same 165-case study and report path. the output is `runs/intraday-example/study/report.md`; [the saved sample](reports/intraday-synthetic/report.md) shows what it writes. `edge-hold example` also runs the older 55-case accounting example. on macOS or Linux, use `.venv/bin/python` and `.venv/bin/edge-hold`.

## repeat the spot case

```powershell
.\.venv\Scripts\edge-hold.exe public-fetch --output runs/public-snapshot
.\.venv\Scripts\edge-hold.exe public-study --snapshot runs/public-snapshot --plan research/public-spot/plan.semantic-v2.json --lock research/public-spot/plan.semantic-v2.lock.json --output runs/public-study
```

the download uses 30 unauthenticated requests. the migrated lock checks observations across Parquet writers and still requires the original raw-response hashes and exact replay. revised history must fail. [the walkthrough](docs/independent-input.md) explains the two locks.

## repeat my within-day case

```powershell
.\.venv\Scripts\edge-hold.exe intraday-study --data-root G:\localview.backup-preaudit-2026-08-22\data\bars --cache-root G:\nq-powell\data\cache --output runs/intraday-study
```

this reads my original-precision backup and cache without changing them. it checks the separate frozen plan, audit and complete-window masks. those files aren't in the repo. someone without them can run the synthetic example, but can't reproduce the empirical results from the public repo alone. use a new output directory for each run.

`edge-hold local-report --data-root G:\localview\data\bars --cache-root G:\nq-powell\data\cache` keeps the original cross-date study behind its roll gate.

[within-day choices](docs/intraday-plan.md) Â· [accounting](docs/methods.md) Â· [extensions](docs/extensions.md) Â· [measured runs](docs/benchmarks.md) Â· [clean checkout](docs/clean-run.md) Â· [review fixes](reports/repair/second-review-matrix.md)

the repo contains code, aggregate audits and derived results. raw vendor bars, mapping files and public response snapshots stay local.
