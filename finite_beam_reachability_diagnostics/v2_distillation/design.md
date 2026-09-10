# Cost-Constrained Reachability Distillation v2 — frozen train-only design

## Single hypothesis

Actual finite-beam searches are used only offline to populate a small local query atlas.  At routing time,
the query retrieves nearby train queries from a small vector index; for each Fast geometry top-8 entry,
the atlas predicts (1) relative graph-NDC and (2) utility residual versus geometry rank-0.  No graph search,
GT, or trace feature is used online.

This differs from the stopped static ranker/prototype variants: the student is a local, non-parametric
cost-first estimator, not a global diagonal ranker or a single centroid per entry.

## Frozen protocol

- Inputs: existing `drl_train` trace rows `[0,2000)` only; validation and held-out are forbidden.
- Atlas fit: queries `[0,1600)`; internal audit: `[1600,2000)`.
- Candidate set: the already saved Fast geometry top-8; `L=64/128`, `K=10` evaluated separately.
- Query vectors are L2-normalized only for atlas-neighbor retrieval.
- Fixed atlas neighborhood: exact top-64 cosine neighbors during this diagnostic.  A deployable version
  would place the same 1,600 vectors in a small HNSW index; approximation/latency is not claimed here.
- A candidate needs at least 4 neighbor observations in which that entry was in the neighbor's top-8.
- Neighbor weights are `max(cosine, 0)`; zero-total weight falls back to uniform weights.
- Offline targets for candidate `e` are:
  - `relative_ndc = NDC(q,e)/NDC(q,rank0)-1`;
  - `utility_margin = u(q,e)-u(q,rank0)`, with the frozen v1 utility.
- Cost-first decision:
  1. candidate is predicted feasible only when `mean(relative_ndc) + 1 SE <= 0.005`;
  2. candidate is predicted beneficial only when `mean(utility_margin) - 1 SE > 0`;
  3. select the feasible candidate with greatest lower-bound margin, otherwise use rank-0.
- No hyperparameter sweep or dataset-specific threshold is allowed.

## Train-internal gate

All four dataset-by-L points must simultaneously satisfy, versus geometry rank-0:

1. mean utility delta is positive and query-bootstrap 95% CI lower bound is positive;
2. mean Recall@10 does not decrease;
3. ratio-of-means graph-NDC increase is at most `0.5%`;
4. at least 1% of queries are rerouted, so a vacuous rank-0 policy cannot pass.

If any point fails, stop with `NO_GO_NOT_PREDICTABLE` and do not access validation.  If all pass, freeze
the artifact and separately authorize one validation run; the current script must not read validation.

