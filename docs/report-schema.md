# report changes

new futures reports use schema version 2, save the actual protocol and primary, and call the carried selection `selected_config_from_primary`. the reader still accepts `selected_config_from_NQ` in older reports. old saved research results stay intact.

rank figures use only the candidates shown in the figure. equal Sharpe scores get average rank. this descriptive chart includes successful candidates below the selection trade threshold; the selection table still applies that threshold and its declared tie rule. the figure's numbers are saved in `rank-chart-table.csv`.

`roll-check --plan` uses the validated universe. `resolve-rolls --plan --markets` can resolve a declared subset and records exclusions. a local report audits the files sealed by its lock, including extra legacy sources, while using its plan for the P&L gate and primary.
