# C2 independent final statistical review

**Review PASS; accept `NO_GO_UNCONDITIONAL_HEADROOM_STOP_C`.** WebVid meets both registered effect gates. Official Yandex-IP has positive, small unconditional oracle gains but fails the required +0.5 pp effect at both L values. All four corrected intervals are above zero. The reason to stop is failure of the all-four material-headroom gate; the data do not support saying that C has literally zero headroom. No C3 learner, C4 performance evaluation or additional candidate/budget tuning follows this result.

The review used independently written [`recompute_c2_statistics.py`](recompute_c2_statistics.py), without importing the producer scorer or calling an ANN kernel. Machine-readable verification and key numbers are in [`c2_statistics_final_review.json`](c2_statistics_final_review.json).

## Independent reconstruction

After confirming both main raw datasets were complete, read only the 2000 authorized sampled training rows' exact top10 GT IDs per dataset. No validation or held-out file was opened. The following all passed:

- Recomputed every GT membership for **720000 returned IDs across 72000 logical branches**, representing 8000 query-by-L states. All hit counts match the saved NPZ arrays.
- Independently reconstructed ordered `continue + force_0..3` oracle choices and continue-first ties. All choices, proportions and aligned NDC arrays match NPZ.
- Regenerated all **80000 bootstrap values**, using a different batch size and the same frozen PCG64 stream. All values match exactly; ordinary and Bonferroni4 intervals match.
- Checked every value of both 4000-row per-query CSV files: sampled row identity, L, continue/oracle Recall, delta, action, NDC, per-query envelope and early/no-eligible indicators.
- Opened all **8000 saved prefix-state files**. Verified query/L/K, checkpoint progress, initial entries, visited/expanded identities, fixed candidate slots, eligibility, exact ineligible aliases, cap accounting, and exactly one expansion of each eligible forced candidate. This is a consistency check of persisted C2 states, not a replacement for the independent C1 kernel review.
- Recomputed all action Recall means, same-candidate natural contrasts, coverage, cost distributions, natural-finish fractions, clone/serialization/alias and routing summaries from raw records. All reported summaries match.
- Recounted counted/plain prefixes and physical branches from raw execution markers: WebVid 74596, Yandex 79604, total **154200** main executions. Aliases remain in quality denominators without becoming fictitious additional physical executions.

No mismatch or filtered query was found. The source/input/locked protocol and raw report hashes also match.

## Four registered primary comparisons

Each row retains **all 2000 queries**, K=10, paired Fast3, the frozen candidates and common B=1856. The exact minimum effect is 100 extra GT hits; no floating-point threshold ambiguity remains. Intervals are the Bonferroni4 familywise 95% intervals, in percentage points.

| Dataset | L | Extra GT hits | Unconditional oracle gain | Corrected interval | Material gate |
|---|---:|---:|---:|---:|---|
| WebVid | 64 | 196 | +0.980 pp | [+0.620, +1.410] | PASS |
| WebVid | 128 | 127 | +0.635 pp | [+0.365, +0.975] | PASS |
| Official Yandex-IP | 64 | 46 | +0.230 pp | [+0.040, +0.49503125] | FAIL |
| Official Yandex-IP | 128 | 28 | +0.140 pp | [+0.005, +0.360] | FAIL |

The lower endpoints, including the small +0.005 pp endpoint for Yandex L128, are positive in the frozen bootstrap calculation. Statistical positivity alone does not satisfy the separately registered +0.5 pp practical threshold.

## Coverage and action choices

Early-finished count is zero at all four points. That is an observed sample property; early finish remains covered by C1 and by the unconditional C2 schema. No-eligible/all-force-no-op counts are 3/13/0/0 for WebVid64/WebVid128/Yandex64/Yandex128. Any eligible/effective force coverage is 99.85%/99.35%/100%/100%, but strict quality gain occurs on only **81/58/9/6 queries**, or 4.05%/2.90%/0.45%/0.30%. Eligibility, executed intervention and Recall improvement must remain separate concepts.

Oracle choice proportions below use all 2000 queries as denominator:

