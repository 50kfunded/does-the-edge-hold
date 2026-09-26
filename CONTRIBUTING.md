# adding an input or rule

i've kept the scope to research audits, with no broker or live-trading code.

a signal extension registers its callback through `register_signal`. [the breakout example](examples/breakout.py) uses only completed bars and prior highs. declare every setting in a revised plan, then test that future-price changes can't alter earlier decisions.

a source supplies ordered UTC start-stamped `ts,open,high,low,close,volume,contract`, its provenance and a `MarketAdapter`. the adapter declares the bar duration, instrument, asset kind and ledger. don't reuse futures principal accounting for spot inventory.

real futures need reviewed date-valid identities and advance roll instructions. price jumps and retrospective switch dates aren't substitutes. new cost models need a small cash/equity reconciliation and matched scenarios.

run the tests and public example. keep old plans and results, freeze changes before strategy returns, and retain failed configurations. source files stay read-only; vendor bars and mapping evidence stay in ignored folders.

[the independent-input walkthrough](docs/independent-input.md) shows the working public case and how to handle a revised snapshot.

