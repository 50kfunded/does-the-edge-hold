# the futures roll gate

the local minute exports contain prices, volume and timestamps, but no contract ID. a jump from one contract's price to another's is not trading P&L. the strategy ledger has a synthetic test that closes at the **open of the final old-contract minute** and, if the target is still long, reopens at the **open of the first new-contract minute**. it charges both sides. that accounting test does not identify the contracts in the real exports.

the local cache comparison reconstructed all five minute exports exactly, including timestamp and OHLCV values after the builder's float32 conversion and duplicate handling:

| export | matched cache root | requested continuous rule |
| --- | --- | --- |
| NQ 1m | `NQc0` | calendar (`NQ.c.0`) |
| ES 1m | `ESc0` | calendar (`ES.c.0`) |
| YM 1m | `YMc0` | calendar (`YM.c.0`) |
| GC 1m | `GCv0` | previous-day volume (`GC.v.0`) |
| CL 1m | `CLv0` | previous-day volume (`CL.v.0`) |

the NQ second-bar ingestion code requests `NQ.c.0`; a full second-file reconstruction has not been done. the cache filenames and source code show the requested rules, while the cached Parquet slices still lack the **date-to-contract mapping**. [local-provenance.json](../reports/local-provenance.json) records the file-level comparisons and hashes. Databento says its continuous prices are unadjusted and that `symbology.resolve` is free. [Source](https://databento.com/docs/standards-and-conventions/symbology)

## decision for this run

**unresolved: empirical futures P&L is blocked.** the free mapping lookup could not complete because the local account returned an access error. no paid time-series request was made. large price changes are not used to infer rolls. [roll-gate.json](../reports/roll-gate.json) records the machine-readable decision.

to try again with an account that can use the free resolver, set `DATABENTO_API_KEY` locally, then run:

```powershell
edge-hold resolve-rolls --audit reports/local-data-audit.json --provenance reports/local-provenance.json --output runs/roll-mapping
edge-hold roll-check --audit reports/local-data-audit.json --provenance reports/local-provenance.json --mapping-root runs/roll-mapping --output runs/roll-gate.json
```

the generated CSV files and evidence manifest stay under `runs/`, which Git ignores. the gate checks the five export hashes, requested continuous symbols, schedule hashes and date coverage. a manually reviewed mapping may use the same CSV format (`effective_at,contract`) and an `evidence.json` manifest, but its provenance and roll dates must be documented before describing any P&L as validated. the one-second NQ study needs an additional source match before it can support a fill claim.
