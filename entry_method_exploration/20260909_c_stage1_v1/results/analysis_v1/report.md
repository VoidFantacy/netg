# C2 finite-action oracle — observed result

Decision: **NO_GO_UNCONDITIONAL_HEADROOM_STOP_C**. Stop before C3; no C3/C4/validation/held-out executed.

| Dataset | L | continue R@10 | oracle R@10 | unconditional Δ pp | Bonferroni4 family95 CI pp | eligible % | strict gain % | oracle actual NDC mean | gate |
|---|---:|---:|---:|---:|---|---:|---:|---:|---|
| webvid2_5m_light_v1 | 64 | 65.595% | 66.575% | +0.980 | [+0.620, +1.410] | 99.85 | 4.05 | 922.65 | PASS |
| webvid2_5m_light_v1 | 128 | 74.800% | 75.435% | +0.635 | [+0.365, +0.975] | 99.35 | 2.90 | 1644.93 | PASS |
| yandex_t2i_official10M_ip_v1 | 64 | 83.150% | 83.380% | +0.230 | [+0.040, +0.495] | 100.00 | 0.45 | 1637.43 | FAIL |
| yandex_t2i_official10M_ip_v1 | 128 | 89.440% | 89.580% | +0.140 | [+0.005, +0.360] | 100.00 | 0.30 | 2787.60 | FAIL |

All 2000 queries per dataset are retained at each L, including early-finished, no-eligible and no-op cases. GT was opened only after both datasets completed raw branch execution.

The primary oracle selects among continue and up to four legal force actions; Recall ties choose continue first, then frozen candidate slot order. Natural controls are paired with the same candidate. All branch costs, action proportions, mechanism contrasts, state serialization and clone costs are in report.json; aligned IDs/distances remain in raw branches.jsonl.

This is common-cap headroom only. Actual NDC differs among branches, the historical drl_train pool and single paired build limit inference, and branch wall is not formal QPS.
