# custom signals

i declare the columns, global settings and helper functions a signal uses when i register it. changing a declared setting changes the execution identity. an undeclared global setting is rejected. i only allow pandas/numpy modules and pure declared helpers in this interface; unrelated globals and credentials aren't inspected or saved.

before a custom signal runs, i check repeated output, truncated history and changes to later prices. small inputs get every prefix; larger inputs get the first 32 and up to 16 distributed prefixes. the check status is saved with each case. a failed check stays a failed case, with no scored return.

these checks catch the review's mutable-global and next-close examples. they aren't a proof against arbitrary Python, hidden file reads through a library, deliberate evasion or randomness. research extensions must be deterministic functions of their declared inputs and settings. this interface isn't a sandbox.

see [the breakout example](../examples/breakout.py) for registration. an old callback registered without an input declaration needs updating.
