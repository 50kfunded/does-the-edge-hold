"""An independent signal extension, using the public canonical bar contract."""
import pandas as pd
from does_the_edge_hold.signals import register_signal

def breakout(bars, spec):
    prior_high = bars.groupby(bars.contract.ne(bars.contract.shift()).cumsum()).high.transform(
        lambda values: values.shift(1).rolling(spec.lookback_hours).max())
    return pd.DataFrame({"known_at": bars.known_at, "target": (bars.close > prior_high).astype(int)})

def register():
    register_signal("breakout", breakout)
