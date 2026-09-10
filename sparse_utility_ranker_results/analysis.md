# Sparse Utility Ranking Gate

## Protocol

- frozen WebVid and official Yandex NSG: `R64/L_build100/C512`
- independent prototype-train first 10K for fitting
- independent validation 10K for route generation and evaluation
- candidates: current Fast prototype top-32
- utility labels: single-entry Recall@10 and graph NDC at `L=64/128`
- model: three-seed diagonal query/prototype/raw-hub interaction listwise reranker
- online graph test: reranked top-3, 3 timing runs

The model fit and internal early stopping use only the first 80% and last 20% of
prototype-train. Validation utilities are used for reporting and to provide the
same Fast top-32 candidate IDs that an online router would retrieve; validation
utility values are not model inputs.

## WebVid

At the same `L`, all three seeds improve Recall@10 by `0.197 to 0.329 pp`, while
graph NDC rises `0.47% to 1.03%`. At approximately matched graph NDC:

- ranker `L=63` vs Fast `L=64`: `+0.027 to +0.100 pp`, with `0.26% to 0.62%`
  lower NDC;
- ranker `L=127` vs Fast `L=128`: `+0.125 to +0.218 pp`; two seeds use lower
  NDC and one uses `0.088%` more.

The signal is positive but small.

## Yandex

At the same `L`, Recall@10 changes by `-0.042 to +0.202 pp`, while graph NDC
rises `1.78% to 3.31%`. Lowering the ranker to `L=62/126` does not recover a
Pareto gain:

- vs Fast `L=64`, all seeds have lower recall (`-0.158 to -0.402 pp`) and higher
  NDC (`+0.46% to +0.89%`);
- vs Fast `L=128`, changes are `-0.070 to +0.016 pp` with `+0.46% to +0.63%`
  NDC.

## Decision

The Fast top-32 shortlist oracle has material utility headroom on both datasets,
but static query/hub geometry is not sufficient to predict it robustly. The
diagonal listwise reranker is WebVid-positive but fails cross-dataset and is a
no-go for the paper method. Do not enlarge this into a generic dual tower or MLP:
that lacks empirical support and moves closer to GATE without adding a distinct
mechanism.

The next defensible route is budgeted probe-then-reroute: obtain graph-native
failure evidence from a very small initial search and choose a second entry only
for predicted failures, under a fixed total NDC budget. This keeps the graph
frozen and keeps entry selection as the core problem.
