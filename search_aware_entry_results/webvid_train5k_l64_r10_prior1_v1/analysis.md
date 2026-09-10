# WebVid Search-Aware Prototype Gate

## Protocol

- frozen WebVid NSG: `R64/L_build100/C512`
- label split: independent `drl_train` / prototype-train first 5K
- label target: exhaustive current-hub single oracle at `L=64`, Recall@10
- candidates: 815 existing QGT-Cover hubs; 809 received at least one label
- predictor: normalized mean query per oracle hub plus raw-hub prior 1.0
- evaluation: validation first 1K, `L=64/128/200/400`, Recall@1/10/100, 3 runs
- baseline: current Fast prototype top-3

## Result

With search-aware prototype top-3, Recall@1 and Recall@10 improve at all four `L`
values. Gains are only `+0.35 to +0.82 pp`; graph NDC rises `0.36% to 0.71%`.
Recall@100 changes by `-0.078 to +0.189 pp` and is effectively flat.

With search-aware prototype top-1, Recall@1 drops by `0.2 to 0.7 pp` and
Recall@100 drops by `0.066 to 0.379 pp`. Recall@10 changes by `0 to +0.61 pp`,
while graph NDC is `0.95% to 3.08%` higher than Fast top-3.

## Decision

The oracle labels contain useful signal, but a hard-label spherical centroid does
not capture enough of the large current-hub oracle headroom. Top-3 remains useful
as error tolerance for an imperfect predictor even though exact oracle top-3 under
a shared fixed search pool is worse than exact single oracle.

Stop the oracle-label centroid route. The next method must retain sparse
query-entry utilities and learn cost-aware ranking/marginal gain rather than reduce
each training query to one class. This result does not justify a larger generic
classifier or graph repair.

The 3 runs repeat deterministic search on the same 1K validation queries and do
not measure build-seed or query-sample uncertainty. Routing cost and per-query tail
arrays are not included, so this is a direction gate rather than a paper result.
