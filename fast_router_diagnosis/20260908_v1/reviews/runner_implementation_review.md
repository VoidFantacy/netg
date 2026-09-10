# Runner implementation and observed acceptance review

2026-09-08. This review makes no source, binary, index or model change. No real graph process was started by this reviewer. The isolated runner source and binary have remained frozen since their handoff.

## Frozen implementation

| Artifact | SHA256 |
| --- | --- |
| `src/fast_router_diagnosis.cpp` | `968796a903bd562a2b4231a1b92a90bb35528f5dc932de37c1361f7f9f8c9c28` |
| `bin/fast_router_diagnosis` | `c2948518b715aa66d28cede1aec126fef197b513dc555d0f42ff6e14d826287f` |

Both hashes were recomputed after all four real jobs completed and match `results/run_v1/execution_freeze.json`. The compiler, source/header and linked-library identities are recorded in [build_manifest.json](../bin/build_manifest.json). The original `IndexACSGFlat::loadACPG` and `ACSG::search_new(mode=2)` are linked and called directly. No alternate search implementation is used.

HNSW and exact prototype ranking use unchanged raw query bytes and the same `InnerProductSpace` distance function. Original real base IDs are HNSW labels; saved local labels explicitly map through `hub_ids.i32`. GT is absent from `Work::run` and is scored from returned IDs outside the search kernel. The count wrapper audits that the first distance evaluations match every requested entry ID in order. One, two and three entries all use the same shared search beam.

## Synthetic acceptance

[acceptance.json](../bin/acceptance.json) records:

- `--help` and the memory-only synthetic test passed: 144 graph plain/count comparisons and 48 router comparisons.
- [Synthetic end-to-end log](../bin/synthetic_e2e_v1.log): a generated 192-node index was saved, loaded through the original loader, and evaluated through the complete runner path. All 91 variants and 3,464 serialized hitmask/count/NDC records passed.
- [Synthetic parity](../bin/synthetic_e2e_v1/result/parity.json): 484 entry-set comparisons, each counted/plain/counted-repeat, totaling 1,452 search calls. Returned IDs/distances and repeated NDC matched exactly; acceptance rows excluded the synthetic pilot.
- Independent Python checks verified variant counts, unique/padded actual entries, Fast1/exact1 reuse of all-single records, and rejection of an existing output root without changing its metadata.
- [Parity-only metadata](../bin/synthetic_parity_only_v1/metadata.json) reached `PARITY_ONLY_COMPLETE` and recorded its call count.

## Real acceptance and matrix checks

The root coordinator ran the real jobs. Their [job records](../results/run_v1/jobs.json) show sequential WebVid parity/main then Yandex parity/main, all exit code 0.

| Dataset | Auxiliary parity rows | Entry-set comparisons | Count/plain/repeat search calls | Status |
| --- | ---: | ---: | ---: | --- |
| WebVid | 8 | 14,464 | 43,392 | PASS |
| Yandex | 8 | 14,560 | 43,680 | PASS |

The [WebVid parity](../results/run_v1/parity/webvid2_5m_light_v1/parity.json) and [Yandex parity](../results/run_v1/parity/yandex_t2i_official10M_ip_v1/parity.json) confirm identical returned IDs/distances, repeated NDC, route identity and actual initial-entry order. All acceptance rows begin at local row 512. Main runs explicitly use `--parity-queries 0` and use separate output roots.

Four jobs used **2,770,770 graph search calls**, including 87,072 acceptance calls. Both main roots and both L matrices have completion markers. An independent read-only check sampled query-local rows 0, 127, 511, 512 and the final row, and four hub columns per row, for each dataset and L. All **80 sampled raw returned-ID records** matched recomputed GT10 hitcounts and masks and had no duplicated valid returned IDs. Full all-single returned-ID byte lengths matched their declared shapes; all 512 Fast1/exact1 hitcount columns matched the corresponding all-single columns at both L values.

## Controller review and boundary

The reviewed [run_diagnosis.py](../tools/run_diagnosis.py) checks the prepared-input completion marker, freezes source/config/artifact identities, runs only one owned process at a time, requires parity PASS before main, and checks RSS, disk reserve, new-artifact size and wall limits while a job is running. It preserves output/log exclusivity and uses owned process-group identity before termination.

One implementation limitation should remain explicit: the cumulative search-call limit is checked **after each job**, rather than interrupting an individual job at a live call threshold. The current frozen N/H/P/action counts have a known upper bound below the protocol cap, and the observed total is below 3,000,000; this does not invalidate this run. A future expanded configuration must not infer that this controller alone provides an exact in-job search-call cutoff.

This acceptance establishes implementation consistency within the frozen scope. It does not prove correctness for every unseen input, validate a new selector, or establish deployment QPS. All reported timing remains instrumented diagnostic wall time.
