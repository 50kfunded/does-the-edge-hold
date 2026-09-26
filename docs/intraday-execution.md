# how the window runs

i only make a five-minute bar when all five minute starts are observed. its close becomes known at the bucket end. features use this UTC date alone. momentum uses the first open of its n-bar window, so the 12-bar rule has enough history at 09:00. mean reversion includes the latest close in its mean and sample standard deviation; holding state starts flat after warmup.

an earlier pending instruction that is already executable at an observed open fills before a new decision arriving at that same time. a later decision supersedes a still-unfilled instruction. buy fills at or after 11:30 are cancelled. at 11:50 the fixed terminal instruction cancels every remaining signal order and blocks new ones. its first permitted minute-open proxy includes the scenario delay and must be before noon.

each window has its own ledger. the `contract` field inside that ledger is only an equality guard holding the opaque source/date segment label; it doesn't identify a real futures contract. the public records call it `source_segment_id`, and real contract identity stays unknown.

fill prices round adversely to the product tick when needed, then add adverse ticks. gross P&L uses original raw prices. slippage includes rounding and tick costs; commission is charged on both sides. successful windows end with zero position, pending orders and unrealized P&L. a missing terminal observation retains the earlier fills and unresolved ledger with no completed score.
