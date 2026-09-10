# C2 independent statistics and execution pre-review

Date: 2026-09-09. Reviewer: independent `review_protocol` agent. Sources reviewed: `src/score_c2.py`, `src/stage_control.py`, `src/c2.cpp`, and the frozen protocol/config. No GT file was opened, no real Recall was scored, and no method search was executed by this reviewer.

## Initial decision

**PRIMARY_DESIGN_PASS_WITH_PRE_SCORING_PRECISION_FIX_REQUIRED.** The action schema, oracle, paired-bootstrap family, unconditional denominators and separate offline scoring order implement the protocol. One exact-threshold implementation defect must be fixed before scoring: an exact +0.5 pp effect can fail the floating-point comparison. This can be corrected without changing any research choice or threshold and before any quality result is known.

## Findings

### F1: exact hit-count threshold must not depend on floating-point cancellation

The initial scorer subtracts separately rounded Recall arrays, then tests `primary['mean'] >= .005`. A GT-free synthetic check with 2000 queries, 100 improvements from Recall 0.2 to 0.3 and 1900 ties yields mean `0.004999999999999999`; the comparison incorrectly returns False even though exactly 100 extra top-10 hits meet +0.5 pp.

Use signed integer hit-count differences as the primary aligned response before dividing by ten. Apply the practical effect gate in exact hit-count units: for this fixed N=2000, K=10 and threshold 0.005, require total oracle-minus-continue hits **>=100**. More generally use an exact rational conversion of the locked threshold. Keep the corrected-bootstrap lower-bound requirement unchanged. Do not subtract uint8 hit arrays directly, since future non-oracle contrasts may be negative.

### F2: incomplete C2 executions are missing from the cumulative call ledger

`call_upper_bound()` counts C2 executions only from `c2_*/complete.json`. A failed or interrupted C2 process has consumed work even without that marker. If subsequent actions are ever attempted, ignoring this work can understate the authorized cumulative 200000-call budget.

Count an incomplete launched command's full reservation conservatively, or add a reliable persisted executed-call bound. C2 failure should remain a stop, not an unrecorded retry. The successful sequential path reserves `N×2L×20=80000` calls per dataset, correctly covering two prefix runs and two repetitions of all nine physical branches per query/L. Alias branches reduce actual calls without creating extra query samples.

### F3: recommended independent pre-GT invariant strengthening

Before opening GT, the scorer should recheck `protocol_lock.bound_files` and verify each branch has exactly ten IDs and ten distances, valid/padding IDs, and nonnegative suffix NDC. For early-finished and ineligible branches, verify that the persisted alias matches continuation in returned IDs/distances and NDC. Check branch candidate/slot correspondence against the fixed candidate IDs. The reviewed C++ runner implements these semantics, so this adds independent raw-artifact protection rather than a new method restriction.

The current completion validation already requires both dataset directories to be complete, 2000 queries and 4000 rows each, correct sampled query IDs and L layout, nine named actions, locked B/K, total/prefix/suffix consistency, cap bounds, mutually exclusive terminal reasons, unique valid result IDs and in-range base IDs. It runs for **both datasets before the first GT hash/read**, which is the correct delayed-scoring order.

## Statistical implementation checks

| Item | Finding |
|---|---|
| Main action columns | `[0,5,6,7,8]` means continue plus force slots 0–3. Natural controls are not silently added to the primary oracle. |
| Oracle ties | NumPy argmax picks the first maximum; continue comes first, then frozen slot order. No quality tie is reselected by NDC. |
| Unconditional population | Each L keeps exactly 2000 queries. Early finish, no eligible candidate and no-op branch aliases remain present. All primary means, coverage and action-choice proportions use that denominator. |
| Independent units | Bootstrap resamples a 2000-element vector of paired query differences. The per-query oracle max has already been computed from its complete action vector; resampling that aligned value is equivalent to moving all actions together. |
| Cross-L sampling | The same fixed seed resets for each point, preserving identical bootstrap query indices across L within a dataset. Using those indices in both datasets does not invalidate Bonferroni marginal intervals. |
| Family correction | 20000 PCG64 replicates; ordinary 95% quantiles 0.025/0.975; familywise95 Bonferroni4 quantiles 0.00625/0.99375. Exactly four primary comparisons. |
| Main gate | All four effects meet +0.5 pp, all corrected lower bounds are positive, and selected effective force coverage is nonzero with all branches within cap. Exact effect threshold needs F1 correction. |
| Natural mechanism control | Force slots 5–8 are compared with corresponding natural slots 1–4. `choices-4` maps a chosen force slot back to its same candidate's natural slot; continue maps to continue. |
| Selection-bias labels | Per-slot comparisons are descriptive. The selected-force-winner contrast is explicitly marked GT-selection-biased; different force/natural oracle winners are not claimed to identify the pure mechanism. |
| Unsigned arithmetic | NDC is converted to int64 before aggregation. Recall conversion currently prevents uint8 underflow, but F1 should retain signed hit differences. |
| Cost envelope | Actual graph and suffix NDC distributions, per-query min/max envelope, oracle cost, natural-finish fraction and ratio-of-means cost change are retained. Common cap is never equated to actual equal work. |
| Timing | Prefix, serialization/deserialization, physical clone, alias materialization, route and plain branch diagnostics are separated; no QPS claim. Alias wall values are explicitly identified as continuation measurements. |
| GT access | Only the separate scorer opens training GT, after complete raw validation of both datasets. GT hash is verified and hit sets use row-specific exact top10 IDs. Validation/held-out GT is never requested. |
| Output and stop | Aligned hit/NDC/oracle/bootstrap arrays, per-query CSV, full report and gate are retained. All-four PASS still means stop and report before C3; otherwise STOP_C. |

