# QPS-first entry theory: read-only evidence study

Authorized 2026-09-22; deadline 16:00 Asia/Shanghai (08:00 UTC).
The user approved implementation of the theory plan, not a new method experiment.

## Scope

- Minimize complete mean query latency subject to Recall@1 or Recall@100 >= 0.90.
- WebVid and Yandex separately. Discuss 0.95 only where existing curves cover it.
- Fixed bottom graph, metric, main search, expansion, stopping and one global L per configuration.
- Zero training, optimizer steps, new NSG/ANN calls, GT generation, graph construction, new test payload access or production changes.
- Read existing aggregate CSV/JSON, protocols, source and research papers. New arithmetic and synthetic decision examples do not execute search.
- The three-point timing supplement is exposed four-fold development evidence, not a fresh test. E103 is a separate historical workload; never splice its time with record125 Recall.

## Analysis contract

1. Recompute all 24 record125 method points from the three recorded QPS samples. Use reciprocal median QPS for representative time and also report pooled time across repeats. N/sum(time) is throughput; mean per-query inverse latency is not.
2. Preserve all 12 matched-L comparisons. Interpolate time against Recall only between adjacent measured points; no extrapolation, fabricated search point or confidence claim.
3. At 90% decompose the interpolated time difference into baseline budget credit and combined same-L pipeline penalty. This is an identity of the interpolation model, not a measured component decomposition or causal attribution to kNN.
4. Report the conditional thought experiment that a successor has the observed Recall curve and unchanged baseline same-L cost apart from a new decision charge. Its affordable charge is the budget credit; this is not a universal upper bound on successors that also reduce search work.
5. Inspect E103 default curves independently for historical 90/95% cost scales. Nonmonotone or uncovered brackets must be flagged, not forced to fit.
6. Numerically check counterexamples and algebra with an independent implementation. Preserve input hashes and root-document snapshots. No method selection, fitting or tuning is performed by these checks.

## Deliverables

- report.md: concise conclusion and evidence limits.
- theory.md: cost identity, conditional information value, error/representation/budget-transfer limits, falsifiable predictions.
- prior_work.md: primary-paper and project-history comparison, verified conditions and non-transferable claims.
- candidates.md: at most two concrete designs and at most one prioritized implementation candidate; none may be presented as validated or novel by naming alone.
- results/: reproducible accounting, sensitivity tables and algebra checks, not new performance measurements.
- reviews/: source identities and verification; state.json lists what actually ran.
- Research history card and root summary/target synchronization after closeout. spec.md changes only for the implemented isolated accounting contract, not proposed router abilities.

## Stop boundary

No automatic experiment follows this study. A candidate lacking cost feasibility, information evidence or a substantive distinction is explicitly held or rejected. No new model name substitutes for that gap.
