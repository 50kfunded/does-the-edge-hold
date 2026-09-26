# what i still need for futures

the exports have OHLCV and timestamps, but no contract IDs. the five minute files match their local caches: NQ/ES/YM use `c.0`; GC/CL use `v.0`. NQ seconds have an ingestion-code lead, but no verified cache reconstruction.

**the futures study stays blocked.** the account-locked request and earlier bounded local searches found no usable mapping. i no longer have that account. i haven't retried it, bought data or guessed rolls from price jumps.

the resolver now uses [Databento's documented continuous → instrument_id route](https://databento.com/docs/standards-and-conventions/symbology). raw symbols are optional and need a separate instrument_id → raw_symbol response with intersected validity dates. repairing that parser doesn't recover the missing evidence.

## the files that would clear the gate

keep them in an ignored folder and pass it with `--mapping-root`.

| file | contents |
| --- | --- |
| `NQ_rolls.csv`, etc. | `effective_at,end_at,contract`; UTC start-inclusive / end-exclusive identity intervals, covering every source bar |
| `NQ_instructions.csv`, etc. | `known_at,executable_at,deadline,effective_at,old_contract,new_contract` |
| `NQ_policy-source.json`, etc. | the independent source showing when the advance instruction was available; a retrospective switch list alone isn't enough |
| `evidence.json` | method, dataset, original response/request/retrieval hashes, exact policy and per-market source/schedule/instruction hashes |

each market's `policy_evidence` needs `kind: advance_schedule`, `reviewed: true` and the policy-source SHA-256. that review must describe genuine contemporaneous availability; filling in a boolean isn't evidence. the exact schema is exercised by `tests/test_empirical_integration.py` using explicitly synthetic fixtures.

the exit uses the first observed old-contract open after executable time plus the scenario delay, before the deadline. if that price is missing, it fails. reentry waits until the new-contract boundary plus delay. both sides pay costs. the engine never searches backwards for the last old bar.

NQ must pass identity, advance-policy and quality checks. ES/GC/CL/YM may be excluded only as the protocol allows, with reasons in the run's universe manifest. calendar mapping alone doesn't establish causal liquidation, and a volume mapping needs the same advance evidence.

someone with saved resolver/DBN metadata can supply those artifacts without a new account. otherwise the next required action is obtaining genuine historical identities and an independently defensible execution policy from an authorized source. this project makes no billable request and doesn't estimate a price for unavailable evidence.
