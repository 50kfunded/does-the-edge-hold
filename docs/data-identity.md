# data identity

new locks can declare `ohlcv-utc-ns-f64-v1`. i keep the file's byte hash as an artifact receipt and use the observation hash to compare data across Parquet writers. old locks keep their original byte identity; i don't overwrite them.

the canonical stream has a fixed header, then rows in observed order: signed 64-bit UTC nanoseconds, followed by open/high/low/close/volume as IEEE 754 float64, all big endian. a final unsigned 64-bit row count follows `rows:`. timezone offsets and timestamp units normalize to UTC nanoseconds. zero normalizes to positive zero. no other price rounding occurs. integer volume must remain exactly representable. column order, compression, row groups and pandas metadata aren't economic inputs.

nulls, nonfinite values, duplicate/out-of-order timestamps, invalid OHLC and negative volume fail before hashing. the code never sorts, fills or removes bad input to make its identity pass. source-specific stricter quality gates remain separate.

a migration receipt may reference a historical lock and add semantic hashes after rechecking the observations. it doesn't claim those hashes were frozen before the old research. new execution identities use semantic sources and retain file hashes outside the economic identity.
