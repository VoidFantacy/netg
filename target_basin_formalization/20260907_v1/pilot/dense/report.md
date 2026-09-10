# E1 dense routing pilot

Status: **FAIL → E1b**. Held-out accessed: **false**.

On the first 1,000 `drl_train` queries, dense routing alone costs `1759.172` NDC/query on WebVid and `1765.384` on Yandex. The paired Fast L64 total budgets are only `1037.866` and `1763.126`, respectively. Both points are therefore infeasible before graph search begins.

Because E1 requires both datasets and both targets to pass, further dense graph/timing sweeps cannot change the decision and were not run. The only allowed next action is E1b with fixed secondary Micro-HNSW (`M=16`, `efConstruction=200`, `efSearch=32`).
