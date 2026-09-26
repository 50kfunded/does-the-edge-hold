# roll check

the minute files have prices and timestamps, but no contract ID. i need to know which contract each bar belongs to before treating the P&L as a futures result. a price jump between contracts can't count as a trade.

i matched the five minute exports back to the local cache, including their timestamps and OHLCV values. NQ, ES and YM came from calendar continuous series (`c.0`); GC and CL came from previous-day-volume series (`v.0`). [the provenance file](../reports/local-provenance.json) has the hashes and comparisons. the NQ second bars came from `NQ.c.0` in the ingestion code, but i haven't reconstructed that file yet.

the accounting test closes at the last old-contract minute's open and reopens at the first new-contract minute's open, charging costs on both sides. that test works with known synthetic contracts. it doesn't tell me the real roll dates.

there's also a timing problem for GC and CL. a volume-ranked switch may only be known after the old minute's open, so its historical mapping alone can't justify that exit. the current runner keeps volume-roll P&L blocked. i'd need a reviewed policy extension using advance schedule evidence or extra prices for both contracts before clearing it.

**current decision: blocked.** the local cache doesn't include the date-to-contract schedule. the free Databento lookup returned an account-locked error, and i no longer have that account. i checked local downloads and the older market-project ZIPs, but didn't find the mapping. i won't guess roll dates from price jumps. [the gate result](../reports/roll-gate.json) records this status.

if i find saved mapping files, i'll check their source, date coverage and contract IDs against the exports, then check whether the execution policy was possible at the time. the mapping and evidence stay under `runs/`, which Git ignores. `edge-hold research` checks the plan lock and roll gate before it calculates P&L.

## supplying a mapping

each market needs a CSV named `NQ_rolls.csv`, `ES_rolls.csv`, etc., with `effective_at,contract` columns. times are UTC and start-inclusive. the first mapping must cover the first bar. volume-based schedules can return to an earlier contract; signals restart at every change.

`evidence.json` records `method` (`databento.symbology.resolve` or `manual_reviewed`), the exact `roll_policy` from the gate result, and a `markets` object. each market entry needs `continuous_symbol`, `source_sha256`, `schedule_sha256` and `coverage_end` (exclusive). a manual review should also record where the mapping came from and how it was checked.

for someone who still has an authorised account, `edge-hold resolve-rolls --audit reports/local-data-audit.json --provenance reports/local-provenance.json` calls only [Databento's free resolver](https://databento.com/docs/standards-and-conventions/symbology). it needs the optional `databento` dependency and a local `DATABENTO_API_KEY`. the public example needs neither.
