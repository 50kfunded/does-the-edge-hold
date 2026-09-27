# how the window runs

i only make a five-minute bar when all five minute starts are observed. its close becomes known at the bucket end. features use this UTC date alone. momentum uses the first open of its n-bar window, so the 12-bar rule has enough history at 09:00. mean reversion includes the latest close in its mean and sample standard deviation; holding state starts flat after warmup.

an earlier pending instruction that is already executable at an observed open fills before a new decision arriving at that same time. a later decision supersedes a still-unfilled instruction. buy fills at or after 11:30 are cancelled. at 11:50 the fixed terminal instruction cancels every remaining signal order and blocks new ones. its first permitted minute-open proxy includes the scenario delay and must be before noon.

each window has its own ledger. the `contract` field inside that ledger is only an equality guard holding the opaque source/date segment label; it doesn't identify a real futures contract. the public records call it `source_segment_id`, and real contract identity stays unknown.

fill prices round adversely to the product tick when needed, then add adverse ticks. gross P&L uses original raw prices. slippage includes rounding and tick costs; commission is charged on both sides. successful windows end with zero position, pending orders and unrealized P&L. a missing terminal observation retains the earlier fills and unresolved ledger with no completed score.

## explaining the choices

i'd use these questions to work through the study. having this guide doesn't establish that someone understands the choices; the equations, code and saved results are there to check.

- **signal math:** can i explain latest close minus the first open of the last n completed bars for momentum, and the mean-reversion z-score using n closes including the latest with sample standard deviation? why do insufficient or zero-variance inputs stay flat?
- **availability and fills:** when does a five-minute close become known, and which observed minute open can first fill its instruction after the scenario delay? why isn't that a guaranteed quote or trade at that instant?
- **scheduled exit:** why does the preknown 11:50 instruction cancel pending orders, include delay and fail if no exit exists before noon?
- **source boundary:** why do daily resets remove cross-date price changes from this comparison while still leaving real contract identities unresolved?
- **coverage:** why is a complete 240-minute mask only known after the window, and why can't excluded dates become zero returns or a live 09:00 filter?
- **trade costs:** can i recover tick value from multiplier times tick size, check sides = 2 * completed entries and reconcile gross minus commission/slippage to net? why is entries per window frequency rather than notional turnover?
- **cost budget:** why is G/R the total break-even cost on a fixed path, with positive net only below a positive budget? why can't lower costs rescue a negative gross path, or this curve predict changed delays?
- **uncertainty:** why are paired circular 3/5/10-observation blocks descriptive, and how do selection, prior exposure, skipped dates and long memory limit them?

`edge-hold intraday-report --study reports/intraday` regenerates the saved-result analysis. it records reporting-code digests separately and keeps the original evaluation identities. each split uses aggregate dollars divided by completed trades; averaging yearly per-trade ratios would give different weights. successful flat paths have no per-trade ratio. failed or inconsistent cases stay unscored/unsupported.