| Dataset | L | continue | force_0 | force_1 | force_2 | force_3 |
|---|---:|---:|---:|---:|---:|---:|
| WebVid | 64 | 95.95% | 1.45% | 1.20% | 0.80% | 0.60% |
| WebVid | 128 | 97.10% | 1.15% | 0.85% | 0.55% | 0.35% |
| Official Yandex-IP | 64 | 99.55% | 0.15% | 0.10% | 0.15% | 0.05% |
| Official Yandex-IP | 128 | 99.70% | 0% | 0.10% | 0.15% | 0.05% |

## Natural insertion and actual work

The independently recomputed unconditional same-slot `force(e) - natural(e)` Recall changes, in pp, are:

| Dataset | L | slot 0 | slot 1 | slot 2 | slot 3 |
|---|---:|---:|---:|---:|---:|
| WebVid | 64 | +0.220 | +0.095 | +0.100 | +0.130 |
| WebVid | 128 | +0.180 | +0.045 | +0.075 | +0.075 |
| Official Yandex-IP | 64 | +0.080 | +0.025 | +0.085 | +0.035 |
| Official Yandex-IP | 128 | −0.045 | −0.015 | +0.005 | −0.015 |

These are descriptive fixed-candidate mechanism contrasts. The force-oracle winner compared with its own candidate's natural insertion gives +0.715/+0.410/+0.185/+0.095 pp, but that contrast benefits from GT selection of the force winner. It is not a learned-policy result. Different force/natural oracle winners likewise do not isolate the pure mechanism.

| Dataset | L | Continue mean graph NDC | Oracle mean graph NDC | Ratio-of-means change | Queries with unequal branch NDC |
|---|---:|---:|---:|---:|---:|
| WebVid | 64 | 918.8445 | 922.6540 | +0.41460% | 1995/2000 |
| WebVid | 128 | 1644.6705 | 1644.9290 | +0.01572% | 1947/2000 |
| Official Yandex-IP | 64 | 1636.6005 | 1637.4280 | +0.05056% | 1977/2000 |
| Official Yandex-IP | 128 | 2787.6330 | 2787.6010 | −0.00115% | 1645/2000 |

All suffix costs are within B=1856; the full actual total graph-NDC ranges across each point's queries/actions are [280,2244], [508,3516], [327,3318], [497,4788]. Prefix cost accounts for values above B. Continue itself hits the cap on 2/43/25/356 queries. These are genuine truncated-continuation comparisons, with unequal actual work despite the shared cap. Neither the small selected-oracle mean NDC changes nor diagnostic branch wall establishes equal-cost or Pareto improvement.

## Timing, resources and delayed scoring

Both main commands completed before the scorer started at `2026-09-09T07:30:15.676186+00:00`; the saved quality-scoring state timestamp is `07:30:17.321061+00:00`. The producer source has no GT opening path and the scorer verifies both complete raw datasets before GT access.

The independently summed conservative execution ledger, including C0, preserved C1 attempts, supplemental checks, both smoke runs and both main runs, is **172261 <= 200000**. Main work contributes 154200; smoke contributes 312. Recorded C2 commands, including smoke and scoring, sum to 122.375 seconds; observed peak RSS is 10657427456 bytes (about 9.93 GiB). New version artifacts occupied about 307 MB at review, within 5 GiB. This timing includes loading and diagnostics and is not a QPS measurement. No new ANN or model run was used for review.

Exact audit command, from the version directory:

```bash
env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 /data/netg/ACSG/.venv_cpu/bin/python reviews/recompute_c2_statistics.py
```

It completed successfully in about 5.85 seconds. The script refuses to overwrite its existing review JSON.

## Interpretation and next boundary

Accept the current frozen version's stop. Preserve WebVid's positive headroom, Yandex's smaller positive means, and all corrected intervals rather than collapsing the result into a universal no-information claim. The evidence is from one historical training-development pool and one paired build; query bootstrap does not measure build variability or fresh held-out generalization. No learner, state-versus-query-only comparison, retained-state-versus-restart comparison, A+B combination or full Recall–QPS claim has been established.

C3/C4, validation/held-out and candidate/checkpoint/B/model expansion remain unrun and outside the current execution scope. This review supplies no basis for bypassing the registered stop.
