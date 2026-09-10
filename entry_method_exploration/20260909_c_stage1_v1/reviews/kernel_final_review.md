# Independent C1 kernel review

Decision: **`C1_KERNEL_PARITY_REVIEW_PASS`**, limited to the frozen C stage1 v1 mode-2 state machine and the tested domain. The C1 engineering gate is supported; the authorized four-query C2 smoke may proceed. This is not a method-quality, learner, equal-cost, Pareto, or QPS verdict.

## What was independently checked

The reviewer read the complete native headers/source, the locked protocol/configuration, the independent implementation, the mechanical native-reference extractor, the actual parity test source, build identities, raw synthetic/real JSON, and successful command records. The review did not open GT or validation/held-out vectors. Initial findings and their acceptance requirements remain in [kernel_pre_review.md](kernel_pre_review.md).

The initial review found incomplete state-shape validation and insufficient explicit test coverage for initial ties, forced-row cursor semantics, accepted-then-evicted candidates, terminal/illegal no-ops, and exact-cap natural termination. The author strengthened shape validation and tests before the final gate; no legacy kernel or locked action/cost protocol was changed. The exact-cap/query-binding checks were supplied and executed independently by the reviewer.

### Native parity and source identity

- The expanded-ID and distance-ID observers are the only changes in the extracted native function body. Removing those two observer statements reproduces the frozen native function body byte for byte; the insertion routine is also a literal extraction. The extraction additionally adapts the free-function signature, explicit ntotal and mutex, without changing search control flow.
- Current `ACSG/ACSG.cpp` equals the frozen snapshot, SHA256 `931d74db432bb2a64aeaedd5200f933674b5e84fb0d129d5640189d76b008ba4`.
- Extracted reference SHA256: `39fc562545b83be71c0b34f34a2b06efda355e9e3793a9075da32f90c9782987`.
- Reviewed state-machine SHA256: `337cc3c52fb712b5f7ca0992b3625949530399520880ffd86dd59e2b49d1354a`.
- Reviewed parity-source SHA256: `6a4c3c9fef06752f5c3952ac85fc751ae4efacb4fc3ee1495f1c1f2a02711938`.
- Executed `parity_v2` binary SHA256: `27ce34a3b55addf24c13767733076b2fe921fb47e1f9b112941f502fa50ac193`.

These identities were checked against [parity_v2.build.json](../bin/parity_v2.build.json), not inferred from names. The build retains source snapshots and links the real unchanged kernel. Reference/native comparisons assert bitwise top-K distances, IDs, actual DC counts, traced NDC, and expansion count. Subsequent state-machine comparisons assert complete evaluation and expansion order, full L+1 retset contents/flags, natural termination and top-K.

### Executed coverage

| Evidence | Observed result |
|---|---|
| [Synthetic v2](../results/c1_synthetic_v2.json) | PASS, 180 fixture/L/entry combinations; 960 partial-row cases; three tie fixtures including all-equal initialization; 159 force and 159 natural controls; repeated clone/serialization determinism and isolation |
| Hand-computable action cases in synthetic v2 | PASS for candidate distances 100 (pool rejected), 8.5 (accepted then evicted), and 4.5 (retained); full independently specified force/natural expansion order and top-K checked |
| [WebVid real v2](../results/c1_webvid_v2.json) | PASS, frozen first 16 sample IDs at each L64/L128, 32 query/L checks |
| [Yandex real v2](../results/c1_yandex_v2.json) | PASS, frozen first 16 sample IDs at each L64/L128, 32 query/L checks |
| [Independent supplemental run](kernel_supplemental_v1.json) | PASS for exact-cap natural end after visited/padding scans, zero-cost trailing rows, intentionally wrong DC query binding corrected by resume, partial serialization without duplicate charging, and terminal injection no-op |

The reviewer independently aligned all 64 real records to their sampled drl_train row-ID files, checked both L values and sample positions 0–15, verified every reported expansion order has unique IDs, and checked prefix NDC does not exceed total NDC. All corresponding command records have exit code zero and no resource stop. Real tests change the legacy shared `search_L` after checkpoint and confirm the frozen state's continuation is unchanged; plain and count/trace runs return identical states/results. Unsafe native invalid-ID calls are deliberately avoided; invalid inputs are rejected by the independent API.

