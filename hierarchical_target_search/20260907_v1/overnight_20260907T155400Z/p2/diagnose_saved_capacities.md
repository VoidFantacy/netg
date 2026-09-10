# Saved-capacity diagnosis

`diagnose_saved_capacities.py` is a fixed, read-only P2 diagnosis of existing
aligned count rows. The root controller runs the actual pilot analysis. The
script itself never runs ANN search or fitting and never opens GT, region-label,
graph, base, query-vector, validation or held-out files.

The prerequisite is the completed main analysis, with its input audit passed and
positive ordinary paired 95% lower bounds for `oracle_probability` minus
`oracle_unified` on both datasets at both L64 and L128. This permits the bounded
diagnosis; it does not issue P2 GO or a formal performance claim. Count/model
paths and SHA256 must equal that analysis, and the count must embed the exact
model manifest, use the first 10,000 `drl_train` pilot queries, and retain the
20,000-query isolated fit metadata.

The allocator reconstruction is bound to the frozen `ACSG/RegionalSearch.h`
SHA256 `320e29c9407d5907ece7ef64113edeb8b2d5157fa8796aaf94e470eb6771e14e`
and checked against the P1 source manifest. Its shared queue receives
`floor(L/4)`, each of four active regions receives four slots, and remaining
slots use largest remainder with ascending region ID on exact fractional ties.
Scalar binary64 operations preserve the C++ calculation order. The saved
capacity vector is ordered as shared queue, then saved selected-region order.

The scheduler also uses these integer capacities. Once routes, portal order and
capacities coincide, the uniform and probability searches must be identical.
For every such pilot row, the diagnosis therefore requires exact equality of
result IDs, Recall, routing/graph/total NDC, routing/graph/total MAC, expanded,
rejected and evicted-unexpanded counts. Instrumented time is deliberately not
part of this deterministic equality check. Any mismatch causes an incomplete
diagnosis, not a method NO_GO conclusion.

Outputs include per-dataset JSON and aligned per-query CSV with:

- Fraction of geometry uniform/probability rows with identical capacities,
  and exact saved-field equality fractions across all rows.
- Geometric and oracle conditional weight maximum, entropy in bits, normalized
  entropy, and Herfindahl concentration. The same statistics are computed from
  regional capacity shares, excluding the fixed shared queue.
- Geometric and oracle capacity L1 distances from their respective uniform
  allocations, plus a histogram of the largest regional capacity.
- Fixed same-capacity and different-capacity groups with their saved
  probability-minus-uniform Recall, graph NDC and expanded-count means.

These are descriptive counts and concentration statistics with no new
significance test or fitted threshold. Top4 weights and regional capacity shares
are conditional distributions, not absolute GT mass. Oracle and geometry use
different routes, and capacity changes affect both retention and scheduling;
these summaries cannot identify an optimal calibration or isolate either
mechanism causally.

Run from `/data/netg/ACSG`, using a fresh output directory under the controller:

```bash
.venv_cpu/bin/python hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p2/diagnose_saved_capacities.py \
  --analysis hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p2/analysis_v1/analysis.json \
  --input webvid2_5m_light_v1 hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p2/webvid_eval/count.json hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p2/webvid_model/model.json \
  --input yandex_t2i_official10M_ip_v1 hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p2/yandex_eval/count.json hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p2/yandex_model/model.json \
  --output hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p2/saved_capacity_diagnosis_v1
```

The fixed soft deadline is 2026-09-07 22:59 UTC; the script also checks it during
query processing. Success writes `diagnosis.json` and `complete.json`; an error
retains partial CSV/dataset output and records `failure.json`. Existing output
directories and files are never overwritten.

`test_saved_capacities.py --output <new-directory>` compiles a tiny standalone
allocator reference against the existing frozen header. The initial synthetic
test passed 1,075 exact C++/Python cases, including ties, near-uniform roundoff,
zero masses, active-count boundaries and fixed-seed cases. It also passed all
11 exact-field mismatch rejection checks, main-analysis prerequisite rejection,
count SHA binding and an end-to-end four-query fixture whose file-open guard
permits only synthetic count/model and newly emitted CSV. Evidence is in
`capacity_diagnosis_synthetic_tests_v1/result.json`. These tests did not run the
real pilot diagnosis.
