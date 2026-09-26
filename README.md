# does the edge hold?

i made a small Python tool to check whether a backtest holds up on later data, other markets, costs and slower orders.

this is a research prototype with a completed spot case. the original futures objective remains unfinished.

## what i found

i finished a separate [public BTC/ETH study](reports/public-spot/report.md): 14 settings, six scenarios and 192 runs. the BTC development pick was 30-day momentum. its Sharpe fell from 0.956 to 0.064 in validation, then rose to 0.674 in the final historical period. all declared later intervals against flat and always long include zero. positive returns here don't establish a lasting edge.

the original futures study is still blocked. i audited 17.3 million minute bars and 60.8 million NQ second bars, and matched the five minute exports to their cache. i still need real contract identities and advance roll evidence. [the local report](reports/local-study.md) and [roll check](docs/roll-gate.md) explain that limit.

## try it

Python 3.11 or newer, in PowerShell:

```powershell
git clone https://github.com/50kfunded/does-the-edge-hold.git
cd does-the-edge-hold
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\edge-hold.exe example --output runs/example
```

the example needs no account or market files. it runs 55 cases on 43,200 made-up minute bars and writes a report, CSV, JSON and plots. [the sample report](reports/synthetic/report.md) is a software check, not a market result. on macOS or Linux, use `.venv/bin/python` and `.venv/bin/edge-hold`.

## repeat the real spot study

```powershell
.\.venv\Scripts\edge-hold.exe public-fetch --output runs/public-snapshot
.\.venv\Scripts\edge-hold.exe public-study --snapshot runs/public-snapshot --output runs/public-study
```

the public download uses 30 unauthenticated candle requests for the fixed window. the study checks the frozen data hashes. if Coinbase revises history or your Parquet writer produces different bytes, the old lock must fail; [the walkthrough](docs/independent-input.md) explains how to distinguish a data change from a writer change and record a new snapshot.

## my local futures files

```powershell
.\.venv\Scripts\edge-hold.exe local-report --data-root G:\localview\data\bars --cache-root G:\nq-powell\data\cache
```

this reads without changing the source files. it writes an audit and a blocked study report until reviewed mapping and roll instructions are supplied. NQ stays the primary; listed optional markets can be excluded with reasons.

[research choices](docs/research-plan.md) · [accounting](docs/methods.md) · [measured scale](docs/benchmarks.md) · [clean-run check](docs/clean-run.md) · [repair log](docs/repair-log.md)

the repo contains code, aggregate audits and derived results. raw vendor bars, contract mappings and public response snapshots stay in ignored local folders.
