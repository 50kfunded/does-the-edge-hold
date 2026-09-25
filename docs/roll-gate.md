# roll check

the minute files have prices and timestamps, but no contract ID. i need to know which contract each bar belongs to before treating the P&L as a futures result. a price jump between contracts can't count as a trade.

i matched the five minute exports back to the local cache, including their timestamps and OHLCV values. NQ, ES and YM came from calendar continuous series (`c.0`); GC and CL came from previous-day-volume series (`v.0`). [the provenance file](../reports/local-provenance.json) has the hashes and comparisons. the NQ second bars came from `NQ.c.0` in the ingestion code, but i haven't reconstructed that file yet.

the accounting test closes at the last old-contract minute's open and reopens at the first new-contract minute's open, charging costs on both sides. that test works with known synthetic contracts. it doesn't tell me the real roll dates.

**current decision: blocked.** the local cache doesn't include the date-to-contract schedule. the free Databento lookup returned an account-locked error, and i no longer have that account. i'm checking old local downloads for the mapping. i won't guess roll dates from price jumps. [the gate result](../reports/roll-gate.json) records this status.

if i find saved mapping files, i'll check their source, date coverage and contract IDs against the exports before running `edge-hold research`. the mapping and evidence stay under `runs/`, which Git ignores. the command checks the plan lock and roll gate before it calculates P&L.
