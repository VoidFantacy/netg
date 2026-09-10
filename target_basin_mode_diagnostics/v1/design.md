# Residual Target-Basin Modes v1 — frozen train-only gate

Goal: add a substantive but still bounded representation layer without sacrificing the established Fast
baseline.  This is not artificial delay: it models multi-modal query regions inside each GT basin.

## Frozen method

- Keep the frozen QGT-Cover hub IDs and the current primary GT-basin prototype for every hub.
- Fit only on `drl_train` rows `[10000,30000)`; evaluate on the disjoint existing sparse-utility rows
  `[0,10000)`.  Do not read validation or held-out.
- Assign each fit query to the hub nearest to its top-1 GT vector, exactly as Fast does.
- For basins with at least 8 samples, fit two deterministic spherical modes; otherwise duplicate the
  primary prototype.  No utility labels or graph probes are used for fitting.
- Current Micro-HNSW candidates remain authoritative: retrieve the existing primary-prototype top-32,
  then rerank only those candidates.
- For hub `h`, dimension `d`, mode weights `pi_hm`, current prototype `p_h`, and unit query `q`, use

  `score(q,h) = max(q·p_h, max_m(q·mu_hm + log(pi_hm)/d))`.

  The primary score is an exact fallback.  `log(pi)/d` is the fixed finite-sample/mixture penalty; there
  is no alpha, temperature, or dataset-specific tuning.
- Select top-3 distinct hubs by this score.  Online work beyond Fast is bounded by 64 dot products over
  the primary top-32 candidates; no graph probe, GT, or trace is used online.

## Non-degradation gate

Run the generated routes on the frozen NSG over the same 10K `drl_train` queries, `K=10`, `L=64/128`.
Both datasets and both L values must satisfy:

1. mean Recall@10 is not below current Fast top-3;
2. `Recall - 0.05 * NDC/NDC_Fast` is not below current Fast;
3. at least 1% of top-3 routes change, preventing a vacuous pass.

Any failure stops the variant before validation.  Passing only authorizes freezing the C++ online
implementation and one validation evaluation; it does not authorize held-out.

