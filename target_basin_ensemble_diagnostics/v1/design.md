# Multi-seed Target-Basin Ensemble v1 — frozen train-first design

Purpose: increase method capacity and robustness through independent QGT/GT-basin builds, not artificial
delay.  Three existing build seeds are treated as bootstrap views of the query-conditioned target basins.

- Preserve seed-20260828 Fast rank-0 exactly for every query.
- Candidate pool is the union of seed-20260828 current top-8 and exact-cosine top-8 from seeds
  20260829/20260830.
- Select entries 2 and 3 by the largest cosine to their own seed's normalized GT-basin prototype;
  duplicate base-node IDs are merged by maximum score.
- Online implementation requires three small prototype indexes and at most 24 candidate merges.  No GT,
  graph probe, utility label, or trace is used online.
- First gate: 10K `drl_train`, both datasets, `L=64/128`, `K=10`; Recall and frozen utility must not fall
  below seed-20260828 Fast, and at least 1% of top-3 sets must change.
- Only if all four train points pass may the same frozen rule be evaluated on validation. Held-out is
  forbidden in this diagnostic.

