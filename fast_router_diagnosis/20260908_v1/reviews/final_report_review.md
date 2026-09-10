# Final report and handoff review

2026-09-08. **PASS after two substantive corrections.** The final report, README and current handoff sections agree with `analysis/v2`, completed search records and the corrected `results/costs_v2.json`. No unresolved numerical, interpretation or current-status blocker was found. This review ran no search or model fitting and modified only this review file.

The report's four-point Recall tables, exact-minus-Fast intervals, exact/Fast C8 coverage, basin gaps and recovery rates, Spearman range, A0 medians, cross-L intersections/regrets and nearest/random transfer values were checked against the verified final analysis. The additional descriptive triple-versus-single counts were independently rederived from saved matrices: WebVid best triples beat C8 best singles on 4/512 and 2/512 queries; Yandex has 0/512 at both L. The corresponding tied-query counts are 486/491 and 490/506. Yandex L128 has 266/512 queries with every hub attaining Recall=1, matching 51.95%. The reported lost-hit means and absence of new union-external hits also match saved interaction statistics.

The report keeps oracle action families, same-L versus same-cost comparisons, historical pilot versus new held-out evaluation, and local-transfer evidence versus general learnability claims separate. It explicitly limits implementation correctness to audited checks, does not turn the signed basin decomposition into causal percentages, does not isolate an untested single-mean/prior mechanism as the sole cause, and does not claim that oracle single-entry quality proves the best deployable cardinality. Near-zero bootstrap bounds and the approximation in family intervals are disclosed.

Two findings were corrected and rechecked before PASS:

1. The current prototype formula is the sum of unit queries plus a unit raw-hub prior of weight 1, followed by normalization. It is not the mean of unit queries plus an unchanged weight-1 prior. The report and spec 2.1 now state the actual formula.
2. `stage=route` is emitted before HNSW construction/routing, after input/index loading. The earlier collector mislabeled its elapsed value as a completed joint routing phase. The corrected collector and costs_v2 label 4.183603446/11.03554108 seconds as cumulative elapsed time at routing start. Combined HNSW+route and separate HNSW/route times are all null with reasons. Report section 9, README and spec 18 reference costs_v2 and disclose the preserved v1 misreading. No searches or Recall statistics changed.

The four child-job wall times sum to **150.55661451502237 seconds**; controller elapsed is **150.67637845900026 seconds**. Peak observed child RSS is **10,746,122,240 bytes = 10.008106231689453 GiB**. These match costs_v2, jobs and completion records, and the report rounds them correctly. Preparation and analysis times remain separate; reused historical exact-GT/QGT/NSG times remain unknown. No conversion to deployable QPS or full training time is claimed.

README points to prepared_v2, run_v1 and analysis/v2; it requires new reproduction output paths and explains the historical controller's fixed-log limitation. It does not automatically rerun a job. Current summary/spec/s-target agree that this diagnosis is completed, the old fixed-anchor/three-entry design is withdrawn, Fast remains the baseline, and no new training or old branch is automatically resumed. Historical design sections are subordinate to the current entry point. At review time root was completing the final state/delivery manifest after this PASS; that final bookkeeping is outside this report-content hash check.

## Reviewed file identities

| File | SHA256 |
|---|---|
| `report.md` | `14a679b6c4415b2758b8dfe6a60c8aecaf61efa902e01c840df2a096264d8d56` |
| `README.md` | `12f197f4d6ca03a2c4993d296f79c20ba6859890dc235d98a24a7be0d18b0cb4` |
| Project `summary.md` | `92594a7d465fa5794579d472abc2f7cc4e02729b4847dc2a689e69326069706c` |
| Project `spec.md` | `8a433cb07059c17380d77eac7729c3d2eae449a10050de008ea6a22fba32e7fa` |
| Project `s-target.md` | `a95879fa7388e8395d229cf237d4a0d4ac22867b6d7469591a7d9b07a9110e76` |
| `results/costs_v2.json` | `b02349370baaa6118dc96428c3d3f1060578f7f1939a812850bd40a79ea19acc` |
| `tools/collect_costs.py` | `2805ca86858140ebb60ca4a054c082566c7c13e2e02996c4dfa52729faf850b7` |
| `analysis/v2/analysis.json` | `d4714a363e271ccc92f964b3f11e6c6418a903f15b92796c6d8f3fff6582dc16` |

Earlier independent input, execution and analysis checks are recorded in their dedicated review files. The final state/protection/link manifest is maintained by the delivery owner; this review does not replace those checks.
