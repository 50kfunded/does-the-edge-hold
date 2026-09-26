# adding something

i've kept the parts small so another signal or data source doesn't need a new backtester.

for a signal, add its rule in `signals.py`. it returns `known_at,target`, where target is 0 or 1 and `known_at` is when the input bar is complete. add it to a declared grid and record every setting tried. test that changing future prices doesn't change earlier decisions, and that a contract transition resets its history.

for a data source, return `ts,open,high,low,close,volume` in time order, with UTC start timestamps. `iter_parquet` is the local adapter and `make_bars` is the synthetic source. add contract metadata to `specs.py` when using another market. the local file registry is in `data.py`; the existing audit intentionally checks these six exports.

don't manufacture contract IDs from price jumps. supply a reviewed schedule through `rolls.py` and the evidence manifest described in [the roll check](docs/roll-gate.md). new costs belong in the ledger, with a small hand-calculated path proving that cash, equity and both sides' costs reconcile.

run `python -m pytest -q` and `edge-hold example`. keep licensed files under an ignored local folder. before a new empirical grid, document the change, archive the old plan, and freeze a new one. include failed runs in the report too.