## Runner/schema checks

- Candidate top7 ranks 3:7 are fixed before looking at state; initial/duplicate IDs become empty slots without refill. Both L values receive the same query-only shortlist and direct-top3 initialization.
- Each physical branch starts from a copy of the identical prefix and applies its own B. It executes a counted/traced branch and a plain branch, then compares the full serialized state. Prefix equality after branching is checked.
- Ineligible actions alias the native continuation. Their hypothetical wall is preserved with an explicit alias marker; they are not counted as independently executed work. Coverage uses effective trajectory/retset differences rather than simply counting allocated slots.
- The runner retains per-query checkpoint state files and topK ID/distance raw rows before any scoring.
- The controller checks the locked protocol/source/input files, C1 gate and state-machine SHA, binary identity and smoke gate. It enforces aggregate recorded C2 wall, per-process RSS and periodic output-size checks on the current single-worker path. F2 is needed for a conservative failure ledger.

## Evidence scope

This is a source-level pre-review and a synthetic floating-point regression check, not acceptance of real C2 outputs. A final independent review must recompute the four effects/intervals from saved aligned artifacts, confirm the integer threshold and source fix, and verify that no raw rows were removed. Historical training-pool and single-build limitations remain. Passing the oracle gate cannot establish a learner, state information value, retained-state value, equal-cost gains or Recall–QPS performance.

Initial reviewed SHA256 identities:

```text
src/score_c2.py      d9a8f0e61d9e9b3cd15a854db66e7716f663cd9b018ff89f273896bfb53efef6
src/stage_control.py dd04454cacc953e862cfdc2c83773dea39e41f1973ac24515bfba69b49954a5d
src/c2.cpp           72f8a93811cc7198b6907a344afb353b8e38ad339bd6d393b44e5af25cc24290
```

## Addendum: pre-scoring fixes independently accepted

**C2_STATISTICS_PRE_SCORING_REVIEW_PASS.** F1, F2 and the material pre-GT checks in F3 have been addressed before actual quality scoring. This supersedes the initial precision-fix-required status; acceptance of actual C2 results still requires a separate artifact review.

- The scorer now constructs `gain_hits` by subtracting signed int16 arrays, then derives the bootstrap input by division by K=10. The effect gate compares the integer total with `Fraction(str(locked_threshold))*2000*10`, which is exactly 100. The report records both integer total and required hit gain.
- A pure synthetic check of 99, 100 and 101 extra hits independently gives FAIL, PASS and PASS. Quality ties select continue. Loading only the scorer's function definitions and running its `intervals()` on a synthetic four-element array produced exactly the same 20000 bootstrap samples and corrected interval as an independent direct PCG64 resampling calculation.
- The call ledger now retains each incomplete/failed C2 command's full recorded reservation from `commands.jsonl`. A completed command is counted from its actual physical executions instead, avoiding both omission and double counting.
- Before opening GT, the scorer now rechecks every bound file hash, ten result IDs/distances, finite sorted distances, valid/padding IDs, ineligible alias equality to continue, and zero suffix work with natural termination for early-finished queries. Both complete datasets are still validated before any GT access.

No real GT or Recall artifact was opened by this reviewer for these checks. The scientific threshold, four-comparison family, fixed actions/checkpoints/B and all-query denominator did not change. Actual C2 execution can proceed under the existing user authorization; this review does not authorize C3.

Accepted source SHA256:

```text
src/score_c2.py      ffbd06e9043c44ff8895d7267bfc28f782c20f37da494b8ce595bda1e8b93446
src/stage_control.py 7bbf36127a20d235eb9065d6827f6c3b1124a157eaa7687331894e13159a3fea
src/c2.cpp           72f8a93811cc7198b6907a344afb353b8e38ad339bd6d393b44e5af25cc24290
```