WebVid raw-result SHA256: `773565a2f578a4d92ab8fa5d73ccc7dc83b7bf003362b96b6c8d6dddf6a50237`. Yandex raw-result SHA256: `ff954c5025d5e8cd7d7d55d086afa10cc2ae0f76d186e2621fe5a477c6680140`.

## Search semantics review

The independent implementation retains first-three-position entry consumption, native seeded fallback, distance-only initial sort, exact pool insertion/ties, L+1 scratch, effective length, native bound rejection, pending flags, per-row fixed cursor and accumulated rewind. Mandatory visited and expanded membership are separate. Diagnostic full-order observers are external; online history retains counters and only the last 16 expanded IDs.

A partial row stops before marking/evaluating the next legal unvisited neighbor. State carries the selected node, next offset, forced/native row type, cursor, rewind position, cap and counts. Resume binds its own serialized raw query to the supplied independent DC. The exact-cap supplemental test confirms that exhausted budget does not incorrectly prohibit free visited/padding scans or natural termination.

Natural and forced candidate actions pay candidate distance even when pool-rejected. Force clears pending at insertion, scans that candidate once, and returns to the saved/rewound scheduler without an unconditional cursor increment. The hand-computable cases demonstrate this distinction directly. Branches deep-copy mutable state; base/graph references are read-only. Output remains retset top-K.

## Reproducible commands and scope

Run from `/data/netg/ACSG`; outputs must use new paths on any rerun. The actual C1 commands and CPU environment are retained in `logs/c1_synthetic_v2.command.json`, `logs/c1_webvid_v2.command.json`, and `logs/c1_yandex_v2.command.json`.

```bash
entry_method_exploration/20260909_c_stage1_v1/bin/parity_v2 synthetic entry_method_exploration/20260909_c_stage1_v1/results/c1_synthetic_v2.json
entry_method_exploration/20260909_c_stage1_v1/bin/parity_v2 real entry_method_exploration/20260909_c_stage1_v1/inputs/webvid2_5m_light_v1/config.json entry_method_exploration/20260909_c_stage1_v1/config.locked.json entry_method_exploration/20260909_c_stage1_v1/results/c1_webvid_v2.json
entry_method_exploration/20260909_c_stage1_v1/bin/parity_v2 real entry_method_exploration/20260909_c_stage1_v1/inputs/yandex_t2i_official10M_ip_v1/config.json entry_method_exploration/20260909_c_stage1_v1/config.locked.json entry_method_exploration/20260909_c_stage1_v1/results/c1_yandex_v2.json
python3 entry_method_exploration/20260909_c_stage1_v1/src/run_logged.py review_build_kernel_supplemental_v1 bash entry_method_exploration/20260909_c_stage1_v1/reviews/build_kernel_supplemental.sh
python3 entry_method_exploration/20260909_c_stage1_v1/src/run_logged.py review_kernel_supplemental_v1 entry_method_exploration/20260909_c_stage1_v1/reviews/kernel_supplemental_v1 entry_method_exploration/20260909_c_stage1_v1/reviews/kernel_supplemental_v1.json
```

Supplemental source/build/binary/result identities are saved in [kernel_supplemental_manifest.json](kernel_supplemental_manifest.json). This supplemental review adds three synthetic resume executions and two initializations; use a conservative five when aggregating resource calls. The synthetic v2 counter includes a separate prefix count and conservative upper bound because branch calls alone omit prefix execution.

C1 is evidence over these fixtures and sampled real queries, not exhaustive proof for every graph or malformed external state. The state API is an internal versioned diagnostic interface, not an untrusted-state deserialization service. Branch wall and bookkeeping still need C2 recording; these parity runs establish no formal QPS. C2 runner/action accounting, GT separation and statistics require their own review; C3/C4 and validation/held-out remain outside this gate.
